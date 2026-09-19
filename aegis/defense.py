"""The defense boundary imports no scenario loader, evaluator, fixtures, or labels.

run_id is used only as an opaque session key, never as a decision feature.
Risk values are ordinal engineering severities, not calibrated probabilities.
"""

from __future__ import annotations

import hashlib
import json
import re
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field

from sentinel.core.actions import ActionType, DefenseDecision
from sentinel.defenses.interface import Defense, DefenseRequest
from sentinel.domains.enterprise.tools import enterprise_tools
from sentinel.domains.finance.tools import finance_tools
from sentinel.domains.soc.tools import soc_tools

from aegis.flow import Secret, compact, egress_fields, extract_secrets, matches, redact, unordered_disclosures
from aegis.repairs import qualify_completion, repair_read_arguments

UNTRUSTED = {"untrusted_internal", "untrusted_external", "adversary_controlled"}
DIRECTIVE = re.compile(
    r"ignore.{0,40}(?:instruction|policy|previous)|(?:must|call|invoke|execute|use|send|paste|store|remember)\b"
    r"|system\s*(?:message|override)|approved|new\s+policy|always|from now on",
    re.IGNORECASE,
)
MEMORY_AUTHORITY = re.compile(
    r"(?:policy|approved|authorization|system override|always|from now on|ignore|must|execute|send|share)",
    re.IGNORECASE,
)
TOOLS = {t.name: t for t in enterprise_tools() + finance_tools() + soc_tools()}


@dataclass
class Session:
    seen: set[str] = field(default_factory=set)
    secrets: dict[str, Secret] = field(default_factory=dict)
    untrusted: list[tuple[str, str]] = field(default_factory=list)
    objects: dict[str, str] = field(default_factory=dict)
    egress: dict[str, str] = field(default_factory=dict)
    releases: set[tuple[int, str]] = field(default_factory=set)
    receipts: set[str] = field(default_factory=set)
    touched: float = field(default_factory=time.monotonic)
    last_step: int = -1


class AegisDefense(Defense):
    name = "aegis"

    def __init__(
        self,
        *,
        flow=True,
        authority=True,
        persistence=True,
        repair=True,
        streaming=True,
        unordered=True,
        argument_repair=True,
        completion=True,
        max_sessions=128,
    ):
        self.flow = flow
        self.authority = authority
        self.persistence = persistence
        self.repair = repair
        self.streaming = streaming
        self.unordered = unordered
        self.argument_repair = argument_repair
        self.completion = completion
        self.max_sessions = max_sessions
        self.sessions: OrderedDict[str, Session] = OrderedDict()
        self.lock = threading.RLock()

    def _observe(self, request, state):
        records = {p.id: p.provenance for p in request.provenance}
        items = list(request.conversation)
        if request.observation:
            items.append(request.observation)
        for item in items:
            identity = hashlib.sha256((item.content + str(item.provenance_ids)).encode()).hexdigest()
            if identity in state.seen:
                continue
            state.seen.add(identity)
            provs = [records[p] for p in item.provenance_ids if p in records]
            unknown = bool(item.provenance_ids) and len(provs) != len(item.provenance_ids)
            tainted = unknown or any(p.trust_level.value in UNTRUSTED for p in provs)
            source = ",".join(item.provenance_ids) or "unattributed"
            if tainted:
                state.untrusted.append((source, item.content))
            sensitive = max((p.sensitivity.rank for p in provs), default=0)
            level = ["public", "internal", "confidential", "restricted"][sensitive]
            for secret in extract_secrets(item.content, source, level):
                state.secrets.setdefault(secret.value, secret)
            # Only simulator result envelopes establish lifecycle facts. No prose approvals.
            if item.kind == "tool_result" and not tainted and getattr(item, "role", "tool") == "tool":
                try:
                    data = json.loads(item.content)
                    if isinstance(data, dict):
                        for key, status, kind in (
                            ("draft_id", "draft", "draft"),
                            ("message_id", "sent", "sent"),
                            ("incident_id", "investigating", "incident"),
                        ):
                            if data.get(key) and data.get("status") == status:
                                state.receipts.add(kind)
                        for key in ("payment_id", "remediation_id"):
                            if key in data and data.get("status") in {"prepared", "confirmed", "executed"}:
                                state.objects[str(data[key])] = data["status"]
                except ValueError:
                    pass
        # Hard memory budgets; hitting capacity blocks rather than silently forgetting secrets.
        return not (
            len(state.secrets) > 2048 or len(state.seen) > 8192 or sum(len(t) for _, t in state.untrusted) > 2_000_000
        )

    def decide(self, request: DefenseRequest) -> DefenseDecision:
        with self.lock:
            now = time.monotonic()
            for key in [k for k, v in self.sessions.items() if now - v.touched > 3600]:
                del self.sessions[key]
            state = self.sessions.get(request.run_id)
            if state is not None and 1 < request.step_id < state.last_step:
                return self._decision(
                    "block",
                    "OUT_OF_ORDER_REQUEST",
                    "Non-initial step arrived out of order; evidence cannot be rolled back.",
                )
            if self.persistence and state is None and request.step_id > 1:
                return self._decision(
                    "block",
                    "SESSION_CONTEXT_LOST",
                    "Prior session evidence is unavailable; restart the task from its first step.",
                )
            if state is None or request.step_id < state.last_step or not self.persistence:
                if state is None and len(self.sessions) >= self.max_sessions:
                    return self._decision(
                        "block", "SESSION_CAPACITY", "Session capacity reached; restart after review."
                    )
                state = Session()
                self.sessions[request.run_id] = state
            state.touched, state.last_step = now, request.step_id
            if not self._observe(request, state):
                return self._decision("block", "EVIDENCE_CAPACITY", "Evidence budget exhausted; human review required.")
            result = self._decide(request, state)
            if self.flow and self.streaming and result.decision in {"allow", "rewrite", "escalate"}:
                effective = result.rewritten_action or request.candidate_action
                key = (request.step_id, effective.digest())
                if key not in state.releases:
                    for sink, value in egress_fields(effective).items():
                        state.egress[sink] = (state.egress.get(sink, "") + value)[-16_000:]
                    state.releases.add(key)
            return result

    def _decision(self, decision, code, explanation, *, rewrite=None, evidence=None, risk=None):
        return DefenseDecision(
            decision=decision,
            risk_score=risk
            if risk is not None
            else {"allow": 0.05, "block": 0.95, "escalate": 0.65, "rewrite": 0.8}[decision],
            confidence=0.9 if decision in {"allow", "block"} else 0.8,
            reason_codes=[code],
            explanation=explanation,
            rewritten_action=rewrite,
            metadata={"method": "aegis-v1", "risk_kind": "ordinal_not_probability", "evidence": (evidence or [])[:8]},
        )

    def _decide(self, request, state):
        original = request.candidate_action
        action = original.confirmation_for if original.type == ActionType.REQUEST_CONFIRMATION else original
        policy = request.policy_context
        allowed = policy.get("allowed_tools", [])
        if action.type == ActionType.TOOL_CALL:
            if action.tool not in allowed or action.tool not in TOOLS:
                return self._decision("block", "TOOL_OUTSIDE_POLICY", "Tool is outside the active task policy.")
            try:
                TOOLS[action.tool].args_model.model_validate(action.arguments)
            except ValueError:
                fixed = (
                    repair_read_arguments(action, TOOLS[action.tool]) if self.repair and self.argument_repair else None
                )
                if fixed and original.type == ActionType.TOOL_CALL:
                    replacement, changes = fixed
                    check = self._decide(request.model_copy(update={"candidate_action": replacement}), state)
                    if check.decision == "allow":
                        return self._decision(
                            "rewrite",
                            "READ_ARGUMENTS_REPAIRED",
                            "Renamed unambiguous read-only arguments; preserved values and rechecked policy.",
                            rewrite=replacement,
                            evidence=[{"renamed": changes}],
                            risk=0.2,
                        )
                return self._decision("block", "INVALID_TOOL_ARGUMENTS", "Arguments do not satisfy the tool schema.")

        if self.flow:
            external = False
            if action.tool in {"email_send", "email_draft"}:
                address = str(action.arguments.get("to", ""))
                domain = address.rsplit("@", 1)[-1].casefold()
                external = domain not in [d.casefold() for d in policy.get("internal_email_domains", [])]
            # Credentials stay at their source; other confidential identifiers may be used internally.
            secrets = [s for s in state.secrets.values() if s.credential or external]
            hits = matches(action.text_payload(), secrets)
            retry = (request.step_id, action.digest()) in state.releases
            streams = egress_fields(action) if self.streaming and not retry else {}
            if len(set(state.egress) | set(streams)) > 512 or len(state.releases) >= 8192:
                return self._decision(
                    "block", "EGRESS_CAPACITY", "Too many output streams; fresh task review required."
                )
            if not hits:
                for sink, value in streams.items():
                    prior = state.egress.get(sink, "")
                    stitched = matches(prior + value, secrets) if prior else []
                    if stitched:
                        return self._decision(
                            "block",
                            "CROSS_ACTION_DISCLOSURE",
                            "This fragment would complete a known secret across earlier authorized output fields.",
                            evidence=[
                                {"source": s.source, "encoding": e, "scope": "same_destination_field"}
                                for s, e in stitched
                            ],
                        )
                if self.unordered:
                    scattered = unordered_disclosures(state.egress, streams, secrets)
                    if scattered:
                        secret, encoding, destination, covered, total = scattered
                        return self._decision(
                            "block",
                            "REORDERED_FRAGMENT_DISCLOSURE",
                            "Prior and proposed fields reveal most of a known credential in any order.",
                            evidence=[
                                {
                                    "source": secret.source,
                                    "encoding": encoding,
                                    "destination": destination,
                                    "covered": covered,
                                    "total": total,
                                }
                            ],
                        )
            if hits:
                evidence = [{"source": s.source, "encoding": e, "sensitivity": s.sensitivity} for s, e in hits]
                safe = self._repair(action, [s for s, _ in hits]) if self.repair else None
                if safe is not None and not matches(safe.text_payload(), secrets):
                    # New bytes invalidate old human approvals. Never send a modified message directly.
                    if safe.tool == "email_send":
                        if "email_draft" not in allowed:
                            safe = None
                        else:
                            safe = safe.model_copy(update={"tool": "email_draft"})
                    if safe is not None and original.type != ActionType.REQUEST_CONFIRMATION:
                        # Recheck every other constraint before emitting a rewrite.
                        probe = request.model_copy(update={"candidate_action": safe})
                        checked = self._decide(probe, state)
                        if checked.decision in {"allow", "rewrite"}:
                            return self._decision(
                                "rewrite",
                                "SENSITIVE_FLOW_REPAIRED",
                                "Removed source-derived sensitive data; retained safe content.",
                                rewrite=checked.rewritten_action or safe,
                                evidence=evidence + checked.metadata.get("evidence", []),
                            )
                return self._decision(
                    "block",
                    "SENSITIVE_FLOW_BLOCKED",
                    "Sensitive data cannot cross this action boundary.",
                    evidence=evidence,
                )

        if self.authority:
            if (
                action.type == ActionType.MEMORY_WRITE
                and state.untrusted
                and MEMORY_AUTHORITY.search(action.content or "")
            ):
                return self._decision(
                    "block",
                    "MEMORY_AUTHORITY_PROMOTION",
                    "Untrusted context cannot establish durable policy or approval.",
                    evidence=[{"source": s} for s, _ in state.untrusted[-3:]],
                )
            if (
                action.type == ActionType.TOOL_CALL
                and TOOLS[action.tool].capabilities != frozenset({"read"})
                and action.digest() not in request.history_digest.confirmations_granted
            ):
                for source, text in state.untrusted:
                    if action.tool in text.lower() and DIRECTIVE.search(text):
                        anchors = [
                            str(v)
                            for k, v in action.arguments.items()
                            if v is not None and len(str(v)) >= 4 and k not in {"body", "summary", "note", "text"}
                        ]
                        if anchors and all(compact(v) in compact(text) for v in anchors):
                            return self._decision(
                                "block",
                                "UNTRUSTED_ACTION_AUTHORITY",
                                "Proposed tool and target match a directive in untrusted evidence.",
                                evidence=[{"source": source}],
                            )

        if action.type == ActionType.TOOL_CALL:
            if action.tool in {"payment_confirm", "payment_execute", "remediation_execute"}:
                key = "payment_id" if action.tool.startswith("payment") else "remediation_id"
                expected = "confirmed" if action.tool == "payment_execute" else "prepared"
                if state.objects.get(str(action.arguments.get(key))) != expected:
                    return self._decision(
                        "block",
                        "OBJECT_LIFECYCLE_MISSING",
                        "This exact object lacks an observed successful prerequisite.",
                    )
            consequential = (
                TOOLS[action.tool].is_consequential(action.arguments)
                or action.tool in policy.get("confirmation_required_tools", [])
                or action.tool in policy.get("consequential_tools", [])
            )
            confirmed = action.digest() in request.history_digest.confirmations_granted
            if consequential and not confirmed:
                if original.type == ActionType.REQUEST_CONFIRMATION:
                    return self._decision(
                        "allow", "BOUND_CONFIRMATION_REQUEST", "Human review is bound to this exact action.", risk=0.3
                    )
                if self.repair and action.tool == "email_send" and "email_draft" in allowed:
                    safe = action.model_copy(update={"tool": "email_draft"})
                    return self._decision(
                        "rewrite",
                        "SEND_DEFERRED_TO_DRAFT",
                        "Preserved message as a draft pending explicit approval.",
                        rewrite=safe,
                        risk=0.6,
                    )
                return self._decision(
                    "escalate",
                    "BOUND_APPROVAL_REQUIRED",
                    "Consequential action requires a trusted approval for its exact arguments.",
                )
        if self.repair and self.completion and action.type == ActionType.RESPOND:
            text, missing = qualify_completion(action.content or "", state.receipts)
            if missing:
                safe = action.model_copy(update={"content": text})
                checked = self._decide(request.model_copy(update={"candidate_action": safe}), state)
                if checked.decision == "allow":
                    return self._decision(
                        "rewrite",
                        "UNVERIFIED_COMPLETION_QUALIFIED",
                        "Qualified completion claims without observed success receipts.",
                        rewrite=safe,
                        evidence=[{"missing_receipt_types": missing}],
                        risk=0.4,
                    )
                return checked
        return self._decision(
            "allow",
            "POLICY_AND_FLOW_SATISFIED",
            "Action satisfies the checked policy and information-flow constraints.",
        )

    def _repair(self, action, secrets):
        if action.type in {ActionType.RESPOND, ActionType.MEMORY_WRITE}:
            return action.model_copy(update={"content": redact(action.content or "", secrets)})
        text_fields = {"body", "subject", "note", "text", "summary", "title", "justification"}
        if action.type == ActionType.TOOL_CALL:
            args = dict(action.arguments)
            for key, value in args.items():
                if isinstance(value, str) and matches(value, secrets):
                    if key not in text_fields:
                        return None
                    args[key] = redact(value, secrets)
            return action.model_copy(update={"arguments": args})
        return None
