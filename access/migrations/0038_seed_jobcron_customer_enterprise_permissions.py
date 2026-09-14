from django.db import migrations


APPLICATION_CODE = "JOBCRON"
MODULE_CODE = "CUSTOMER_ENTERPRISE_IDENTITY"
MODULE_PATH = "/api/v1/core/customer/v2"

PERMISSIONS = {
    "customer.read": "READ",
    "customer.view": "READ",
    "customer.create": "CREATE",
    "customer.write": "UPDATE",
    "customer.admin": "MANAGE",
}

# Enterprise identity administration can create/retire legal/customer
# relationships. Until a narrower Customer operator role is approved and
# runtime-certified, only the existing JobCron super-admin receives these
# permissions by default. Other applications are not broadened implicitly.
DEFAULT_ROLE_PERMISSIONS = {
    "JOBCRON_SUPER_ADMIN": tuple(PERMISSIONS.keys()),
}


def seed_jobcron_customer_enterprise_permissions(apps, schema_editor):
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
            "Name": "Customer Enterprise Identity",
            "Description": "Customer-owned enterprise identity read/write surface used by JobCron administration.",
            "Path": MODULE_PATH,
        },
    )

    permission_rows = {}
    for permission_code, action_name in PERMISSIONS.items():
        action, _ = Actions.objects.update_or_create(
            Name=action_name,
            defaults={"Description": f"Customer enterprise identity action: {action_name}."},
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


def unseed_jobcron_customer_enterprise_permissions(apps, schema_editor):
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

    Permissions.objects.filter(PermissionID__in=permission_ids).delete()


class Migration(migrations.Migration):
    dependencies = [("access", "0037_seed_jobcron_product_import_permissions")]

    operations = [
        migrations.RunPython(
            seed_jobcron_customer_enterprise_permissions,
            unseed_jobcron_customer_enterprise_permissions,
        )
    ]
