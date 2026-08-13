from django.db import migrations


PERMISSION_CODE = "automotive.product_compatibility.write"


def grant_supplier_manager_compatibility(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    ApplicationPermissions = apps.get_model("access", "ApplicationPermissions")
    Modules = apps.get_model("access", "Modules")
    Actions = apps.get_model("access", "Actions")
    Permissions = apps.get_model("access", "Permissions")
    RolePermissions = apps.get_model("access", "RolePermissions")
    Roles = apps.get_model("roles", "Roles")

    application = Applications.objects.get(Code="REFAPART")
    role = Roles.objects.get(Name="REFAPART_SUPPLIER_MANAGER")
    module, _ = Modules.objects.update_or_create(
        Code="AUTOMOTIVE_PRODUCT_COMPATIBILITY",
        defaults={
            "Name": "Automotive Product Compatibility",
            "Description": "Asociación entre productos Catalog y configuraciones Automotive.",
            "Path": "/admin/refapart/products",
        },
    )
    action, _ = Actions.objects.update_or_create(
        Name="MANAGE", defaults={"Description": "Administrar un recurso funcional."}
    )
    permission, _ = Permissions.objects.update_or_create(
        Code=PERMISSION_CODE,
        defaults={"ModuleID": module, "ActionID": action},
    )
    ApplicationPermissions.objects.get_or_create(
        ApplicationID=application, PermissionID=permission
    )
    RolePermissions.objects.get_or_create(RoleID=role, PermissionID=permission)


def revoke_supplier_manager_compatibility(apps, schema_editor):
    RolePermissions = apps.get_model("access", "RolePermissions")
    Roles = apps.get_model("roles", "Roles")
    role = Roles.objects.filter(Name="REFAPART_SUPPLIER_MANAGER").first()
    if role is not None:
        RolePermissions.objects.filter(
            RoleID=role, PermissionID__Code=PERMISSION_CODE
        ).delete()


class Migration(migrations.Migration):
    dependencies = [("access", "0028_refapart_supplier_manager_product_pricing")]
    operations = [
        migrations.RunPython(
            grant_supplier_manager_compatibility,
            revoke_supplier_manager_compatibility,
        )
    ]
