#!/usr/bin/env python3
"""
Export the backend OpenAPI spec to a local frontend file.

This keeps client generation reproducible without requiring a live server.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]
    backend_root = repo_root / "backend"
    frontend_root = repo_root / "frontend"
    output_path = frontend_root / "openapi.local.json"

    if len(sys.argv) > 1:
        output_path = Path(sys.argv[1]).resolve()

    sys.path.insert(0, str(backend_root))

    from main import app  # pylint: disable=import-outside-toplevel

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(app.openapi(), f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
