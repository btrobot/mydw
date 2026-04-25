from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = ROOT / "remote" / "remote-backend"
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app.core.config import reset_settings_cache
from app.core.db import reset_db_state
from app.migrations.alembic import (
    BASELINE_REVISION,
    downgrade_to,
    ensure_database_on_head,
    get_current_revision,
    stamp_revision,
    upgrade_head,
    upgrade_to,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run remote-backend Alembic migration commands.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade the database to the requested revision")
    upgrade_parser.add_argument("revision", nargs="?", default="head")

    downgrade_parser = subparsers.add_parser("downgrade", help="Downgrade the database to the requested revision")
    downgrade_parser.add_argument("revision", nargs="?", default="base")

    stamp_parser = subparsers.add_parser("stamp", help="Stamp the database with the requested revision")
    stamp_parser.add_argument("revision", nargs="?", default=BASELINE_REVISION)

    subparsers.add_parser("current", help="Print the current Alembic revision")
    subparsers.add_parser("ensure-head", help="Adopt legacy runner state when needed, then upgrade to head")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    reset_settings_cache()
    reset_db_state()

    if args.command == "upgrade":
        upgrade_head() if args.revision == "head" else upgrade_to(args.revision)
    elif args.command == "downgrade":
        downgrade_to(args.revision)
    elif args.command == "stamp":
        stamp_revision(args.revision)
    elif args.command == "current":
        print(get_current_revision() or "None")
    elif args.command == "ensure-head":
        ensure_database_on_head()
    else:
        raise SystemExit(f"Unsupported command: {args.command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
