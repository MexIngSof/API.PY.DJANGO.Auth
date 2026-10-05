from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0005_pascalcase_physical_columns"),
    ]

    operations = [
        migrations.AlterField(
            model_name="useraccount",
            name="email",
            field=models.EmailField(db_column="Email", max_length=255),
        ),
        migrations.AddConstraint(
            model_name="useraccount",
            constraint=models.UniqueConstraint(
                fields=("idApp", "email"),
                name="uq_useraccounts_application_email",
            ),
        ),
        migrations.AddIndex(
            model_name="useraccount",
            index=models.Index(
                fields=("idApp", "email"),
                name="ix_useraccounts_app_email",
            ),
        ),
    ]
