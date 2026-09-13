from django.db import migrations


APPLICATION_CODE = "JOBCRON"
MODULE_CODE = "INVENTORY_OPERATIONS"
MODULE_PATH = "/api/v1/core/inventory"

PERMISSIONS = {
    "inventory.stock.read": "READ",
    "inventory.reservations.read": "READ",
    "inventory.reservations.create": "CREATE",
    "inventory.reservations.manage": "MANAGE",
}

# Least privilege for the current consultative commercial scope. Inventory
# operational access is administered through JobCron; customer-facing apps use
# the public commercial availability projection and receive no reservation or
# physical-stock permission by default.
DEFAULT_ROLE_PERMISSIONS = {
    "JOBCRON_SUPER_ADMIN": tuple(PERMISSIONS.keys()),
}


def seed_inventory_operational_permissions(apps, schema_editor):
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
            "Name": "Inventory Operations",
            "Description": "Lectura de stock fisico y gestion autorizada de reservas Inventory.",
            "Path": MODULE_PATH,
        },
    )

    permission_rows = {}
    for permission_code, action_name in PERMISSIONS.items():
        action, _ = Actions.objects.update_or_create(
            Name=action_name,
            defaults={"Description": f"Accion Inventory {action_name}."},
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


def unseed_inventory_operational_permissions(apps, schema_editor):
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
    dependencies = [("access", "0035_seed_lexnova_extended_legal_permissions")]

    operations = [
        migrations.RunPython(
            seed_inventory_operational_permissions,
            unseed_inventory_operational_permissions,
        )
    ]
