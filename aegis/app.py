"""Loopback-only defense API and offline trace explorer. No CDN or remote assets."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sentinel.core.actions import DefenseDecision
from sentinel.defenses.interface import DefenseRequest

from aegis.audit import AuditedDefense
from aegis.defense import AegisDefense

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
app = FastAPI(title="AEGIS | SENTINEL Defense", version="0.1.0")
stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
defense = AuditedDefense(AegisDefense(), ARTIFACTS / "live" / f"{stamp}.audit.jsonl")
app.mount("/static", StaticFiles(directory=ROOT / "aegis/web"), name="static")


@app.get("/")
def index():
    return FileResponse(ROOT / "aegis/web/index.html")


@app.get("/healthz")
def health():
    return {"status": "ok", "defense": "aegis", "offline": True}


@app.post("/v1/decision", response_model=DefenseDecision)
def decision(request: DefenseRequest):
    return defense.decide(request)


def inventory():
    return {
        hashlib.sha256(str(p.relative_to(ARTIFACTS)).encode()).hexdigest()[:20]: p
        for p in ARTIFACTS.rglob("*.jsonl")
        if not p.is_symlink()
    }


@app.get("/api/runs")
def runs():
    return [
        {
            "id": key,
            "name": p.stem,
            "group": p.parent.name,
            "batch": p.parent.name if ".audit." in p.name else p.parent.parent.name,
            "kind": "audit" if ".audit." in p.name else "simulator",
        }
        for key, p in sorted(inventory().items(), key=lambda kv: str(kv[1]), reverse=True)
    ]


@app.get("/api/runs/{run_id}")
def events(run_id: str):
    path = inventory().get(run_id)
    if not path:
        raise HTTPException(404, "Unknown trace")
    result = read_live_jsonl(path)
    if ".audit." not in path.name and result:
        audit_path = path.parent.parent / f"{path.parent.name}.audit.jsonl"
        if audit_path.exists():
            audits = read_live_jsonl(audit_path)
            by_step = {a["step_id"]: a for a in audits if a["run_id"] == result[0]["run_id"]}
            for event in result:
                if event.get("type") == "defense_decision":
                    event["audit"] = by_step.get(event["step_id"])
    return result


def read_live_jsonl(path):
    """A concurrently appended final record may be incomplete until the next poll."""
    lines = path.read_text(encoding="utf-8").splitlines()
    result = []
    for index, line in enumerate(lines):
        try:
            result.append(json.loads(line))
        except ValueError:
            if index != len(lines) - 1:
                raise HTTPException(409, "Trace contains a malformed interior record; verify the audit file.") from None
    return result


@app.get("/api/reports")
def reports():
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(ARTIFACTS.glob("*/manifest.json"), reverse=True)]
