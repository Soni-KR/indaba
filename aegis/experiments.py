"""Offline evaluation only. Grader outputs never enter the defense boundary."""

import hashlib
import json
import platform
import subprocess
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from sentinel.attackers.baselines.mutation import MutationAttacker
from sentinel.attackers.baselines.static import StaticAttacker
from sentinel.config import CompetitionConfig
from sentinel.defenses.baselines import get_baseline
from sentinel.evaluator.runner import AttackMode, RunConfig, evaluate, load_suite
from sentinel.storage.runs import ArtifactStore

from aegis.audit import AuditedDefense, verify
from aegis.defense import AegisDefense

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = {
    "aegis": {},
    "aegis_v1": {"unordered": False, "argument_repair": False, "completion": False},
    "no_argument_repair": {"argument_repair": False},
    "no_unordered": {"unordered": False},
    "no_completion": {"completion": False},
    "no_flow": {"flow": False},
    "no_authority": {"authority": False},
    "no_persistence": {"persistence": False},
    "no_repair": {"repair": False},
    "no_streaming": {"streaming": False},
}


def reference_revision():
    if (ROOT / "starter-kit/.git").exists():
        try:
            return subprocess.check_output(
                ["git", "-C", str(ROOT / "starter-kit"), "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
            ).strip()
        except (OSError, subprocess.CalledProcessError):
            pass
    return (ROOT / "UPSTREAM_REVISION").read_text(encoding="utf-8").strip()


def run(variants=None, seeds=(0,), adaptive=False, model_path=None, model_url=None, profile="stock", scenarios=None):
    if model_path and model_url:
        raise ValueError("Choose either the stock HF model or the local quantized runtime")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    output = ROOT / "artifacts" / stamp
    output.mkdir(parents=True)
    suite = load_suite(ROOT / "starter-kit/scenarios/public")
    if scenarios:
        selected = set(scenarios)
        suite = [s for s in suite if s.id in selected]
        if {s.id for s in suite} != selected:
            raise ValueError("Requested scenario is not in the public suite")
    reports = []
    for seed in seeds:
        for variant in variants or ["allow_all", "provenance", *VARIANTS]:

            def factory(variant=variant, seed=seed):
                inner = AegisDefense(**VARIANTS[variant]) if variant in VARIANTS else get_baseline(variant)
                inner.name = variant
                return AuditedDefense(inner, output / f"{variant}-s{seed}.audit.jsonl")

            config = RunConfig(
                root=ROOT / "starter-kit",
                competition=CompetitionConfig(run_seed=seed),
                attack_mode=AttackMode.ADAPTIVE if adaptive else AttackMode.STATIC,
                artifacts=ArtifactStore(output),
                artifact_group=f"{variant}-s{seed}",
            )
            if model_path:
                from sentinel.models.hf_adapter import HFModelAdapter

                config.model_factory = lambda: HFModelAdapter(model_path=model_path)
                config.include_reference_plan = False
            if model_url:
                from aegis.local_model import LocalQwenAdapter

                config.model_factory = lambda variant=variant, seed=seed: LocalQwenAdapter(
                    model_url, profile, trace_path=output / f"{variant}-s{seed}.model.log"
                )
                config.include_reference_plan = False
            report = evaluate(suite, factory, config, MutationAttacker if adaptive else StaticAttacker)
            view = report.participant_view()
            (output / f"{variant}-s{seed}.json").write_text(json.dumps(view, indent=2), encoding="utf-8")
            families = defaultdict(lambda: {"runs": 0, "tasks_completed": 0, "attack_successes": 0})
            for outcome in view["outcomes"]:
                family = families[outcome["attack_family"]]
                family["runs"] += 1
                family["tasks_completed"] += outcome["task_success"]
                family["attack_successes"] += outcome["attack_success"]
            row = {
                "variant": variant,
                "seed": seed,
                "scenario_count": view["scenario_count"],
                "tasks_completed": sum(o["task_success"] for o in view["outcomes"]),
                "attack_runs": sum(o["attack_present"] for o in view["outcomes"]),
                "attack_successes": sum(o["attack_success"] for o in view["outcomes"]),
                "critical_violations": sum(o["critical_violation"] for o in view["outcomes"]),
                "metrics": view["metrics"],
                "families": dict(families),
                "digest": view["deterministic_digest"],
                "audit": verify(output / f"{variant}-s{seed}.audit.jsonl"),
            }
            reports.append(row)
            print(
                f"{variant} seed={seed}: tasks {row['tasks_completed']}/{row['scenario_count']}; "
                f"attack successes {row['attack_successes']}/{row['attack_runs']}",
                flush=True,
            )
    manifest = {
        "created": stamp,
        "model": f"qwen3-8b-q4_k_m-{profile}" if model_url else "qwen3-8b" if model_path else "mock",
        "model_path": model_path,
        "model_url": model_url,
        "model_profile": profile if model_url else None,
        "reference_prompt_unchanged": profile == "stock" if model_url else None,
        "runtime_settings": {"max_new_tokens": 768, "enable_thinking": False, "temperature": 0, "model_seed": 0}
        if model_url else None,
        "model_setup": json.loads((ROOT / "models/setup-manifest.json").read_text(encoding="utf-8"))
        if model_url and (ROOT / "models/setup-manifest.json").exists()
        else None,
        "attack_mode": "adaptive" if adaptive else "static",
        "python": platform.python_version(),
        "solution_hashes": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((ROOT / "aegis").rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts
        },
        "reference_commit": reference_revision(),
        "reports": reports,
        "limitations": [
            "Local diagnostics, not jury scores.",
            "Mock model results are not evidence of reference-model robustness.",
            "Public scenarios are development data, not an independent holdout.",
        ],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Evidence: {output}", flush=True)
    return output
