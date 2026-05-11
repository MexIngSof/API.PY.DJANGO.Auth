# Generated manually to keep Auth-owned tables out of public.

from django.db import migrations


PUBLIC_TO_AUTH_SQL = """
CREATE SCHEMA IF NOT EXISTS "Auth";
ALTER TABLE IF EXISTS public."Roles" SET SCHEMA "Auth";
ALTER TABLE IF EXISTS public."UserRoles" SET SCHEMA "Auth";
"""


class Migration(migrations.Migration):

    dependencies = [
        ("roles", "0002_initial"),
        ("user", "0002_auth_schema_table"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=PUBLIC_TO_AUTH_SQL,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.AlterModelTable(
                    name="roles",
                    table='"Auth"."Roles"',
                ),
                migrations.AlterModelTable(
                    name="userroles",
                    table='"Auth"."UserRoles"',
                ),
            ],
        ),
    ]
