from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
REMOTE_BACKEND_ROOT = ROOT / "remote" / "remote-backend"
OUTPUT = ROOT / "remote" / "remote-shared" / "openapi" / "remote-auth-runtime.json"


def build_runtime_spec() -> dict:
    if str(REMOTE_BACKEND_ROOT) not in sys.path:
        sys.path.insert(0, str(REMOTE_BACKEND_ROOT))
    from app.main import create_app  # noqa: WPS433

    app = create_app()
    return app.openapi()


def main() -> None:
    spec = build_runtime_spec()
    OUTPUT.write_text(json.dumps(spec, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
