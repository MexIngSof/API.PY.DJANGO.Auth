from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("access", "0038_seed_jobcron_customer_enterprise_permissions"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="GlobalIdentities",
            fields=[
                ("GlobalIdentityID", models.BigAutoField(db_column="Id", primary_key=True, serialize=False)),
                ("IsActive", models.BooleanField(db_column="IsActive", default=True)),
                ("CreatedAt", models.DateTimeField(auto_now_add=True, db_column="CreatedAt")),
                ("UpdatedAt", models.DateTimeField(auto_now=True, db_column="UpdatedAt")),
            ],
            options={"db_table": '"Auth"."GlobalIdentities"'},
        ),
        migrations.CreateModel(
            name="GlobalIdentityAccounts",
            fields=[
                ("GlobalIdentityAccountID", models.BigAutoField(db_column="Id", primary_key=True, serialize=False)),
                ("IsVerified", models.BooleanField(db_column="IsVerified", default=False)),
                ("IsActive", models.BooleanField(db_column="IsActive", default=False)),
                ("VerifiedAt", models.DateTimeField(blank=True, db_column="VerifiedAt", null=True)),
                ("UnlinkedAt", models.DateTimeField(blank=True, db_column="UnlinkedAt", null=True)),
                ("CreatedAt", models.DateTimeField(auto_now_add=True, db_column="CreatedAt")),
                ("UpdatedAt", models.DateTimeField(auto_now=True, db_column="UpdatedAt")),
                (
                    "ApplicationID",
                    models.ForeignKey(
                        db_column="ApplicationId",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="GlobalIdentityAccounts",
                        to="access.applications",
                    ),
                ),
                (
                    "GlobalIdentityID",
                    models.ForeignKey(
                        db_column="GlobalIdentityId",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="Accounts",
                        to="access.globalidentities",
                    ),
                ),
                (
                    "UserID",
                    models.ForeignKey(
                        db_column="UserId",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="GlobalIdentityLinks",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"db_table": '"Auth"."GlobalIdentityAccounts"'},
        ),
        migrations.AddConstraint(
            model_name="globalidentityaccounts",
            constraint=models.UniqueConstraint(
                condition=models.Q(("IsActive", True)),
                fields=("UserID",),
                name="uq_global_identity_active_user",
            ),
        ),
        migrations.AddConstraint(
            model_name="globalidentityaccounts",
            constraint=models.UniqueConstraint(
                condition=models.Q(("IsActive", True)),
                fields=("GlobalIdentityID", "ApplicationID"),
                name="uq_global_identity_active_application",
            ),
        ),
        migrations.AddIndex(
            model_name="globalidentityaccounts",
            index=models.Index(fields=["UserID", "IsActive"], name="ix_global_identity_user_active"),
        ),
        migrations.AddIndex(
            model_name="globalidentityaccounts",
            index=models.Index(
                fields=["GlobalIdentityID", "ApplicationID", "IsActive"],
                name="ix_global_identity_app_active",
            ),
        ),
    ]
