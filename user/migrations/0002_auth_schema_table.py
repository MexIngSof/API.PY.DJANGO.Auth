# Generated manually to keep Auth-owned tables out of public.

from django.db import migrations, models


PUBLIC_TO_AUTH_SQL = """
CREATE SCHEMA IF NOT EXISTS "Auth";
ALTER TABLE IF EXISTS public.user_useraccount RENAME COLUMN id TO "Id";
ALTER TABLE IF EXISTS public.user_useraccount RENAME COLUMN password TO "Password";
ALTER TABLE IF EXISTS public.user_useraccount RENAME COLUMN last_login TO "LastLogin";
ALTER TABLE IF EXISTS public.user_useraccount RENAME COLUMN first_name TO "FirstName";
ALTER TABLE IF EXISTS public.user_useraccount RENAME COLUMN last_name TO "LastName";
ALTER TABLE IF EXISTS public.user_useraccount RENAME COLUMN email TO "Email";
ALTER TABLE IF EXISTS public.user_useraccount RENAME COLUMN is_active TO "IsActive";
ALTER TABLE IF EXISTS public.user_useraccount RENAME COLUMN is_staff TO "IsStaff";
ALTER TABLE IF EXISTS public.user_useraccount RENAME COLUMN is_superuser TO "IsSuperuser";
ALTER TABLE IF EXISTS public.user_useraccount RENAME COLUMN "idApp" TO "ApplicationId";
ALTER TABLE IF EXISTS public.user_useraccount SET SCHEMA "Auth";
ALTER TABLE IF EXISTS "Auth".user_useraccount RENAME TO "UserAccounts";
"""


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0001_initial"),
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
