from django.db import migrations


APPLICATION_PERMISSIONS = {
    "REFAPART": {
        "module": ("REFAPART_DOMAIN", "/api/refapart"),
        "permissions": {
            "refapart.requests.create": "CREATE",
            "refapart.requests.read_own": "READ",
            "refapart.orders.create": "CREATE",
            "refapart.orders.read_own": "READ",
            "refapart.quotes.manage": "MANAGE",
            "refapart.admin.access": "MANAGE",
            "refapart.audit.read": "READ",
        },
        "roles": {
            "REFAPART_ADMIN": "*",
            "REFAPART_CUSTOMER": (
                "refapart.requests.create",
                "refapart.requests.read_own",
                "refapart.orders.create",
                "refapart.orders.read_own",
                "refapart.quotes.manage",
            ),
            "REFAPART_QUOTER": ("refapart.requests.read_own", "refapart.quotes.manage"),
            "REFAPART_LOGISTICS": ("refapart.orders.read_own",),
            "REFAPART_FINANCE": ("refapart.orders.read_own", "refapart.quotes.manage"),
            "REFAPART_SUPPORT": ("refapart.requests.read_own", "refapart.orders.read_own"),
        },
    },
    "JOBCRON": {
        "module": ("LEADHUNTER_OPERATIONS", "/admin/prospectos"),
        "permissions": {
            "leadhunter.dashboard.read": "READ",
            "leadhunter.leads.read": "READ",
            "leadhunter.leads.create": "CREATE",
            "leadhunter.leads.update": "UPDATE",
            "leadhunter.leads.convert": "MANAGE",
            "leadhunter.rules.read": "READ",
            "leadhunter.apify.read": "READ",
            "leadhunter.apify.execute": "EXECUTE",
        },
        "roles": {
            "JOBCRON_SUPER_ADMIN": "*",
            "JOBCRON_PLATFORM_ADMIN": "*",
            "JOBCRON_PROSPECTING_OPERATOR": (
                "leadhunter.dashboard.read",
                "leadhunter.leads.read",
                "leadhunter.leads.create",
                "leadhunter.leads.update",
                "leadhunter.leads.convert",
                "leadhunter.rules.read",
                "leadhunter.apify.read",
            ),
        },
    },
}


def seed_active_commercial_permissions(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    ApplicationPermissions = apps.get_model("access", "ApplicationPermissions")
    ApplicationRoles = apps.get_model("access", "ApplicationRoles")
    Modules = apps.get_model("access", "Modules")
    Actions = apps.get_model("access", "Actions")
    Permissions = apps.get_model("access", "Permissions")
    RolePermissions = apps.get_model("access", "RolePermissions")
    Roles = apps.get_model("roles", "Roles")

    for application_code, contract in APPLICATION_PERMISSIONS.items():
        application = Applications.objects.get(Code=application_code)
        module_code, module_path = contract["module"]
        module, _ = Modules.objects.update_or_create(
            Code=module_code,
            defaults={
                "Name": module_code.replace("_", " ").title(),
                "Description": f"Operaciones autorizadas de {module_code}.",
                "Path": module_path,
            },
        )
        permissions = {}
        for permission_code, action_name in contract["permissions"].items():
            action, _ = Actions.objects.update_or_create(
                Name=action_name,
                defaults={"Description": f"Accion {action_name}."},
            )
            permission, _ = Permissions.objects.update_or_create(
                Code=permission_code,
                defaults={"ModuleID": module, "ActionID": action},
            )
            permissions[permission_code] = permission
            ApplicationPermissions.objects.get_or_create(
                ApplicationID=application,
                PermissionID=permission,
            )

        for role_name, permission_codes in contract["roles"].items():
            role, _ = Roles.objects.update_or_create(
                Name=role_name,
                defaults={"Description": f"Rol autorizado para {module_code}."},
            )
            ApplicationRoles.objects.get_or_create(ApplicationID=application, RoleID=role)
            selected_codes = permissions.keys() if permission_codes == "*" else permission_codes
            for permission_code in selected_codes:
                RolePermissions.objects.get_or_create(
                    RoleID=role,
                    PermissionID=permissions[permission_code],
                )


class Migration(migrations.Migration):
    dependencies = [("access", "0023_jobcron_super_master_idempotent_seed")]
    operations = [
        migrations.RunPython(seed_active_commercial_permissions, migrations.RunPython.noop),
    ]
