from django.contrib.auth.hashers import make_password
from django.db import migrations


TEMP_PASSWORD = "LexNova.Temp#2026"

MODULES = {
    "HOME": "/dashboard/modules/home",
    "CASES": "/dashboard/modules/cases",
    "ANALYSIS": "/dashboard/modules/analysis",
    "RESULTS": "/dashboard/modules/results",
    "PROFILE": "/dashboard/modules/profile",
    "SETTINGS": "/dashboard/modules/settings",
    "ADMIN": "/dashboard/modules/admin",
    "ACCESS_CONTROL": "/dashboard/modules/admin/access-control",
    "AUDIT": "/dashboard/modules/admin/audit",
}

PERMISSIONS = [
    "HOME_VIEW",
    "HOME_VIEW_GLOBAL_STATS",
    "HOME_VIEW_TEAM_ACTIVITY",
    "CASE_VIEW_OWN",
    "CASE_VIEW_ASSIGNED",
    "CASE_VIEW_TEAM",
    "CASE_VIEW_ALL",
    "CASE_CREATE",
    "CASE_EDIT",
    "CASE_ASSIGN",
    "CASE_UPLOAD_FILES",
    "CASE_CHANGE_STATUS",
    "CASE_DELETE",
    "ANALYSIS_ACCESS",
    "ANALYSIS_RUN_AI",
    "ANALYSIS_EDIT_NOTES",
    "ANALYSIS_VIEW_LOGS",
    "ANALYSIS_SUBMIT_FOR_REVIEW",
    "ANALYSIS_APPROVE",
    "RESULT_VIEW",
    "RESULT_EDIT_DRAFT",
    "RESULT_PUBLISH",
    "RESULT_SHARE_WITH_CLIENT",
    "RESULT_DOWNLOAD_PDF",
    "PROFILE_VIEW_SELF",
    "PROFILE_EDIT_SELF",
    "PROFILE_VIEW_ROLES",
    "SETTINGS_ACCESS",
    "SETTINGS_EDIT_POLICIES",
    "SETTINGS_MANAGE_TEMPLATES",
    "SETTINGS_MANAGE_CATALOGS",
    "ADMIN_ACCESS",
    "ADMIN_MANAGE_USERS",
    "ADMIN_MANAGE_ROLES",
    "ADMIN_MANAGE_PERMISSIONS",
    "ADMIN_VIEW_AUDIT_LOGS",
    "ACCESS_CONTROL_VIEW",
    "ACCESS_CONTROL_EDIT_USER_PROFILE",
    "ACCESS_CONTROL_EDIT_ROLE_PERMISSIONS",
    "ACCESS_CONTROL_EDIT_USER_OVERRIDES",
    "AUDIT_VIEW_OWN",
    "AUDIT_VIEW_TEAM",
    "AUDIT_VIEW_ALL",
    "ALL_PERMISSIONS",
]

ROLE_PERMISSIONS = {
    "CLIENT_RESTRICTED": [
        "HOME_VIEW",
        "CASE_VIEW_OWN",
        "RESULT_VIEW",
        "PROFILE_VIEW_SELF",
    ],
    "CLIENT_BASE": [
        "HOME_VIEW",
        "CASE_VIEW_OWN",
        "RESULT_VIEW",
        "RESULT_DOWNLOAD_PDF",
        "PROFILE_VIEW_SELF",
        "PROFILE_EDIT_SELF",
    ],
    "CLIENT_PLUS": [
        "HOME_VIEW",
        "CASE_VIEW_OWN",
        "CASE_UPLOAD_FILES",
        "RESULT_VIEW",
        "RESULT_DOWNLOAD_PDF",
        "PROFILE_VIEW_SELF",
        "PROFILE_EDIT_SELF",
        "PROFILE_VIEW_ROLES",
    ],
    "ANALYST_RESTRICTED": [
        "HOME_VIEW",
        "CASE_VIEW_ASSIGNED",
        "ANALYSIS_ACCESS",
        "RESULT_VIEW",
        "PROFILE_VIEW_SELF",
    ],
    "ANALYST_BASE": [
        "HOME_VIEW",
        "CASE_VIEW_ASSIGNED",
        "CASE_UPLOAD_FILES",
        "ANALYSIS_ACCESS",
        "ANALYSIS_RUN_AI",
        "ANALYSIS_EDIT_NOTES",
        "ANALYSIS_SUBMIT_FOR_REVIEW",
        "RESULT_VIEW",
        "PROFILE_VIEW_SELF",
        "PROFILE_EDIT_SELF",
    ],
    "ANALYST_PLUS": [
        "HOME_VIEW",
        "HOME_VIEW_TEAM_ACTIVITY",
        "CASE_VIEW_ASSIGNED",
        "CASE_UPLOAD_FILES",
        "CASE_EDIT",
        "ANALYSIS_ACCESS",
        "ANALYSIS_RUN_AI",
        "ANALYSIS_EDIT_NOTES",
        "ANALYSIS_VIEW_LOGS",
        "ANALYSIS_SUBMIT_FOR_REVIEW",
        "RESULT_VIEW",
        "RESULT_EDIT_DRAFT",
        "PROFILE_VIEW_SELF",
        "PROFILE_EDIT_SELF",
        "PROFILE_VIEW_ROLES",
    ],
    "REVIEWER_RESTRICTED": [
        "HOME_VIEW",
        "CASE_VIEW_ASSIGNED",
        "ANALYSIS_ACCESS",
        "RESULT_VIEW",
        "PROFILE_VIEW_SELF",
    ],
    "REVIEWER_BASE": [
        "HOME_VIEW",
        "CASE_VIEW_ASSIGNED",
        "CASE_VIEW_TEAM",
        "ANALYSIS_ACCESS",
        "ANALYSIS_EDIT_NOTES",
        "ANALYSIS_VIEW_LOGS",
        "ANALYSIS_APPROVE",
        "RESULT_VIEW",
        "RESULT_EDIT_DRAFT",
        "PROFILE_VIEW_SELF",
        "PROFILE_EDIT_SELF",
    ],
    "REVIEWER_PLUS": [
        "HOME_VIEW",
        "HOME_VIEW_TEAM_ACTIVITY",
        "CASE_VIEW_TEAM",
        "CASE_CHANGE_STATUS",
        "ANALYSIS_ACCESS",
        "ANALYSIS_EDIT_NOTES",
        "ANALYSIS_VIEW_LOGS",
        "ANALYSIS_APPROVE",
        "RESULT_VIEW",
        "RESULT_EDIT_DRAFT",
        "RESULT_PUBLISH",
        "RESULT_SHARE_WITH_CLIENT",
        "PROFILE_VIEW_SELF",
        "PROFILE_EDIT_SELF",
        "PROFILE_VIEW_ROLES",
    ],
    "MANAGER_RESTRICTED": [
        "HOME_VIEW",
        "HOME_VIEW_TEAM_ACTIVITY",
        "CASE_VIEW_TEAM",
        "RESULT_VIEW",
        "PROFILE_VIEW_SELF",
    ],
    "MANAGER_BASE": [
        "HOME_VIEW",
        "HOME_VIEW_TEAM_ACTIVITY",
        "CASE_CREATE",
        "CASE_VIEW_TEAM",
        "CASE_ASSIGN",
        "CASE_CHANGE_STATUS",
        "ANALYSIS_VIEW_LOGS",
        "RESULT_VIEW",
        "RESULT_EDIT_DRAFT",
        "PROFILE_VIEW_SELF",
        "PROFILE_EDIT_SELF",
        "AUDIT_VIEW_TEAM",
    ],
    "MANAGER_PLUS": [
        "HOME_VIEW",
        "HOME_VIEW_GLOBAL_STATS",
        "HOME_VIEW_TEAM_ACTIVITY",
        "CASE_CREATE",
        "CASE_VIEW_TEAM",
        "CASE_VIEW_ALL",
        "CASE_ASSIGN",
        "CASE_CHANGE_STATUS",
        "ANALYSIS_VIEW_LOGS",
        "RESULT_VIEW",
        "RESULT_EDIT_DRAFT",
        "RESULT_PUBLISH",
        "RESULT_SHARE_WITH_CLIENT",
        "PROFILE_VIEW_SELF",
        "PROFILE_EDIT_SELF",
        "ACCESS_CONTROL_VIEW",
        "ACCESS_CONTROL_EDIT_USER_PROFILE",
        "AUDIT_VIEW_TEAM",
    ],
    "ADMIN_RESTRICTED": [
        "HOME_VIEW",
        "HOME_VIEW_GLOBAL_STATS",
        "CASE_VIEW_ALL",
        "RESULT_VIEW",
        "SETTINGS_ACCESS",
        "ADMIN_ACCESS",
        "ADMIN_VIEW_AUDIT_LOGS",
        "PROFILE_VIEW_SELF",
    ],
    "ADMIN_BASE": [
        "HOME_VIEW",
        "HOME_VIEW_GLOBAL_STATS",
        "HOME_VIEW_TEAM_ACTIVITY",
        "CASE_VIEW_ALL",
        "CASE_CREATE",
        "CASE_EDIT",
        "CASE_ASSIGN",
        "CASE_CHANGE_STATUS",
        "ANALYSIS_ACCESS",
        "ANALYSIS_VIEW_LOGS",
        "RESULT_VIEW",
        "RESULT_EDIT_DRAFT",
        "RESULT_PUBLISH",
        "RESULT_SHARE_WITH_CLIENT",
        "SETTINGS_ACCESS",
        "SETTINGS_MANAGE_TEMPLATES",
        "SETTINGS_MANAGE_CATALOGS",
        "ADMIN_ACCESS",
        "ADMIN_MANAGE_USERS",
        "ADMIN_MANAGE_ROLES",
        "ADMIN_VIEW_AUDIT_LOGS",
        "ACCESS_CONTROL_VIEW",
        "ACCESS_CONTROL_EDIT_USER_PROFILE",
        "AUDIT_VIEW_ALL",
        "PROFILE_VIEW_SELF",
        "PROFILE_EDIT_SELF",
    ],
}

ROLE_PERMISSIONS["ADMIN_ROOT"] = PERMISSIONS

USERS = [
    ("cliente.restricted@lexnova.local", "CLIENT_RESTRICTED", "Cliente", "Restricted"),
    ("cliente.base@lexnova.local", "CLIENT_BASE", "Cliente", "Base"),
    ("cliente.plus@lexnova.local", "CLIENT_PLUS", "Cliente", "Plus"),
    ("analyst.restricted@lexnova.local", "ANALYST_RESTRICTED", "Analyst", "Restricted"),
    ("analyst.base@lexnova.local", "ANALYST_BASE", "Analyst", "Base"),
    ("analyst.plus@lexnova.local", "ANALYST_PLUS", "Analyst", "Plus"),
    ("reviewer.restricted@lexnova.local", "REVIEWER_RESTRICTED", "Reviewer", "Restricted"),
    ("reviewer.base@lexnova.local", "REVIEWER_BASE", "Reviewer", "Base"),
    ("reviewer.plus@lexnova.local", "REVIEWER_PLUS", "Reviewer", "Plus"),
    ("manager.restricted@lexnova.local", "MANAGER_RESTRICTED", "Manager", "Restricted"),
    ("manager.base@lexnova.local", "MANAGER_BASE", "Manager", "Base"),
    ("manager.plus@lexnova.local", "MANAGER_PLUS", "Manager", "Plus"),
    ("admin.restricted@lexnova.local", "ADMIN_RESTRICTED", "Admin", "Restricted"),
    ("admin.base@lexnova.local", "ADMIN_BASE", "Admin", "Base"),
    ("admin.root@lexnova.local", "ADMIN_ROOT", "Admin", "Root"),
]


def module_code_for_permission(permission_code):
    if permission_code.startswith("CASE_"):
        return "CASES"
    if permission_code.startswith("RESULT_"):
        return "RESULTS"
    if permission_code.startswith("PROFILE_"):
        return "PROFILE"
    if permission_code.startswith("ACCESS_CONTROL_"):
        return "ACCESS_CONTROL"
    if permission_code.startswith("ALL_"):
        return "ADMIN"
    return permission_code.split("_", 1)[0]


def action_name_for_permission(permission_code):
    if permission_code == "ALL_PERMISSIONS":
        return "ALL"
    parts = permission_code.split("_")
    return parts[1] if len(parts) > 1 else permission_code


def seed_lexnova_auth(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    Modules = apps.get_model("access", "Modules")
    Actions = apps.get_model("access", "Actions")
    Permissions = apps.get_model("access", "Permissions")
    ApplicationRoles = apps.get_model("access", "ApplicationRoles")
    ApplicationPermissions = apps.get_model("access", "ApplicationPermissions")
    RolePermissions = apps.get_model("access", "RolePermissions")
    AccessAuditEvents = apps.get_model("access", "AccessAuditEvents")
    PasswordHistory = apps.get_model("access", "PasswordHistory")
    Roles = apps.get_model("roles", "Roles")
    UserRoles = apps.get_model("roles", "UserRoles")
    UserAccount = apps.get_model("user", "UserAccount")

    application, _ = Applications.objects.update_or_create(
        Code="LEXNOVA",
        defaults={
            "Name": "LexNova",
            "Description": "LegalTech product application.",
            "IsActive": True,
        },
    )

    modules = {}
    for code, path in MODULES.items():
        module, _ = Modules.objects.update_or_create(
            Code=code,
            defaults={
                "Name": code.replace("_", " ").title(),
                "Description": f"LexNova module {code}.",
                "Path": path,
            },
        )
        modules[code] = module

    actions = {}
    for permission_code in PERMISSIONS:
        action_name = action_name_for_permission(permission_code)
        action, _ = Actions.objects.update_or_create(
            Name=action_name,
            defaults={"Description": f"LexNova action {action_name}."},
        )
        actions[action_name] = action

    permissions = {}
    for permission_code in PERMISSIONS:
        module = modules[module_code_for_permission(permission_code)]
        action = actions[action_name_for_permission(permission_code)]
        permission, _ = Permissions.objects.update_or_create(
            Code=permission_code,
            defaults={
                "ModuleID": module,
                "ActionID": action,
            },
        )
        permissions[permission_code] = permission
        ApplicationPermissions.objects.update_or_create(
            ApplicationID=application,
            PermissionID=permission,
        )

    roles = {}
    for role_name in ROLE_PERMISSIONS:
        role, _ = Roles.objects.update_or_create(
            Name=role_name,
            defaults={"Description": f"LexNova profile level {role_name}."},
        )
        roles[role_name] = role
        ApplicationRoles.objects.update_or_create(
            ApplicationID=application,
            RoleID=role,
        )

        for permission_code in ROLE_PERMISSIONS[role_name]:
            RolePermissions.objects.update_or_create(
                RoleID=role,
                PermissionID=permissions[permission_code],
            )

    password_hash = make_password(TEMP_PASSWORD)
    for email, role_name, first_name, last_name in USERS:
        user, created = UserAccount.objects.update_or_create(
            email=email,
            defaults={
                "password": password_hash,
                "first_name": first_name,
                "last_name": last_name,
                "is_active": True,
                "is_staff": role_name.startswith("ADMIN_"),
                "is_superuser": role_name == "ADMIN_ROOT",
                "must_change_password": True,
                "idApp": application.ApplicationID,
            },
        )
        UserRoles.objects.update_or_create(
            UserID=user,
            RoleID=roles[role_name],
        )
        if created:
            PasswordHistory.objects.create(
                UserID=user,
                PasswordHash=user.password,
            )

    AccessAuditEvents.objects.create(
        ApplicationID=application,
        EventType="LEXNOVA_AUTH_SEED_APPLIED",
        Metadata={
            "users": len(USERS),
            "roles": len(ROLE_PERMISSIONS),
            "modules": len(MODULES),
            "permissions": len(PERMISSIONS),
            "must_change_password": True,
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ("access", "0013_remove_erp_admin_application"),
        ("roles", "0005_alter_userroles_id"),
        ("user", "0004_useraccount_must_change_password"),
    ]

    operations = [
        migrations.RunPython(seed_lexnova_auth, migrations.RunPython.noop),
    ]
