from django.db import migrations


APPLICATION_CODE = "LEXNOVA"
MODULE_CODE = "LEXNOVA_LEGAL"

PERMISSIONS = {
    "lexnova.cases.write": "WRITE",
    "lexnova.evidence.read": "READ",
    "lexnova.evidence.write": "WRITE",
    "lexnova.events.read": "READ",
    "lexnova.events.write": "WRITE",
    "lexnova.deadlines.read": "READ",
    "lexnova.authorities.read": "READ",
    "lexnova.authorities.write": "WRITE",
    "lexnova.participants.write": "WRITE",
}

READ_ONLY = {
    "lexnova.evidence.read",
    "lexnova.events.read",
    "lexnova.deadlines.read",
    "lexnova.authorities.read",
}

WRITE_LEGAL = set(PERMISSIONS)

ROLE_MATRIX = {
    "CLIENT_RESTRICTED": set(READ_ONLY),
    "CLIENT_BASE": set(READ_ONLY),
    "CLIENT_PLUS": set(READ_ONLY),
    "ANALYST_RESTRICTED": set(READ_ONLY),
    "ANALYST_BASE": {
        *READ_ONLY,
        "lexnova.evidence.write",
        "lexnova.events.write",
    },
    "ANALYST_PLUS": {
        *READ_ONLY,
        "lexnova.evidence.write",
        "lexnova.events.write",
    },
    "REVIEWER_RESTRICTED": set(READ_ONLY),
    "REVIEWER_BASE": {
        *READ_ONLY,
        "lexnova.evidence.write",
        "lexnova.events.write",
    },
    "REVIEWER_PLUS": {
        *READ_ONLY,
        "lexnova.evidence.write",
        "lexnova.events.write",
    },
    "MANAGER_RESTRICTED": set(READ_ONLY),
    "MANAGER_BASE": set(WRITE_LEGAL),
    "MANAGER_PLUS": set(WRITE_LEGAL),
    "ADMIN_RESTRICTED": {
        *READ_ONLY,
        "lexnova.evidence.write",
        "lexnova.events.write",
        "lexnova.participants.write",
    },
    "ADMIN_BASE": set(WRITE_LEGAL),
    "ADMIN_ROOT": set(WRITE_LEGAL),
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
        raise RuntimeError("LEXNOVA application must exist before extended legal permissions are seeded")

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
            defaults={"Description": f"LexNova extended legal action: {action_name}."},
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
    dependencies = [("access", "0034_seed_lexnova_case_resource_permissions")]

    operations = [migrations.RunPython(seed_permissions, unseed_permissions)]
