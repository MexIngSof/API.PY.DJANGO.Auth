from django.db import migrations


APPLICATION_CODE = "JOBCRON"
MODULE_CODE = "PRICING_ADMIN"
MODULE_PATH = "/admin/pricing"

PERMISSIONS = {
    "pricing.list.read": "READ",
    "pricing.list.write": "UPDATE",
    "pricing.rule.read": "READ",
    "pricing.rule.write": "UPDATE",
    "pricing.simulate": "EXECUTE",
    "pricing.publish": "MANAGE",
    "pricing.rollback": "MANAGE",
    "pricing.admin": "MANAGE",
}

ROLE_PERMISSIONS = {
    "JOBCRON_PRICING_VIEWER": (
        "pricing.list.read",
        "pricing.rule.read",
        "pricing.simulate",
    ),
    "JOBCRON_PRICING_MANAGER": (
        "pricing.list.read",
        "pricing.list.write",
        "pricing.rule.read",
        "pricing.rule.write",
        "pricing.simulate",
        "pricing.publish",
        "pricing.rollback",
    ),
    "JOBCRON_PLATFORM_ADMIN": (
        "pricing.list.read",
        "pricing.list.write",
        "pricing.rule.read",
        "pricing.rule.write",
        "pricing.simulate",
        "pricing.publish",
        "pricing.rollback",
    ),
    "JOBCRON_SUPER_ADMIN": tuple(PERMISSIONS.keys()),
}

ROLE_DESCRIPTIONS = {
    "JOBCRON_PRICING_VIEWER": "Consulta listas, reglas, simulaciones e historial de Pricing sin publicar cambios.",
    "JOBCRON_PRICING_MANAGER": "Administra listas y reglas, simula impacto, publica versiones y ejecuta rollback de Pricing.",
}


def seed_pricing_governance(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    ApplicationPermissions = apps.get_model("access", "ApplicationPermissions")
    ApplicationRoles = apps.get_model("access", "ApplicationRoles")
    Modules = apps.get_model("access", "Modules")
    Actions = apps.get_model("access", "Actions")
    Permissions = apps.get_model("access", "Permissions")
    RolePermissions = apps.get_model("access", "RolePermissions")
    Roles = apps.get_model("roles", "Roles")

    application = Applications.objects.get(Code=APPLICATION_CODE)
    module, _ = Modules.objects.update_or_create(
        Code=MODULE_CODE,
        defaults={
            "Name": "Pricing Admin",
            "Description": "Gobierno de listas, reglas, simulación, publicación y rollback de Pricing.",
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

    for role_name, permission_codes in ROLE_PERMISSIONS.items():
        role = Roles.objects.filter(Name=role_name).first()
        if role is None:
            role = Roles.objects.create(
                Name=role_name,
                Description=ROLE_DESCRIPTIONS.get(
                    role_name,
                    f"Rol JobCron con gobierno de Pricing.",
                ),
            )
        elif role_name in ROLE_DESCRIPTIONS and role.Description != ROLE_DESCRIPTIONS[role_name]:
            role.Description = ROLE_DESCRIPTIONS[role_name]
            role.save(update_fields=["Description"])
        ApplicationRoles.objects.get_or_create(ApplicationID=application, RoleID=role)
        for permission_code in permission_codes:
            RolePermissions.objects.get_or_create(
                RoleID=role,
                PermissionID=permission_rows[permission_code],
            )


class Migration(migrations.Migration):
    dependencies = [("access", "0031_complete_catalog_governance_permissions")]

    operations = [
        migrations.RunPython(seed_pricing_governance, migrations.RunPython.noop),
    ]
