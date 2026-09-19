"""Explicit online setup; pinned publisher model and official inference release."""

import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
assets = [
    (
        "runtime/llama-b10964.zip",
        "https://github.com/ggml-org/llama.cpp/releases/download/b10964/llama-b10964-bin-win-vulkan-x64.zip",
        "1ee3ad952f4ba71f438bd6d7bebef19e1c7af04adcaa35d08b4ddabb27d4c642",
    ),
    (
        "models/Qwen3-8B-Q4_K_M.gguf",
        "https://huggingface.co/Qwen/Qwen3-8B-GGUF/resolve/7c41481f57cb95916b40956ab2f0b139b296d974/Qwen3-8B-Q4_K_M.gguf",
        "d98cdcbd03e17ce47681435b5150e34c1417f50b5c0019dd560e4882c5745785",
    ),
]
for relative, url, expected in assets:
    path = ROOT / relative
    path.parent.mkdir(exist_ok=True)
    print(f"Downloading/resuming {relative}", flush=True)
    existing_hash = None
    if path.exists():
        with path.open("rb") as handle:
            existing_hash = hashlib.file_digest(handle, "sha256").hexdigest()
    if existing_hash != expected:
        subprocess.run(
            [
                "curl.exe",
                "--location",
                "--fail",
                "--retry",
                "3",
                "--silent",
                "--show-error",
                "--continue-at",
                "-",
                "--output",
                str(path),
                url,
            ],
            check=True,
        )
    with path.open("rb") as handle:
        actual = hashlib.file_digest(handle, "sha256").hexdigest()
    if actual != expected:
        raise ValueError(f"Checksum mismatch for {relative}")
    print(f"Verified SHA-256: {relative}", flush=True)
    if path.suffix == ".zip":
        target = ROOT / "runtime/llama"
        target.mkdir(exist_ok=True)
        with zipfile.ZipFile(path) as archive:
            for member in archive.infolist():
                if not (target / member.filename).resolve().is_relative_to(target.resolve()):
                    raise ValueError("Archive path escape")
            archive.extractall(target)
(ROOT / "models/setup-manifest.json").write_text(
    json.dumps({"assets": [{"path": p, "source": u, "sha256": s} for p, u, s in assets]}, indent=2), encoding="utf-8"
)
print("Setup complete. Subsequent inference can run offline.", flush=True)
