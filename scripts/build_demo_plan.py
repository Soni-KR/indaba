"""Choose disclosed demonstration models only after per-scenario undefended checks."""

import json
from pathlib import Path

from aegis.evidence import load_manifest

ROOT = Path(__file__).resolve().parents[1]
revision = (ROOT / "UPSTREAM_REVISION").read_text(encoding="utf-8").strip()
manifests = [load_manifest(p) for p in sorted((ROOT / "artifacts").glob("*/manifest.json"))]


def latest(model):
    choices = [
        m
        for m in manifests
        if m["reference_commit"] == revision
        and m["model"] == model
        and m["attack_mode"] == "static"
        and any(r["variant"] == "aegis" and r["seed"] == 0 and r["scenario_count"] == 19 for r in m["reports"])
    ]
    return choices[-1] if choices else None


mock = latest("mock")
qwen = latest("qwen3-8b-q4_k_m-stock")
if not mock:
    raise SystemExit("Run a complete current-revision mock comparison before generating a demo plan.")


def defense_hashes(manifest):
    names = {"aegis/defense.py", "aegis/flow.py", "aegis/repairs.py"}
    return {name.replace("\\", "/"): digest for name, digest in manifest["solution_hashes"].items()
            if name.replace("\\", "/") in names}


if qwen and defense_hashes(qwen) != defense_hashes(mock):
    qwen = None  # Never silently mix different defense versions into the current demo plan.


def cases(manifest):
    if not manifest:
        return {}
    row = next(r for r in manifest["reports"] if r["variant"] == "aegis" and r["seed"] == 0)
    return {c["scenario_id"]: c for c in row["attack_validation"]["cases"]}


mock_cases, qwen_cases = cases(mock), cases(qwen)
rows = []
for name, fallback in sorted(mock_cases.items()):
    real = qwen_cases.get(name)
    use_real = bool(real and real["eligible"])
    manifest, selected = (qwen, real) if use_real else (mock, fallback)
    if not selected["eligible"]:
        raise SystemExit(f"No validated baseline for {name}; cannot recommend this demonstration.")
    rows.append(
        {
            "scenario": name,
            "model": manifest["model"],
            "experiment": manifest["created"],
        "reference_commit": revision,
        "defense_hashes": defense_hashes(manifest),
            "seed": 0,
            "allow_all_attack_success": selected["allow_all_attack_success"],
            "aegis_attack_success": selected["defended_attack_success"],
            "aegis_task_success": selected["task_success"],
            "selection_reason": "Qwen passes per-scenario allow-all prerequisite"
            if use_real
            else "Qwen has no successful paired undefended attack; use disclosed mock fallback",
            "qwen_eligible": bool(real and real["eligible"]),
            "baseline_trace": f"artifacts/{manifest['created']}/allow_all-s0/{name}-allow_all-s0.jsonl",
            "defense_trace": f"artifacts/{manifest['created']}/aegis-s0/{name}-aegis-s0.jsonl",
        }
    )
    for field in ("baseline_trace", "defense_trace"):
        if not (ROOT / rows[-1][field]).exists():
            raise SystemExit(f"Missing trace: {rows[-1][field]}")

result = {
    "reference_commit": revision,
    "selection": "per-scenario allow-all prerequisite; no hidden outcome filtering",
    "cases": rows,
}
(ROOT / "artifacts/demo-plan.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
lines = [
    "# Validated demonstration plan",
    "",
    f"Organizer revision: `{revision}`.",
    "",
    (
        "Each selected configuration has an undefended successful attack for the same scenario and seed. "
        "Qwen is preferred only when it passes that prerequisite. Otherwise the model is explicitly MOCK. "
        "A failed defended task or successful defended attack is retained, not filtered out."
    ),
    "",
    "| Scenario | Model | Undefended attack | AEGIS attack | AEGIS task | Experiment |",
    "|---|---|---|---|---|---|",
]
for row in rows:
    lines.append(
        f"| {row['scenario']} | {row['model']} | succeeds | "
        f"{'SUCCEEDS' if row['aegis_attack_success'] else 'prevented'} | "
        f"{'PASS' if row['aegis_task_success'] else 'FAIL'} | `{row['experiment']}` |"
    )
lines += [
    "",
    (
        "Show the allow-all trace first, then the paired AEGIS trace. Keep the model and experiment visible. "
        "Use the dashboard selector; do not present mock traces as Qwen. Machine-readable trace paths and "
        "selection reasons are in `artifacts/demo-plan.json`."
    ),
]
(ROOT / "docs/demo-evidence.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(
    f"Validated {len(rows)} demo scenarios: {sum(r['qwen_eligible'] for r in rows)} Qwen, "
    f"{sum(not r['qwen_eligible'] for r in rows)} mock."
)
