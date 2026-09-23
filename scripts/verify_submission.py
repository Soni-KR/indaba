"""Check final report claims against saved evidence without rerunning models."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
text = (ROOT / "docs/technical-report.md").read_text(encoding="utf-8")
keys = ["btu", "asr", "cvr", "fbr", "uer", "tui", "dfi", "brier", "ece", "latency_p95_ms"]
for stamp in ["20260923T191236142234Z", "20260923T191249640018Z", "20260923T191303750037Z"]:
    folder = ROOT / "artifacts" / stamp
    manifest = json.loads((folder / "manifest.json").read_text())
    for path, digest in manifest["solution_hashes"].items():
        assert hashlib.sha256((ROOT / path.replace("\\", "/")).read_bytes()).hexdigest() == digest, path
    for row in manifest["reports"]:
        saved = json.loads((folder / f"{row['variant']}-s{row['seed']}.json").read_text())
        assert saved["metrics"] == row["metrics"]
        assert saved["deterministic_digest"] == row["digest"]
        if stamp != "20260923T191303750037Z":
            assert row["digest"] in text
        if stamp == "20260923T191236142234Z" and row["seed"] == 0:
            expected = "| " + " | ".join([row["variant"]] + [f"{row['metrics'][k]:.4f}" for k in keys]) + " |"
            assert expected in text, expected
            if row["variant"] == "aegis":
                for name, m in saved["by_domain"].items():
                    expected = "| " + " | ".join([name] + [f"{m[k]:.4f}" for k in keys]) + " |"
                    assert expected in text
for i, title in enumerate(
    [
        "Abstract",
        "Threat model",
        "Hypothesis",
        "Method",
        "Experiments",
        "Results",
        "Ablations",
        "Failure analysis",
        "Responsible AI and security considerations",
        "Reproducibility",
    ],
    1,
):
    assert f"## {i}. {title}" in text, title
for filename in ["README.md", "docs/technical-report.md", "docs/submission-checklist.md", "docs/video-storyboard.md"]:
    content = (ROOT / filename).read_text(encoding="utf-8")
    for person in ["Mourad has lost a finger", "Mourad Kraiem", "Mohamed Yassin ghaoui", "Amine Fathallah"]:
        assert person in content
    assert "404" not in content and "repository publication and organizer submission remain" not in content
assert (ROOT / "docs/AEGIS-submission-report.pdf").read_bytes() == (
    ROOT / "output/pdf/AEGIS-submission-report.pdf"
).read_bytes()
print(
    "PASS: artifact source hashes, exact main/domain tables, all cited digests, ten template sections, team names and PDF copy."
)
