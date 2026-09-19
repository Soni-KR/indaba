"""Local hash-chained evidence. Tamper-evident relative to a retained final hash, not signed."""

import hashlib
import json
import threading
import time
from pathlib import Path

from sentinel.defenses.interface import Defense

from aegis.flow import redact


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode()


def scrub(value, secrets):
    if isinstance(value, dict):
        return {k: scrub(v, secrets) for k, v in value.items()}
    if isinstance(value, list):
        return [scrub(v, secrets) for v in value]
    return redact(value, secrets) if isinstance(value, str) else value


def verify(path):
    previous = "0" * 64
    count = 0
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        entry = json.loads(line)
        claimed = entry.pop("hash")
        if entry.get("previous_hash") != previous or hashlib.sha256(canonical(entry)).hexdigest() != claimed:
            raise ValueError(f"Audit chain mismatch at entry {count}")
        previous = claimed
        count += 1
    return {"entries": count, "head": previous, "valid": True}


class AuditedDefense(Defense):
    def __init__(self, inner, path):
        self.inner, self.path, self.name = inner, Path(path), inner.name
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.previous = verify(self.path)["head"] if self.path.exists() else "0" * 64
        self.lock = threading.Lock()

    def decide(self, request):
        with self.lock:
            start = time.perf_counter()
            decision = self.inner.decide(request)
            elapsed = (time.perf_counter() - start) * 1000
            state = getattr(self.inner, "sessions", {}).get(request.run_id)
            secrets = list(state.secrets.values()) if state else []
            entry = {
                "run_id": request.run_id,
                "step_id": request.step_id,
                "action": scrub(request.candidate_action.model_dump(mode="json"), secrets),
                "decision": scrub(decision.model_dump(mode="json"), secrets),
                "latency_ms": round(elapsed, 3),
                "sources": [
                    {"id": p.id, "trust": p.provenance.trust_level.value, "sensitivity": p.provenance.sensitivity.value}
                    for p in request.provenance
                ],
                "previous_hash": self.previous,
            }
            # Redact candidate and observations independently; never log a raw request or secret store.
            entry["observations"] = [
                {
                    "role": i.role,
                    "kind": i.kind,
                    "content": redact(i.content, secrets)[:2000],
                    "provenance_ids": i.provenance_ids,
                }
                for i in request.conversation[-3:]
            ]
            entry["hash"] = hashlib.sha256(canonical(entry)).hexdigest()
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, ensure_ascii=True) + "\n")
            self.previous = entry["hash"]
            return decision

    def close(self):
        self.inner.close()
