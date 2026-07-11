from django.contrib.auth.hashers import is_password_usable
from django.db import migrations


REAL_EMAIL = "super.admin.jobcron@yopmail.com"
LEGACY_EMAIL = "superadmin@jobcron.local"
ROLE_NAME = "JOBCRON_SUPER_ADMIN"


def ensure_jobcron_super_master_without_password_reset(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    Roles = apps.get_model("roles", "Roles")
    UserRoles = apps.get_model("roles", "UserRoles")
    UserAccount = apps.get_model("user", "UserAccount")

    application = Applications.objects.get(Code="JOBCRON")
    role = Roles.objects.get(Name=ROLE_NAME)

    user = UserAccount.objects.filter(email=REAL_EMAIL).first()
    legacy_user = UserAccount.objects.filter(email=LEGACY_EMAIL).first()

    if user is None and legacy_user is not None:
        user = legacy_user
        user.email = REAL_EMAIL
    elif user is None:
        user = UserAccount(
            email=REAL_EMAIL,
            first_name="Super",
            last_name="Master JobCron",
            is_active=True,
            is_staff=True,
            is_superuser=True,
            must_change_password=True,
            idApp=application.ApplicationID,
        )
        user.set_unusable_password()

    user.first_name = user.first_name or "Super"
    user.last_name = user.last_name or "Master JobCron"
    user.is_active = True
    user.is_staff = True
    user.is_superuser = True
    user.idApp = application.ApplicationID
    if not is_password_usable(user.password):
        user.must_change_password = True
    user.save()

    UserRoles.objects.get_or_create(UserID=user, RoleID=role)

    if legacy_user is not None and legacy_user.pk != user.pk:
        legacy_user.is_active = False
        legacy_user.save(update_fields=["is_active"])


class Migration(migrations.Migration):
    dependencies = [("access", "0022_jobcron_super_admin_real_email")]

    operations = [
        migrations.RunPython(
            ensure_jobcron_super_master_without_password_reset,
            migrations.RunPython.noop,
        ),
    ]
