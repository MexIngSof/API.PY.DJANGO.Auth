from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("user", "0006_application_scoped_email_identity")]

    operations = [
        migrations.RunSQL(
            sql=(
                'ALTER TABLE "Auth"."UserAccounts" '
                'DROP CONSTRAINT IF EXISTS "user_useraccount_email_key"'
            ),
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
