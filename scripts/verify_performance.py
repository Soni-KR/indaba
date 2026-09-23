"""Compare optimized behavior with the frozen hardened implementation and recorded decisions."""

import base64
import importlib.util
import json
import random
import sys
from pathlib import Path

from aegis import flow

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("hardened_baseline", ROOT / "artifacts/performance-baseline/flow.py")
old = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = old
spec.loader.exec_module(old)
rng = random.Random(7241)
checks = 0
for n in range(80):
    raw = "aeoPcOx7" + "".join(rng.choices("abcdefXYZ0123456789", k=24))
    a = old.Secret(raw, "source", "restricted", True)
    b = flow.Secret(raw, "source", "restricted", True)
    variants = [v for _, v in old.variants(raw)]
    variants += [base64.b64encode(v.encode()).decode() for v in variants]
    variants += [
        raw.translate(str.maketrans("aeoPcOx", "аеоРсОх")),
        "Harmless ASCII notice",
        "Ελληνικά: καλημέρα",
        "%%% invalid ===",
    ]
    for value in variants:
        text = "Safe prefix. " + value + " Safe suffix."
        assert [(s.value, e) for s, e in old.matches(text, [a])] == [(s.value, e) for s, e in flow.matches(text, [b])]
        assert old.redact(text, [a]) == flow.redact(text, [b])
        assert set(old.decoded_views(text)) == set(flow.decoded_views(text))
        checks += 1
pairs = [("20260922T185242761643Z", "20260922T190222055363Z"), ("20260922T185313998546Z", "20260922T190233948131Z")]
decisions = 0
for before, after in pairs:
    for p in (ROOT / "artifacts" / after).glob("aegis-s*/*.jsonl"):
        q = ROOT / "artifacts" / before / p.parent.name / p.name

        def get(path):
            return [
                e["payload"]
                for e in map(json.loads, path.read_text(encoding="utf-8").splitlines())
                if e["type"] == "defense_decision"
            ]

        left, right = get(q), get(p)
        assert left == right, p.name
        decisions += len(right)
result = {
    "differential_text_cases": checks,
    "identical_complete_decision_payloads": decisions,
    "pairs": pairs,
    "scope": "Generated text cases and recorded full-suite decisions; not a proof over all inputs",
}
(ROOT / "artifacts/performance-comparison.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(result)
