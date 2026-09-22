from django.db import migrations


APPLICATION_CODE = "TECNOTELEC"
MODULE_CODE = "TECNOTELEC_ECONOMICS"
MODULE_PATH = "/admin/tecnotelec/economics"

PERMISSIONS = {
    "tecnotelec.economics.read": "READ",
    "tecnotelec.economics.cost.read": "READ",
    "tecnotelec.economics.returns.read": "READ",
    "tecnotelec.economics.allocations.read": "READ",
    "tecnotelec.economics.scenarios.read": "READ",
    "tecnotelec.economics.admin": "MANAGE",
}


def seed_tecnotelec_economic_permissions(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    ApplicationPermissions = apps.get_model("access", "ApplicationPermissions")
    Modules = apps.get_model("access", "Modules")
    Actions = apps.get_model("access", "Actions")
    Permissions = apps.get_model("access", "Permissions")

    application = Applications.objects.get(Code=APPLICATION_CODE)
    module, _ = Modules.objects.update_or_create(
        Code=MODULE_CODE,
        defaults={
            "Name": "Tecno Telec Economics",
            "Description": (
                "Permisos internos para analisis economico consultivo, "
                "costos, retornos, repartos y escenarios."
            ),
            "Path": MODULE_PATH,
        },
    )

    for permission_code, action_name in PERMISSIONS.items():
        action, _ = Actions.objects.update_or_create(
            Name=action_name,
            defaults={
                "Description": f"Accion Tecno Telec economics: {action_name}.",
            },
        )
        permission, _ = Permissions.objects.update_or_create(
            Code=permission_code,
            defaults={"ModuleID": module, "ActionID": action},
        )
        ApplicationPermissions.objects.get_or_create(
            ApplicationID=application,
            PermissionID=permission,
        )


def unseed_tecnotelec_economic_permissions(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    ApplicationPermissions = apps.get_model("access", "ApplicationPermissions")
    Permissions = apps.get_model("access", "Permissions")
    RolePermissions = apps.get_model("access", "RolePermissions")
    UserPermissions = apps.get_model("access", "UserPermissions")

    permission_rows = Permissions.objects.filter(Code__in=PERMISSIONS.keys())
    permission_ids = list(
        permission_rows.values_list("PermissionID", flat=True)
    )

    RolePermissions.objects.filter(
        PermissionID_id__in=permission_ids,
    ).delete()
    UserPermissions.objects.filter(
        PermissionID_id__in=permission_ids,
    ).delete()

    application = Applications.objects.filter(Code=APPLICATION_CODE).first()
    if application is not None:
        ApplicationPermissions.objects.filter(
            ApplicationID=application,
            PermissionID_id__in=permission_ids,
        ).delete()

    Permissions.objects.filter(PermissionID__in=permission_ids).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("access", "0038_seed_jobcron_customer_enterprise_permissions"),
    ]

    operations = [
        migrations.RunPython(
            seed_tecnotelec_economic_permissions,
            unseed_tecnotelec_economic_permissions,
        )
    ]
