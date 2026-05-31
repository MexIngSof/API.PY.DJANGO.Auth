from django.db import migrations


MODULES = {
    "DOCUMENTS": {
        "Name": "Documents",
        "Description": "LexNova document upload and classification center.",
        "Path": "/dashboard/modules/cases/upload",
    },
    "CLIENTS": {
        "Name": "Clients",
        "Description": "LexNova client invitations and progress visibility.",
        "Path": "/dashboard/modules/clients",
    },
}

PERMISSIONS = {
    "DOCUMENT_UPLOAD_OWN": "DOCUMENTS",
    "DOCUMENT_UPLOAD_FOR_CLIENT": "DOCUMENTS",
    "DOCUMENT_CLASSIFY": "DOCUMENTS",
    "DOCUMENT_RECLASSIFY": "DOCUMENTS",
    "DOCUMENT_LINK_TO_PROCEEDING": "DOCUMENTS",
    "DOCUMENT_VIEW_OWN": "DOCUMENTS",
    "DOCUMENT_VIEW_CLIENT": "DOCUMENTS",
    "DOCUMENT_DELETE_PENDING": "DOCUMENTS",
    "DOCUMENT_APPROVE": "DOCUMENTS",
    "CLIENT_INVITE": "CLIENTS",
    "CLIENT_VIEW_PROGRESS": "CLIENTS",
    "CLIENT_UPLOAD_DOCUMENTS": "DOCUMENTS",
}

ROLE_PERMISSIONS = {
    "CLIENT_RESTRICTED": [
        "DOCUMENT_UPLOAD_OWN",
        "DOCUMENT_VIEW_OWN",
        "CLIENT_VIEW_PROGRESS",
    ],
    "CLIENT_BASE": [
        "DOCUMENT_UPLOAD_OWN",
        "DOCUMENT_VIEW_OWN",
        "CLIENT_VIEW_PROGRESS",
        "CLIENT_UPLOAD_DOCUMENTS",
    ],
    "CLIENT_PLUS": [
        "DOCUMENT_UPLOAD_OWN",
        "DOCUMENT_VIEW_OWN",
        "CLIENT_VIEW_PROGRESS",
        "CLIENT_UPLOAD_DOCUMENTS",
    ],
    "ANALYST_BASE": [
        "DOCUMENT_VIEW_CLIENT",
        "DOCUMENT_CLASSIFY",
        "DOCUMENT_LINK_TO_PROCEEDING",
    ],
    "ANALYST_PLUS": [
        "DOCUMENT_VIEW_CLIENT",
        "DOCUMENT_CLASSIFY",
        "DOCUMENT_RECLASSIFY",
        "DOCUMENT_LINK_TO_PROCEEDING",
    ],
    "REVIEWER_BASE": [
        "DOCUMENT_VIEW_CLIENT",
        "DOCUMENT_APPROVE",
    ],
    "REVIEWER_PLUS": [
        "DOCUMENT_VIEW_CLIENT",
        "DOCUMENT_APPROVE",
        "DOCUMENT_RECLASSIFY",
    ],
    "MANAGER_BASE": [
        "DOCUMENT_UPLOAD_FOR_CLIENT",
        "DOCUMENT_VIEW_CLIENT",
        "DOCUMENT_CLASSIFY",
        "DOCUMENT_LINK_TO_PROCEEDING",
        "CLIENT_INVITE",
    ],
    "MANAGER_PLUS": [
        "DOCUMENT_UPLOAD_FOR_CLIENT",
        "DOCUMENT_VIEW_CLIENT",
        "DOCUMENT_CLASSIFY",
        "DOCUMENT_RECLASSIFY",
        "DOCUMENT_LINK_TO_PROCEEDING",
        "DOCUMENT_DELETE_PENDING",
        "CLIENT_INVITE",
    ],
    "ADMIN_BASE": list(PERMISSIONS.keys()),
    "ADMIN_ROOT": list(PERMISSIONS.keys()),
}


def action_name_for_permission(permission_code):
    if permission_code.startswith("DOCUMENT_"):
        return permission_code.removeprefix("DOCUMENT_")
    if permission_code.startswith("CLIENT_"):
        return permission_code.removeprefix("CLIENT_")
    return permission_code


def seed_lexnova_document_permissions(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    Modules = apps.get_model("access", "Modules")
    Actions = apps.get_model("access", "Actions")
    Permissions = apps.get_model("access", "Permissions")
    ApplicationPermissions = apps.get_model("access", "ApplicationPermissions")
    RolePermissions = apps.get_model("access", "RolePermissions")
    Roles = apps.get_model("roles", "Roles")

    application = Applications.objects.get(Code="LEXNOVA")

    modules = {}
    for code, defaults in MODULES.items():
        module, _ = Modules.objects.update_or_create(
            Code=code,
            defaults=defaults,
        )
        modules[code] = module

    permissions = {}
    for permission_code, module_code in PERMISSIONS.items():
        action_name = action_name_for_permission(permission_code)
        action, _ = Actions.objects.update_or_create(
            Name=action_name,
            defaults={"Description": f"LexNova document workflow action {action_name}."},
        )
        permission, _ = Permissions.objects.update_or_create(
            Code=permission_code,
            defaults={
                "ModuleID": modules[module_code],
                "ActionID": action,
            },
        )
        permissions[permission_code] = permission
        ApplicationPermissions.objects.update_or_create(
            ApplicationID=application,
            PermissionID=permission,
        )

    for role_name, permission_codes in ROLE_PERMISSIONS.items():
        try:
            role = Roles.objects.get(Name=role_name)
        except Roles.DoesNotExist:
            continue

        for permission_code in permission_codes:
            RolePermissions.objects.update_or_create(
                RoleID=role,
                PermissionID=permissions[permission_code],
            )


class Migration(migrations.Migration):

    dependencies = [
        ("access", "0014_seed_lexnova_auth"),
        ("roles", "0005_alter_userroles_id"),
    ]

    operations = [
        migrations.RunPython(
            seed_lexnova_document_permissions,
            migrations.RunPython.noop,
        ),
    ]
