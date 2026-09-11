from django.db import migrations


APPLICATION_CODE = "JOBCRON"
MODULE_CODE = "PRICING_PROMOTIONS"
MODULE_PATH = "/admin/pricing/promociones"

PERMISSIONS = {
    "pricing.promotion.read": "READ",
    "pricing.promotion.write": "MANAGE",
    "pricing.admin": "MANAGE",
}

# Least-privilege default: only the global JobCron administrator receives the
# new permissions automatically. Other roles can be granted explicitly through
# Auth administration after product authorization.
DEFAULT_ROLE_PERMISSIONS = {
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
    module, _ = Modules.objects.update_or_create(
        Code=MODULE_CODE,
        defaults={
            "Name": "Pricing Promotions",
            "Description": "Administración de promociones comerciales de Pricing.",
            "Path": MODULE_PATH,
        },
    )

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

    for role_name, permission_codes in DEFAULT_ROLE_PERMISSIONS.items():
        role = Roles.objects.filter(Name=role_name).first()
        if role is None:
            continue
        for permission_code in permission_codes:
            RolePermissions.objects.get_or_create(
                RoleID=role,
                PermissionID=permission_rows[permission_code],
            )


def unseed_pricing_promotion_permissions(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    ApplicationPermissions = apps.get_model("access", "ApplicationPermissions")
    Permissions = apps.get_model("access", "Permissions")
    RolePermissions = apps.get_model("access", "RolePermissions")
    Roles = apps.get_model("roles", "Roles")

    permission_rows = Permissions.objects.filter(Code__in=PERMISSIONS.keys())
    permission_ids = list(permission_rows.values_list("PermissionID", flat=True))

    role_ids = list(
        Roles.objects.filter(Name__in=DEFAULT_ROLE_PERMISSIONS.keys()).values_list(
            "RoleID", flat=True
        )
    )
    RolePermissions.objects.filter(
        RoleID_id__in=role_ids,
        PermissionID_id__in=permission_ids,
    ).delete()

    application = Applications.objects.filter(Code=APPLICATION_CODE).first()
    if application is not None:
        ApplicationPermissions.objects.filter(
            ApplicationID=application,
            PermissionID_id__in=permission_ids,
        ).delete()


class Migration(migrations.Migration):
    dependencies = [("access", "0031_complete_catalog_governance_permissions")]

    operations = [
        migrations.RunPython(
            seed_pricing_promotion_permissions,
            unseed_pricing_promotion_permissions,
        )
    ]
