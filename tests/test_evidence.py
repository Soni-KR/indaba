from sentinel.attackers.baselines.static import StaticAttacker
from sentinel.config import CompetitionConfig
from sentinel.evaluator.runner import RunConfig, evaluate, load_suite

from aegis.defense import AegisDefense
from aegis.experiments import ROOT


def test_full_public_suite_and_deterministic_digest():
    suite = load_suite(ROOT / "starter-kit/scenarios/public")
    config = RunConfig(root=ROOT / "starter-kit", competition=CompetitionConfig(run_seed=31))
    first = evaluate(suite, AegisDefense, config, StaticAttacker)
    second = evaluate(suite, AegisDefense, config, StaticAttacker)
    assert len(first.outcomes) == 19
    assert all(o.task_success and not o.attack_success and not o.critical_violation for o in first.outcomes)
    assert first.deterministic_digest == second.deterministic_digest
