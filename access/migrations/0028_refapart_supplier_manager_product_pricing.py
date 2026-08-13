from django.db import migrations


WORKSPACE_PERMISSIONS = {
    "pricing.product_workspace.read": "READ",
    "pricing.product_workspace.write": "MANAGE",
}


def seed_supplier_manager_product_pricing(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    ApplicationPermissions = apps.get_model("access", "ApplicationPermissions")
    Modules = apps.get_model("access", "Modules")
    Actions = apps.get_model("access", "Actions")
    Permissions = apps.get_model("access", "Permissions")
    RolePermissions = apps.get_model("access", "RolePermissions")
    Roles = apps.get_model("roles", "Roles")

    application = Applications.objects.get(Code="REFAPART")
    role = Roles.objects.get(Name="REFAPART_SUPPLIER_MANAGER")
    product_permission = Permissions.objects.get(Code="CanManageProducts")
    ApplicationPermissions.objects.get_or_create(
        ApplicationID=application,
        PermissionID=product_permission,
    )
    RolePermissions.objects.get_or_create(
        RoleID=role,
        PermissionID=product_permission,
    )

    module, _ = Modules.objects.update_or_create(
        Code="REFAPART_PRODUCT_PRICING",
        defaults={
            "Name": "RefaPart Product Pricing",
            "Description": "Costo y sugerencia en el editor de productos RefaPart.",
            "Path": "/admin/refapart/products",
        },
    )
    for code, action_name in WORKSPACE_PERMISSIONS.items():
        action, _ = Actions.objects.update_or_create(
            Name=action_name,
            defaults={"Description": f"Accion {action_name}."},
        )
        permission, _ = Permissions.objects.update_or_create(
            Code=code,
            defaults={"ModuleID": module, "ActionID": action},
        )
        ApplicationPermissions.objects.get_or_create(
            ApplicationID=application,
            PermissionID=permission,
        )
        RolePermissions.objects.get_or_create(
            RoleID=role,
            PermissionID=permission,
        )


def remove_supplier_manager_product_pricing(apps, schema_editor):
    RolePermissions = apps.get_model("access", "RolePermissions")
    Roles = apps.get_model("roles", "Roles")
    role = Roles.objects.filter(Name="REFAPART_SUPPLIER_MANAGER").first()
    if role is not None:
        RolePermissions.objects.filter(
            RoleID=role,
            PermissionID__Code__in=(
                "CanManageProducts",
                "pricing.product_workspace.read",
                "pricing.product_workspace.write",
            ),
        ).delete()


class Migration(migrations.Migration):
    dependencies = [("access", "0027_seed_automotive_permissions")]
    operations = [
        migrations.RunPython(
            seed_supplier_manager_product_pricing,
            remove_supplier_manager_product_pricing,
        )
    ]