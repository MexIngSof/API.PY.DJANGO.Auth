from django.db import migrations, models


REPAIR_AUTH_SCHEMA_SQL = """
CREATE SCHEMA IF NOT EXISTS "Auth";
CREATE SCHEMA IF NOT EXISTS "AuthRuntime";

ALTER TABLE IF EXISTS "Auth".user_useraccount RENAME COLUMN id TO "Id";
ALTER TABLE IF EXISTS "Auth".user_useraccount RENAME COLUMN password TO "Password";
ALTER TABLE IF EXISTS "Auth".user_useraccount RENAME COLUMN last_login TO "LastLogin";
ALTER TABLE IF EXISTS "Auth".user_useraccount RENAME COLUMN first_name TO "FirstName";
ALTER TABLE IF EXISTS "Auth".user_useraccount RENAME COLUMN last_name TO "LastName";
ALTER TABLE IF EXISTS "Auth".user_useraccount RENAME COLUMN email TO "Email";
ALTER TABLE IF EXISTS "Auth".user_useraccount RENAME COLUMN is_active TO "IsActive";
ALTER TABLE IF EXISTS "Auth".user_useraccount RENAME COLUMN is_staff TO "IsStaff";
ALTER TABLE IF EXISTS "Auth".user_useraccount RENAME COLUMN is_superuser TO "IsSuperuser";
ALTER TABLE IF EXISTS "Auth".user_useraccount RENAME COLUMN "idApp" TO "ApplicationId";
ALTER TABLE IF EXISTS "Auth".user_useraccount RENAME TO "UserAccounts";

ALTER TABLE IF EXISTS public.auth_group SET SCHEMA "Auth";
ALTER TABLE IF EXISTS public.auth_group_permissions SET SCHEMA "Auth";
ALTER TABLE IF EXISTS public.auth_permission SET SCHEMA "Auth";
ALTER TABLE IF EXISTS public.django_session SET SCHEMA "Auth";
ALTER TABLE IF EXISTS public.social_auth_association SET SCHEMA "Auth";
ALTER TABLE IF EXISTS public.social_auth_code SET SCHEMA "Auth";
ALTER TABLE IF EXISTS public.social_auth_nonce SET SCHEMA "Auth";
ALTER TABLE IF EXISTS public.social_auth_partial SET SCHEMA "Auth";
ALTER TABLE IF EXISTS public.social_auth_usersocialauth SET SCHEMA "Auth";
ALTER TABLE IF EXISTS public.user_useraccount_groups SET SCHEMA "Auth";
ALTER TABLE IF EXISTS public.user_useraccount_user_permissions SET SCHEMA "Auth";
ALTER TABLE IF EXISTS public.django_content_type SET SCHEMA "AuthRuntime";
ALTER TABLE IF EXISTS public.django_migrations SET SCHEMA "AuthRuntime";
DROP TABLE IF EXISTS public.django_admin_log CASCADE;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("access", "0005_seed_auth_reference_data"),
        ("user", "0002_auth_schema_table"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=REPAIR_AUTH_SCHEMA_SQL,
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
            state_operations=[
                migrations.AlterModelTable(
                    name="useraccount",
                    table='"Auth"."UserAccounts"',
                ),
                migrations.AlterField(
                    model_name="useraccount",
                    name="id",
                    field=models.BigAutoField(
                        db_column="Id",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                migrations.AlterField(
                    model_name="useraccount",
                    name="password",
                    field=models.CharField(db_column="Password", max_length=128),
                ),
                migrations.AlterField(
                    model_name="useraccount",
                    name="last_login",
                    field=models.DateTimeField(blank=True, db_column="LastLogin", null=True),
                ),
                migrations.AlterField(
                    model_name="useraccount",
                    name="first_name",
                    field=models.CharField(db_column="FirstName", max_length=255),
                ),
                migrations.AlterField(
                    model_name="useraccount",
                    name="last_name",
                    field=models.CharField(db_column="LastName", max_length=255),
                ),
                migrations.AlterField(
                    model_name="useraccount",
                    name="email",
                    field=models.EmailField(db_column="Email", max_length=255, unique=True),
                ),
                migrations.AlterField(
                    model_name="useraccount",
                    name="is_active",
                    field=models.BooleanField(db_column="IsActive", default=False),
                ),
                migrations.AlterField(
                    model_name="useraccount",
                    name="is_staff",
                    field=models.BooleanField(db_column="IsStaff", default=False),
                ),
                migrations.AlterField(
                    model_name="useraccount",
                    name="is_superuser",
                    field=models.BooleanField(db_column="IsSuperuser", default=False),
                ),
                migrations.AlterField(
                    model_name="useraccount",
                    name="idApp",
                    field=models.IntegerField(db_column="ApplicationId"),
                ),
            ],
        ),
    ]
