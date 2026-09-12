from django.db import migrations


APPLICATION_CODE = "LEXNOVA"
MODULE_CODE = "LEXNOVA_LEGAL"

PERMISSIONS = {
    "lexnova.cases.read": "READ",
    "lexnova.cases.read-all": "READ_ALL",
    "lexnova.documents.read": "READ",
    "lexnova.documents.read-all": "READ_ALL",
    "lexnova.documents.write": "WRITE",
    "lexnova.participants.read": "READ",
    "lexnova.catalogs.read": "READ",
}

ROLE_MATRIX = {
    "CLIENT_RESTRICTED": {
        "lexnova.cases.read",
        "lexnova.documents.read",
        "lexnova.participants.read",
        "lexnova.catalogs.read",
    },
    "CLIENT_BASE": {
        "lexnova.cases.read",
        "lexnova.documents.read",
        "lexnova.participants.read",
        "lexnova.catalogs.read",
    },
    "CLIENT_PLUS": {
        "lexnova.cases.read",
        "lexnova.documents.read",
        "lexnova.documents.write",
        "lexnova.participants.read",
        "lexnova.catalogs.read",
    },
    "ANALYST_RESTRICTED": {
        "lexnova.cases.read",
        "lexnova.documents.read",
        "lexnova.participants.read",
        "lexnova.catalogs.read",
    },
    "ANALYST_BASE": {
        "lexnova.cases.read",
        "lexnova.documents.read",
        "lexnova.documents.write",
        "lexnova.participants.read",
        "lexnova.catalogs.read",
    },
    "ANALYST_PLUS": {
        "lexnova.cases.read",
        "lexnova.documents.read",
        "lexnova.documents.write",
        "lexnova.participants.read",
        "lexnova.catalogs.read",
    },
    "REVIEWER_RESTRICTED": {
        "lexnova.cases.read",
        "lexnova.documents.read",
        "lexnova.participants.read",
        "lexnova.catalogs.read",
    },
    "REVIEWER_BASE": {
        "lexnova.cases.read",
        "lexnova.documents.read",
        "lexnova.documents.write",
        "lexnova.participants.read",
        "lexnova.catalogs.read",
    },
    "REVIEWER_PLUS": {
        "lexnova.cases.read",
        "lexnova.documents.read",
        "lexnova.documents.write",
        "lexnova.participants.read",
        "lexnova.catalogs.read",
    },
    "MANAGER_RESTRICTED": {
        "lexnova.cases.read",
        "lexnova.documents.read",
        "lexnova.participants.read",
        "lexnova.catalogs.read",
    },
    "MANAGER_BASE": {
        "lexnova.cases.read",
        "lexnova.cases.read-all",
        "lexnova.documents.read",
        "lexnova.documents.read-all",
        "lexnova.documents.write",
        "lexnova.participants.read",
        "lexnova.catalogs.read",
    },
    "MANAGER_PLUS": set(PERMISSIONS),
    "ADMIN_RESTRICTED": {
        "lexnova.cases.read",
        "lexnova.cases.read-all",
        "lexnova.documents.read",
        "lexnova.documents.read-all",
        "lexnova.participants.read",
        "lexnova.catalogs.read",
    },
    "ADMIN_BASE": set(PERMISSIONS),
    "ADMIN_ROOT": set(PERMISSIONS),
}


def seed_permissions(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    ApplicationPermissions = apps.get_model("access", "ApplicationPermissions")
    Modules = apps.get_model("access", "Modules")
    Actions = apps.get_model("access", "Actions")
    Permissions = apps.get_model("access", "Permissions")
    RolePermissions = apps.get_model("access", "RolePermissions")
    Roles = apps.get_model("roles", "Roles")

    application = Applications.objects.filter(Code=APPLICATION_CODE, IsActive=True).first()
    if application is None:
        raise RuntimeError("LEXNOVA application must exist before case-resource permissions are seeded")

    module, _ = Modules.objects.update_or_create(
        Code=MODULE_CODE,
        defaults={
            "Name": "LexNova Legal",
            "Description": "Canonical legal-domain operations exposed by LexNova.",
            "Path": "/legal",
        },
    )

    rows = {}
    for code, action_name in PERMISSIONS.items():
        action, _ = Actions.objects.update_or_create(
            Name=action_name,
            defaults={"Description": f"LexNova case-resource action: {action_name}."},
        )
        permission, _ = Permissions.objects.update_or_create(
            Code=code,
            defaults={"ModuleID": module, "ActionID": action},
        )
        rows[code] = permission
        ApplicationPermissions.objects.get_or_create(
            ApplicationID=application,
            PermissionID=permission,
        )

    for role_name, codes in ROLE_MATRIX.items():
        role = Roles.objects.filter(Name=role_name).first()
        if role is None:
            continue
        for code in codes:
            RolePermissions.objects.get_or_create(RoleID=role, PermissionID=rows[code])


def unseed_permissions(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    ApplicationPermissions = apps.get_model("access", "ApplicationPermissions")
    Permissions = apps.get_model("access", "Permissions")
    RolePermissions = apps.get_model("access", "RolePermissions")

    permission_ids = list(
        Permissions.objects.filter(Code__in=PERMISSIONS).values_list("PermissionID", flat=True)
    )
    application_ids = list(
        Applications.objects.filter(Code=APPLICATION_CODE).values_list("ApplicationID", flat=True)
    )
    RolePermissions.objects.filter(PermissionID_id__in=permission_ids).delete()
    ApplicationPermissions.objects.filter(
        ApplicationID_id__in=application_ids,
        PermissionID_id__in=permission_ids,
    ).delete()
    Permissions.objects.filter(PermissionID__in=permission_ids).delete()


class Migration(migrations.Migration):
    dependencies = [("access", "0033_seed_lexnova_legal_permissions")]

    operations = [migrations.RunPython(seed_permissions, unseed_permissions)]
