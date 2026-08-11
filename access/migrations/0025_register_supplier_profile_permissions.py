from django.db import migrations


PERMISSIONS = {
    "supplier.profile.view": "READ",
    "supplier.profile.manage": "MANAGE",
    "supplier.admin": "MANAGE",
}


def register_supplier_profile_permissions(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    ApplicationPermissions = apps.get_model("access", "ApplicationPermissions")
    Modules = apps.get_model("access", "Modules")
    Actions = apps.get_model("access", "Actions")
    Permissions = apps.get_model("access", "Permissions")

    module, _ = Modules.objects.update_or_create(
        Code="SUPPLIER_PROFILES",
        defaults={
            "Name": "Supplier Profiles",
            "Description": "Perfiles Supplier enlazados a Customer Party.",
            "Path": "/admin/business-discovery",
        },
    )
    registered = []
    for code, action_name in PERMISSIONS.items():
        action, _ = Actions.objects.update_or_create(
            Name=action_name,
            defaults={"Description": f"Accion {action_name}."},
        )
        permission, _ = Permissions.objects.update_or_create(
            Code=code,
            defaults={"ModuleID": module, "ActionID": action},
        )
        registered.append(permission)

    for application_code in ("JOBCRON", "REFAPART"):
        application = Applications.objects.get(Code=application_code)
        for permission in registered:
            ApplicationPermissions.objects.get_or_create(
                ApplicationID=application,
                PermissionID=permission,
            )


class Migration(migrations.Migration):
    dependencies = [("access", "0024_seed_active_commercial_permissions")]
    operations = [
        migrations.RunPython(register_supplier_profile_permissions, migrations.RunPython.noop),
    ]
