# Generated manually to keep Auth-owned tables out of public.

from django.db import migrations


PUBLIC_TO_AUTH_SQL = """
CREATE SCHEMA IF NOT EXISTS "Auth";
ALTER TABLE IF EXISTS public."Actions" SET SCHEMA "Auth";
ALTER TABLE IF EXISTS public."Modules" SET SCHEMA "Auth";
ALTER TABLE IF EXISTS public."Permissions" SET SCHEMA "Auth";
ALTER TABLE IF EXISTS public."RolePermissions" SET SCHEMA "Auth";
ALTER TABLE IF EXISTS public."UserPermissions" SET SCHEMA "Auth";
"""


class Migration(migrations.Migration):

    dependencies = [
        ("access", "0002_initial"),
        ("roles", "0003_auth_schema_tables"),
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
                    name="actions",
                    table='"Auth"."Actions"',
                ),
                migrations.AlterModelTable(
                    name="modules",
                    table='"Auth"."Modules"',
                ),
                migrations.AlterModelTable(
                    name="permissions",
                    table='"Auth"."Permissions"',
                ),
                migrations.AlterModelTable(
                    name="rolepermissions",
                    table='"Auth"."RolePermissions"',
                ),
                migrations.AlterModelTable(
                    name="userpermissions",
                    table='"Auth"."UserPermissions"',
                ),
            ],
        ),
    ]
