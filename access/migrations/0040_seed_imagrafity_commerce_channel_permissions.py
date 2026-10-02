from django.db import migrations


APPLICATION_CODE = "IMAGRAFITY"
APPLICATION_NAME = "Imagrafity"
PERMISSION_PREFIX = "commercechannel."
ROLE_NAMES = ("CHANNEL_VIEWER", "CHANNEL_OPERATOR", "CHANNEL_MANAGER", "CHANNEL_ADMIN")


def seed_imagrafity_commerce_channel_permissions(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    ApplicationPermissions = apps.get_model("access", "ApplicationPermissions")
    ApplicationRoles = apps.get_model("access", "ApplicationRoles")
    Permissions = apps.get_model("access", "Permissions")
    Roles = apps.get_model("roles", "Roles")

    application, _ = Applications.objects.update_or_create(
        Code=APPLICATION_CODE,
        defaults={"Name": APPLICATION_NAME, "IsActive": True},
    )
    permissions = Permissions.objects.filter(Code__startswith=PERMISSION_PREFIX)
    for permission in permissions:
        ApplicationPermissions.objects.get_or_create(
            ApplicationID=application,
            PermissionID=permission,
        )
    for role in Roles.objects.filter(Name__in=ROLE_NAMES):
        ApplicationRoles.objects.get_or_create(ApplicationID=application, RoleID=role)


class Migration(migrations.Migration):
    dependencies = [("access", "0039_seed_tecnotelec_economic_permissions")]

    operations = [
        migrations.RunPython(
            seed_imagrafity_commerce_channel_permissions,
            migrations.RunPython.noop,
        )
    ]
