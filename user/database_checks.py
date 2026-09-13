import sys

from django.conf import settings
from django.core.checks import Error, Tags, register


CANONICAL_DATABASE_NAME = "Auth"
CANONICAL_DATABASE_USER = "Auth"
CANONICAL_DOMAIN_SCHEMA = "Auth"
CANONICAL_RUNTIME_SCHEMA = "AuthRuntime"


def _options_text(database):
    return str((database.get("OPTIONS") or {}).get("options") or "")


@register(Tags.database)
def auth_database_configuration_check(app_configs, **kwargs):
    """Validate Auth PostgreSQL identity before any SQL is executed.

    This check validates configuration only. Physical schema/table placement is
    certified separately by the PostgreSQL ownership/schema-purpose gates.
    """

    database = (settings.DATABASES or {}).get("default") or {}
    engine = str(database.get("ENGINE") or "")
    name = str(database.get("NAME") or "")
    user = str(database.get("USER") or "")
    options = _options_text(database)
    errors = []

    if engine != "django.db.backends.postgresql":
        errors.append(
            Error(
                "Auth must use PostgreSQL.",
                hint="Set DB_ENGINE=django.db.backends.postgresql; SQLite is not allowed.",
                id="auth.E001",
            )
        )

    if name != CANONICAL_DATABASE_NAME:
        errors.append(
            Error(
                f"Auth database NAME must be {CANONICAL_DATABASE_NAME!r}, found {name!r}.",
                hint="Use AUTH_DB_NAME=Auth.",
                id="auth.E002",
            )
        )

    if user != CANONICAL_DATABASE_USER:
        errors.append(
            Error(
                f"Auth database USER must be {CANONICAL_DATABASE_USER!r}, found {user!r}.",
                hint="DB_USER must equal DB_NAME exactly: AUTH_DB_USER=Auth.",
                id="auth.E003",
            )
        )

    if CANONICAL_DOMAIN_SCHEMA not in options or CANONICAL_RUNTIME_SCHEMA not in options:
        errors.append(
            Error(
                "Auth PostgreSQL search_path is missing a canonical schema.",
                hint='Include "Auth" and "AuthRuntime" in AUTH_POSTGRES_OPTIONS/POSTGRES_OPTIONS.',
                id="auth.E004",
            )
        )
    elif "test" not in sys.argv:
        search_path = options.split("search_path=", 1)[-1].strip()
        if not search_path.startswith(f'"{CANONICAL_DOMAIN_SCHEMA}"'):
            errors.append(
                Error(
                    "Auth normal-runtime search_path must start with the Auth domain schema.",
                    hint='Use -c search_path="Auth","AuthRuntime",public outside test databases.',
                    id="auth.E005",
                )
            )

    return errors
