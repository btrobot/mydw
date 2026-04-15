from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
ARTIFACT_ROOT = ROOT / "remote" / "remote-shared"
FIXTURE_ROOT = ARTIFACT_ROOT / "scripts" / "compat-harness" / "fixtures"
OUTPUT = ARTIFACT_ROOT / "openapi" / "phase1-manifest.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_manifest() -> dict:
    docs = sorted((ARTIFACT_ROOT / "docs").glob("*.md"))
    fixtures = sorted(FIXTURE_ROOT.glob("*.json"))
    return {
        "version": "phase1-v1",
        "openapi_source": {
            "file": "remote-auth-v1.yaml",
            "sha256": sha256_file(ARTIFACT_ROOT / "openapi" / "remote-auth-v1.yaml"),
        },
        "openapi_runtime": {
            "file": "remote-auth-runtime.json",
            "sha256": sha256_file(ARTIFACT_ROOT / "openapi" / "remote-auth-runtime.json"),
        },
        "docs": [{"file": path.name, "sha256": sha256_file(path)} for path in docs],
        "fixtures": [{"file": path.name, "sha256": sha256_file(path)} for path in fixtures],
        "error_code_matrix": {
            "file": "error-codes.json",
            "sha256": sha256_file(ARTIFACT_ROOT / "scripts" / "compat-harness" / "error-codes.json"),
        },
    }


def main() -> None:
    manifest = build_manifest()
    OUTPUT.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
