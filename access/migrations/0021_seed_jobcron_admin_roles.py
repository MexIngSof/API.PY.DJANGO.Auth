from django.contrib.auth.hashers import make_password
from django.db import migrations


TEMP_PASSWORD = "JobCron.Admin#2026"

APPLICATION = {
    "Code": "JOBCRON",
    "Name": "JobCron",
    "Description": "Centro administrativo global del ecosistema.",
    "IsActive": True,
}

MODULES = {
    "JOBCRON_ADMIN": "/admin",
    "JOBCRON_USERS": "/admin/usuarios",
    "JOBCRON_ROLES": "/admin/roles",
    "JOBCRON_PERMISSIONS": "/admin/permisos",
    "JOBCRON_FEATURES": "/admin/feature-availability",
    "JOBCRON_AUDIT": "/admin/auditoria",
}

PERMISSIONS = {
    "jobcron.overview.read": ("JOBCRON_ADMIN", "READ"),
    "jobcron.users.read": ("JOBCRON_USERS", "READ"),
    "jobcron.users.manage": ("JOBCRON_USERS", "MANAGE"),
    "jobcron.roles.read": ("JOBCRON_ROLES", "READ"),
    "jobcron.roles.manage": ("JOBCRON_ROLES", "MANAGE"),
    "jobcron.permissions.read": ("JOBCRON_PERMISSIONS", "READ"),
    "jobcron.permissions.manage": ("JOBCRON_PERMISSIONS", "MANAGE"),
    "jobcron.features.read": ("JOBCRON_FEATURES", "READ"),
    "jobcron.features.manage": ("JOBCRON_FEATURES", "MANAGE"),
    "jobcron.audit.read": ("JOBCRON_AUDIT", "READ"),
}

ROLE_PERMISSIONS = {
    "JOBCRON_SUPER_ADMIN": tuple(PERMISSIONS.keys()),
    "JOBCRON_PLATFORM_ADMIN": (
        "jobcron.overview.read",
        "jobcron.users.read",
        "jobcron.roles.read",
        "jobcron.permissions.read",
        "jobcron.features.read",
        "jobcron.features.manage",
        "jobcron.audit.read",
    ),
    "JOBCRON_SUPPORT_ADMIN": (
        "jobcron.overview.read",
        "jobcron.users.read",
        "jobcron.roles.read",
        "jobcron.permissions.read",
    ),
    "APPLICATION_ADMIN": (
        "jobcron.overview.read",
        "jobcron.users.read",
        "jobcron.roles.read",
        "jobcron.permissions.read",
    ),
}

ROLE_DESCRIPTIONS = {
    "JOBCRON_SUPER_ADMIN": "Control total de JobCron y gobierno global del ecosistema.",
    "JOBCRON_PLATFORM_ADMIN": "Administracion tecnica y operativa global limitada.",
    "JOBCRON_SUPPORT_ADMIN": "Soporte operativo con lectura de usuarios, roles y permisos.",
    "APPLICATION_ADMIN": "Administracion delegada de una aplicacion conectada.",
}

USERS = [
    (
        "superadmin@jobcron.local",
        "JOBCRON_SUPER_ADMIN",
        "JobCron",
        "Super Admin",
        True,
        True,
    ),
]


def seed_jobcron_admin_roles(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    ApplicationPermissions = apps.get_model("access", "ApplicationPermissions")
    ApplicationRoles = apps.get_model("access", "ApplicationRoles")
    Modules = apps.get_model("access", "Modules")
    Actions = apps.get_model("access", "Actions")
    Permissions = apps.get_model("access", "Permissions")
    RolePermissions = apps.get_model("access", "RolePermissions")
    PasswordHistory = apps.get_model("access", "PasswordHistory")
    Roles = apps.get_model("roles", "Roles")
    UserRoles = apps.get_model("roles", "UserRoles")
    UserAccount = apps.get_model("user", "UserAccount")

    application, _ = Applications.objects.update_or_create(
        Code=APPLICATION["Code"],
        defaults={
            "Name": APPLICATION["Name"],
            "Description": APPLICATION["Description"],
            "IsActive": APPLICATION["IsActive"],
        },
    )

    modules = {}
    for code, path in MODULES.items():
        module, _ = Modules.objects.update_or_create(
            Code=code,
            defaults={
                "Name": code.replace("_", " ").title(),
                "Description": f"Modulo JobCron {code}.",
                "Path": path,
            },
        )
        modules[code] = module

    actions = {}
    for _, action_name in PERMISSIONS.values():
        action, _ = Actions.objects.update_or_create(
            Name=action_name,
            defaults={"Description": f"Accion JobCron {action_name}."},
        )
        actions[action_name] = action

    permissions = {}
    for permission_code, (module_code, action_name) in PERMISSIONS.items():
        permission, _ = Permissions.objects.update_or_create(
            Code=permission_code,
            defaults={
                "ModuleID": modules[module_code],
                "ActionID": actions[action_name],
            },
        )
        permissions[permission_code] = permission
        ApplicationPermissions.objects.get_or_create(
            ApplicationID=application,
            PermissionID=permission,
        )

    roles = {}
    for role_name, permission_codes in ROLE_PERMISSIONS.items():
        role, _ = Roles.objects.update_or_create(
            Name=role_name,
            defaults={"Description": ROLE_DESCRIPTIONS[role_name]},
        )
        roles[role_name] = role
        ApplicationRoles.objects.get_or_create(ApplicationID=application, RoleID=role)
        for permission_code in permission_codes:
            RolePermissions.objects.get_or_create(
                RoleID=role,
                PermissionID=permissions[permission_code],
            )

    password_hash = make_password(TEMP_PASSWORD)
    for email, role_name, first_name, last_name, is_staff, is_superuser in USERS:
        user, created = UserAccount.objects.update_or_create(
            email=email,
            defaults={
                "password": password_hash,
                "first_name": first_name,
                "last_name": last_name,
                "is_active": True,
                "is_staff": is_staff,
                "is_superuser": is_superuser,
                "must_change_password": True,
                "idApp": application.ApplicationID,
            },
        )
        UserRoles.objects.get_or_create(UserID=user, RoleID=roles[role_name])
        if created:
            PasswordHistory.objects.create(UserID=user, PasswordHash=user.password)


class Migration(migrations.Migration):
    dependencies = [("access", "0020_seed_refapart_specialized_roles")]
    operations = [
        migrations.RunPython(seed_jobcron_admin_roles, migrations.RunPython.noop),
    ]
