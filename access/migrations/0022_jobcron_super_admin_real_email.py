from django.contrib.auth.hashers import make_password
from django.db import migrations


REAL_EMAIL = "super.admin.jobcron@yopmail.com"
LEGACY_EMAIL = "superadmin@jobcron.local"
TEMP_PASSWORD = "JobCron.Temp#2026!"
ROLE_NAME = "JOBCRON_SUPER_ADMIN"


def update_jobcron_super_admin(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    PasswordHistory = apps.get_model("access", "PasswordHistory")
    Roles = apps.get_model("roles", "Roles")
    UserRoles = apps.get_model("roles", "UserRoles")
    UserAccount = apps.get_model("user", "UserAccount")

    application = Applications.objects.get(Code="JOBCRON")
    role = Roles.objects.get(Name=ROLE_NAME)
    password_hash = make_password(TEMP_PASSWORD)

    user = UserAccount.objects.filter(email=REAL_EMAIL).first()
    legacy_user = UserAccount.objects.filter(email=LEGACY_EMAIL).first()

    if user is None and legacy_user is not None:
        user = legacy_user
        user.email = REAL_EMAIL
    elif user is None:
        user = UserAccount(email=REAL_EMAIL)

    user.password = password_hash
    user.first_name = "Super"
    user.last_name = "Admin JobCron"
    user.is_active = True
    user.is_staff = True
    user.is_superuser = True
    user.must_change_password = True
    user.idApp = application.ApplicationID
    user.save()

    UserRoles.objects.get_or_create(UserID=user, RoleID=role)
    PasswordHistory.objects.create(UserID=user, PasswordHash=user.password)

    if legacy_user is not None and legacy_user.pk != user.pk:
        legacy_user.is_active = False
        legacy_user.save(update_fields=["is_active"])


class Migration(migrations.Migration):
    dependencies = [("access", "0021_seed_jobcron_admin_roles")]

    operations = [
        migrations.RunPython(update_jobcron_super_admin, migrations.RunPython.noop),
    ]
