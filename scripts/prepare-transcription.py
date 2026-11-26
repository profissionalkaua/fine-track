"""Download pinned public weights only; inference subsequently uses local_files_only."""

import argparse
import hashlib
import json
import os
from pathlib import Path

root = Path(__file__).resolve().parents[1]
os.environ["HF_HOME"] = str(root / ".runtime/huggingface")
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"

from huggingface_hub import snapshot_download

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--model", choices=["tiny", "small"], default="tiny")
args = parser.parse_args()
revisions = {
    "tiny": ("d90ca5fe260221311c53c58e660288d3deb8d356",
             "dcb76c6586fc06cbdac6dd21f14cfd129cc4cdd9dce19bf4ffa62e59cbe6e6d1"),
    "small": ("536b0662742c02347bc0e980a01041f333bce120",
              "3e305921506d8872816023e4c273e75d2419fb89b24da97b4fe7bce14170d671"),
}
revision, expected_hash = revisions[args.model]
repository = f"Systran/faster-whisper-{args.model}"
files = ["config.json", "model.bin", "tokenizer.json", "vocabulary.txt", "README.md"]
target = root / f".runtime/models/faster-whisper-{args.model}"
snapshot_download(
    repo_id=repository,
    revision=revision,
    local_dir=target,
    allow_patterns=files,
    token=False,
)
manifest = {
    "repository": repository,
    "revision": revision,
    "license": "MIT",
    "sha256": {name: hashlib.sha256((target / name).read_bytes()).hexdigest() for name in files},
}
if manifest["sha256"]["model.bin"] != expected_hash:
    raise SystemExit("Hash dos pesos diverge da revisão aprovada.")
(target / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf8")
print(f"Modelo local preparado: {target}")
