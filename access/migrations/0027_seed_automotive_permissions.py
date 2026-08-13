from django.db import migrations


def seed_automotive_permissions(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    ApplicationPermissions = apps.get_model("access", "ApplicationPermissions")
    Modules = apps.get_model("access", "Modules")
    Actions = apps.get_model("access", "Actions")
    Permissions = apps.get_model("access", "Permissions")
    RolePermissions = apps.get_model("access", "RolePermissions")
    Roles = apps.get_model("roles", "Roles")

    application = Applications.objects.get(Code="REFAPART")
    module, _ = Modules.objects.update_or_create(
        Code="AUTOMOTIVE_CATALOG",
        defaults={
            "Name": "Automotive Catalog",
            "Description": "Catalogos vehiculares y compatibilidad de productos.",
            "Path": "/admin/refapart/products",
        },
    )
    action, _ = Actions.objects.update_or_create(
        Name="MANAGE",
        defaults={"Description": "Administrar un recurso funcional."},
    )
    permission, _ = Permissions.objects.update_or_create(
        Code="automotive.manage",
        defaults={"ModuleID": module, "ActionID": action},
    )
    ApplicationPermissions.objects.get_or_create(
        ApplicationID=application,
        PermissionID=permission,
    )
    admin_role = Roles.objects.filter(Name="REFAPART_ADMIN").first()
    if admin_role is not None:
        RolePermissions.objects.get_or_create(RoleID=admin_role, PermissionID=permission)


class Migration(migrations.Migration):
    dependencies = [("access", "0026_business_discovery_canonical_identity")]
    operations = [migrations.RunPython(seed_automotive_permissions, migrations.RunPython.noop)]
