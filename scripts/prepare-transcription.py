"""Download pinned public weights only; inference subsequently uses local_files_only."""

import hashlib
import json
import os
from pathlib import Path

root = Path(__file__).resolve().parents[1]
os.environ["HF_HOME"] = str(root / ".runtime/huggingface")
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

from huggingface_hub import snapshot_download

revision = "d90ca5fe260221311c53c58e660288d3deb8d356"
files = ["config.json", "model.bin", "tokenizer.json", "vocabulary.txt", "README.md"]
target = root / ".runtime/models/faster-whisper-tiny"
snapshot_download(
    repo_id="Systran/faster-whisper-tiny",
    revision=revision,
    local_dir=target,
    allow_patterns=files,
    token=False,
)
manifest = {
    "repository": "Systran/faster-whisper-tiny",
    "revision": revision,
    "license": "MIT",
    "sha256": {name: hashlib.sha256((target / name).read_bytes()).hexdigest() for name in files},
}
(target / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf8")
print(f"Modelo local preparado: {target}")
