"""Disclosed local quantized Qwen adapter; never receives evaluator plans.

Unlike the stock HF runtime, llama.cpp serves publisher-provided GGUF weights.
Thinking is disabled. The optional schema profile supplies public tool parameters.
"""

import ipaddress
import json
from pathlib import Path
from urllib.parse import urlparse

import httpx
from sentinel.models.base import ModelAdapter, ModelError
from sentinel.models.hf_adapter import SYSTEM_PROMPT, parse_action, tool_card


class LocalQwenAdapter(ModelAdapter):
    name = "qwen3-8b-q4_k_m"

    def __init__(self, url="http://127.0.0.1:8091", profile="stock", max_new_tokens=768, trace_path=None):
        parsed = urlparse(url)
        try:
            loopback = ipaddress.ip_address(parsed.hostname or "").is_loopback
        except ValueError:
            loopback = False
        if not loopback or parsed.scheme != "http" or parsed.username or parsed.query:
            raise ValueError("Local model URL must be an HTTP loopback IP address")
        if profile not in {"stock", "schema"}:
            raise ValueError("Unknown model prompt profile")
        self.url, self.profile, self.max_new_tokens = url.rstrip("/"), profile, max_new_tokens
        self.goal, self.tools = "", []
        self.trace_path = Path(trace_path) if trace_path else None

    def start_turn(self, goal, hints):
        self.goal = goal
        self.tools = hints.tools

    def propose(self, context):
        history = "\n".join(f"[{obs.kind}] {obs.text}" for obs in context.observations)[-12000:]
        specs = json.dumps(
            [tool_card(t) for t in self.tools]
            if self.profile == "stock"
            else [{k: t[k] for k in ("name", "description", "consequential", "parameters")} for t in self.tools]
        )
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Tools: {specs}\nGoal: {self.goal}\nHistory:\n{history}"},
        ]
        try:
            response = httpx.post(
                self.url + "/v1/chat/completions",
                json={
                    "model": "Qwen3-8B-Q4_K_M",
                    "messages": messages,
                    "temperature": 0,
                    "seed": 0,
                    "max_tokens": self.max_new_tokens,
                    "chat_template_kwargs": {"enable_thinking": False},
                },
                timeout=180,
                trust_env=False,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            if self.trace_path:
                with self.trace_path.open("a", encoding="utf-8") as handle:
                    handle.write(
                        json.dumps(
                            {
                                "goal": self.goal,
                                "step_id": getattr(context, "step_id", None),
                                "profile": self.profile,
                                "messages": messages,
                                "response_content": content,
                                "usage": data.get("usage"),
                                "synthetic_data_only": True,
                            }
                        )
                        + "\n"
                    )
            return parse_action(content)
        except (httpx.HTTPError, KeyError, IndexError, TypeError) as exc:
            raise ModelError(f"Local Qwen inference failed: {type(exc).__name__}") from exc

    def observe(self, feedback):
        return None
