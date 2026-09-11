from django.db import migrations


APPLICATION_CODE = "JOBCRON"
MODULE_CODE = "PRICING_ADMIN"

PERMISSIONS = {
    "pricing.promotion.read": "READ",
    "pricing.promotion.write": "UPDATE",
}

ROLE_PERMISSIONS = {
    "JOBCRON_PRICING_VIEWER": ("pricing.promotion.read",),
    "JOBCRON_PRICING_MANAGER": (
        "pricing.promotion.read",
        "pricing.promotion.write",
    ),
    "JOBCRON_PLATFORM_ADMIN": (
        "pricing.promotion.read",
        "pricing.promotion.write",
    ),
    "JOBCRON_SUPER_ADMIN": tuple(PERMISSIONS.keys()),
}


def seed_pricing_promotion_permissions(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    ApplicationPermissions = apps.get_model("access", "ApplicationPermissions")
    Modules = apps.get_model("access", "Modules")
    Actions = apps.get_model("access", "Actions")
    Permissions = apps.get_model("access", "Permissions")
    RolePermissions = apps.get_model("access", "RolePermissions")
    Roles = apps.get_model("roles", "Roles")

    application = Applications.objects.get(Code=APPLICATION_CODE)
    module = Modules.objects.get(Code=MODULE_CODE)

    permission_rows = {}
    for permission_code, action_name in PERMISSIONS.items():
        action, _ = Actions.objects.update_or_create(
            Name=action_name,
            defaults={"Description": f"Acción Pricing {action_name}."},
        )
        permission, _ = Permissions.objects.update_or_create(
            Code=permission_code,
            defaults={"ModuleID": module, "ActionID": action},
        )
        ApplicationPermissions.objects.get_or_create(
            ApplicationID=application,
            PermissionID=permission,
        )
        permission_rows[permission_code] = permission

    for role_name, permission_codes in ROLE_PERMISSIONS.items():
        role = Roles.objects.filter(Name=role_name).first()
        if role is None:
            continue
        for permission_code in permission_codes:
            RolePermissions.objects.get_or_create(
                RoleID=role,
                PermissionID=permission_rows[permission_code],
            )


class Migration(migrations.Migration):
    dependencies = [("access", "0032_seed_pricing_governance_permissions")]

    operations = [
        migrations.RunPython(
            seed_pricing_promotion_permissions,
            migrations.RunPython.noop,
        ),
    ]
