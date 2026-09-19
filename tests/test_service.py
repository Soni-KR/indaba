import json

import pytest
from fastapi.testclient import TestClient

from aegis.app import app
from aegis.audit import AuditedDefense, verify
from aegis.defense import AegisDefense
from tests.test_defense import SECRET, action, request


def test_contract_and_ui():
    client = TestClient(app)
    assert client.get("/healthz").json()["status"] == "ok"
    assert "Safety observatory" in client.get("/").text
    r = client.post("/v1/decision", json=request(action()).model_dump(mode="json"))
    assert r.status_code == 200
    assert r.json()["decision"] == "allow"
    assert client.post("/v1/decision", json={"unexpected": True}).status_code == 422
    assert client.get("/api/runs/not-a-known-id").status_code == 404


def test_audit_redacts_and_detects_tampering(tmp_path):
    path = tmp_path / "audit.jsonl"
    d = AuditedDefense(AegisDefense(), path)
    d.decide(request(action(content=SECRET), content=json.dumps({"token": SECRET})))
    assert SECRET not in path.read_text()
    assert verify(path)["entries"] == 1
    data = json.loads(path.read_text())
    data["decision"]["decision"] = "allow"
    path.write_text(json.dumps(data) + "\n")
    with pytest.raises(ValueError, match="mismatch"):
        verify(path)


def test_trace_remains_readable_during_audit_append(tmp_path, monkeypatch):
    import aegis.app as service

    monkeypatch.setattr(service, "ARTIFACTS", tmp_path)
    batch = tmp_path / "batch"
    group = batch / "aegis-s0"
    group.mkdir(parents=True)
    trace = group / "example.jsonl"
    trace.write_text(json.dumps({"run_id": "r", "step_id": 1, "type": "defense_decision"}) + "\n")
    receipt = {"run_id": "r", "step_id": 1, "hash": "recorded-hash"}
    audit = batch / "aegis-s0.audit.jsonl"
    prefix = json.dumps(receipt) + "\n"
    audit.write_text(prefix + '{"run_id":')
    client = TestClient(app)
    trace_id = next(r["id"] for r in client.get("/api/runs").json() if r["kind"] == "simulator")
    response = client.get(f"/api/runs/{trace_id}")
    assert response.status_code == 200
    assert response.json()[0]["audit"] == receipt
    # Interior corruption is surfaced, rather than silently hiding a decision.
    audit.write_text(prefix + '{broken}\n' + json.dumps(receipt) + "\n")
    assert client.get(f"/api/runs/{trace_id}").status_code == 409
