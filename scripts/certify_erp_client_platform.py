#!/usr/bin/env python3
"""Owner-local Auth runtime gate for ERP Client Platform V1.

A PASS here proves only the Auth database/permission/session checks on PostgreSQL
16.15. It does not prove cross-owner integration, E2E, or production readiness.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# This gate is intentionally runnable on the approved self-hosted certification path.
POSTGRESQL_16_15_ASSERTION = (
    "from django.db import connection; "
    "connection.ensure_connection(); "
    "assert connection.vendor == 'postgresql', "
    "f'PostgreSQL required, got {connection.vendor}'; "
    "assert getattr(connection, 'pg_version', None) == 160015, "
    "f'PostgreSQL 16.15 required, got server_version={getattr(connection, chr(112)+chr(103)+chr(95)+chr(118)+chr(101)+chr(114)+chr(115)+chr(105)+chr(111)+chr(110), None)}'"
)


def run(*args: str) -> None:
    command = [sys.executable, "manage.py", *args]
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True, env=os.environ.copy())


def main() -> int:
    run("check")
    run("makemigrations", "--check", "--dry-run")
    run("shell", "-c", POSTGRESQL_16_15_ASSERTION)
    run("migrate", "--plan")
    run("migrate", "--noinput")
    run(
        "test",
        "user.test_database_checks.AuthDatabaseConfigurationCheckTests.test_django_temporary_database_is_allowed_only_during_test_execution",
        "access.test_customer_enterprise_permissions",
        "access.test_jobcron_product_import_permissions",
        "auth.tests.test_mobile_session_revocation.MobileSessionContractTests",
        "--verbosity",
        "2",
    )
    print(
        json.dumps(
            {
                "component": "Auth",
                "OWNER_LOCAL_RUNTIME_GATE": "PASS",
                "database_requirement": "PostgreSQL 16.15",
                "scope": "owner-local-product-platform-permissions-mobile-session",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
