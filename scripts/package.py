"""Bundle code, unchanged upstream source, docs and the latest completed evidence."""

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
out = ROOT / "output"
out.mkdir(exist_ok=True)
files = set()
for directory in ("aegis", "tests", "docs", "scripts", ".github", "starter-kit"):
    for p in (ROOT / directory).rglob("*"):
        if p.is_file() and not any(
            part in {".git", "__pycache__", ".pytest_cache", ".ruff_cache", ".venv"} for part in p.parts
        ):
            files.add(p)
for name in (
    "README.md",
    "pyproject.toml",
    "requirements-lock.txt",
    "Dockerfile",
    ".dockerignore",
    ".gitignore",
    "UPSTREAM_REVISION",
    ".gitmodules",
):
    files.add(ROOT / name)
selected = {}
for p in sorted((ROOT / "artifacts").glob("*/manifest.json")):
    m = json.loads(p.read_text(encoding="utf-8"))
    if m["model"].startswith("qwen"):
        files.update(item for item in p.parent.rglob("*") if item.is_file())
    selected[(m["reference_commit"], m["model"], m["attack_mode"])] = p.parent
for directory in selected.values():
    files.update(p for p in directory.rglob("*") if p.is_file())
files.add(ROOT / "artifacts/stress.json")
files.add(ROOT / "artifacts/stress-v1.json")
if (ROOT / "artifacts/demo-plan.json").exists():
    files.add(ROOT / "artifacts/demo-plan.json")
if (ROOT / "models/setup-manifest.json").exists():
    files.add(ROOT / "models/setup-manifest.json")
manifest = {
    str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)
}
path = out / "AEGIS-development-package.zip"
with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for p in sorted(files):
        archive.write(p, str(p.relative_to(ROOT)))
    archive.writestr("PACKAGE_SHA256.json", json.dumps(manifest, indent=2))
with zipfile.ZipFile(path) as archive:
    assert archive.testzip() is None
digest = hashlib.sha256(path.read_bytes()).hexdigest()
(out / "AEGIS-development-package.sha256").write_text(f"{digest}  {path.name}\n", encoding="utf-8")
print(f"Packaged {len(files)} files: {path} ({path.stat().st_size:,} bytes)")
