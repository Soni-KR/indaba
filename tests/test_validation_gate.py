import json

from aegis.evidence import attack_gate, load_manifest


def outcome(name, attack, *, seed=0, present=True):
    return {
        "scenario_id": name,
        "seed": seed,
        "attack_present": present,
        "attack_success": attack,
        "task_success": True,
    }


def test_zero_attacks_is_not_protection_without_exercised_baseline():
    result = attack_gate([outcome("a", False)], [outcome("a", False)])
    assert result["status"] == "unvalidated"
    assert result["eligible_attacks"] == 0


def test_gate_matches_each_scenario_and_seed_not_aggregate_success():
    cases = [outcome("a", False), outcome("b", False), outcome("c", False, seed=1)]
    baseline = [outcome("a", True), outcome("b", False), outcome("c", True, seed=0)]
    result = attack_gate(cases, baseline)
    assert result["status"] == "partial"
    assert result["eligible_attacks"] == 1
    assert result["unvalidated_attacks"] == 2
    assert result["successful_attacks_on_eligible"] == 0


def test_actual_attack_failure_remains_visible_and_benign_is_not_an_attack():
    cases = [outcome("a", True), outcome("b", False, present=False)]
    result = attack_gate(cases, cases)
    assert result["status"] == "passed"
    assert result["eligible_attacks"] == result["successful_attacks_on_eligible"] == 1


def test_historical_gate_does_not_modify_original_manifest(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({"reports": [{"variant": "aegis", "seed": 0}]}), encoding="utf-8")
    original = path.read_bytes()
    (tmp_path / "aegis-s0.json").write_text(json.dumps({"outcomes": [outcome("a", False)]}), encoding="utf-8")
    result = load_manifest(path)
    assert result["reports"][0]["attack_validation"]["status"] == "unvalidated"
    assert path.read_bytes() == original
