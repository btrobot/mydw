from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
APP_ROOT = ROOT / 'remote' / 'remote-backend'
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from app.core.config import reset_settings_cache
from app.core.db import reset_db_state, session_scope
from app.core.security import hash_account_password
from app.migrations.alembic import ensure_database_on_head
from app.models import AdminUser


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Create or update a remote admin bootstrap user.')
    parser.add_argument('--username', required=True, help='Admin username')
    parser.add_argument('--role', default='super_admin', help='Admin role to assign')
    parser.add_argument('--display-name', default=None, help='Display name to show in the admin console')
    parser.add_argument('--status', default='active', help='Admin status to set')
    parser.add_argument('--migrate', action='store_true', help='Run backend migrations before bootstrapping the admin user')
    password_group = parser.add_mutually_exclusive_group(required=True)
    password_group.add_argument('--password', help='Admin password (least safe; avoid in shared environments)')
    password_group.add_argument('--password-env', help='Read the admin password from the named environment variable')
    password_group.add_argument('--password-stdin', action='store_true', help='Read the admin password from stdin')
    return parser.parse_args()


def bootstrap_admin(*, username: str, password: str, role: str, display_name: str | None, status: str) -> dict[str, str]:
    with session_scope() as session:
        admin_user = session.query(AdminUser).filter_by(username=username).one_or_none()
        created = admin_user is None
        password_record = hash_account_password(password)
        if admin_user is None:
            admin_user = AdminUser(
                username=username,
                display_name=display_name or username,
                password_hash=password_record.value,
                password_algo=password_record.algorithm,
                role=role,
                status=status,
            )
            session.add(admin_user)
            session.flush()
        else:
            admin_user.display_name = display_name or admin_user.display_name or username
            admin_user.password_hash = password_record.value
            admin_user.password_algo = password_record.algorithm
            admin_user.role = role
            admin_user.status = status
            session.flush()

        return {
            'result': 'created' if created else 'updated',
            'username': admin_user.username,
            'role': admin_user.role,
            'status': admin_user.status,
            'display_name': admin_user.display_name or '',
        }


def resolve_password(args: argparse.Namespace) -> str:
    if args.password is not None:
        return args.password
    if args.password_env is not None:
        import os

        value = os.getenv(args.password_env)
        if not value:
            raise SystemExit(f'Environment variable {args.password_env} is not set or empty.')
        return value
    if args.password_stdin:
        value = sys.stdin.readline().rstrip('\r\n')
        if not value:
            raise SystemExit('stdin password is empty.')
        return value
    raise SystemExit('No password input provided.')


def main() -> int:
    args = parse_args()
    password = resolve_password(args)
    reset_settings_cache()
    reset_db_state()
    if args.migrate:
        ensure_database_on_head()
    result = bootstrap_admin(
        username=args.username,
        password=password,
        role=args.role,
        display_name=args.display_name,
        status=args.status,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
