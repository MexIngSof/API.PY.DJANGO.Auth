from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0003_repair_auth_schema_pascalcase"),
    ]

    operations = [
        migrations.AddField(
            model_name="useraccount",
            name="must_change_password",
            field=models.BooleanField(db_column="MustChangePassword", default=False),
        ),
    ]
