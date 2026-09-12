from django.db import migrations


MODULE_CODE = "LEXNOVA_LEGAL"
APPLICATION_CODE = "LEXNOVA"

PERMISSIONS = {
    "lexnova.amparos.read": "READ",
    "lexnova.amparos.write": "WRITE",
    "lexnova.investigation-folders.read": "READ",
    "lexnova.investigation-folders.write": "WRITE",
}

ROLE_MATRIX = {
    "MANAGER_PLUS": {
        "lexnova.amparos.read",
        "lexnova.amparos.write",
        "lexnova.investigation-folders.read",
        "lexnova.investigation-folders.write",
    },
    "ADMIN_RESTRICTED": {
        "lexnova.amparos.read",
        "lexnova.investigation-folders.read",
    },
    "ADMIN_BASE": set(PERMISSIONS),
    "ADMIN_ROOT": set(PERMISSIONS),
}


def seed_lexnova_legal_permissions(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    ApplicationPermissions = apps.get_model("access", "ApplicationPermissions")
    Modules = apps.get_model("access", "Modules")
    Actions = apps.get_model("access", "Actions")
    Permissions = apps.get_model("access", "Permissions")
    RolePermissions = apps.get_model("access", "RolePermissions")
    Roles = apps.get_model("roles", "Roles")

    application = Applications.objects.filter(Code=APPLICATION_CODE, IsActive=True).first()
    if application is None:
        raise RuntimeError("LEXNOVA application must exist before legal permissions are seeded")

    module, _ = Modules.objects.update_or_create(
        Code=MODULE_CODE,
        defaults={
            "Name": "LexNova Legal",
            "Description": "Canonical legal-domain operations exposed by LexNova.",
            "Path": "/legal",
        },
    )

    permission_rows = {}
    for code, action_name in PERMISSIONS.items():
        action, _ = Actions.objects.update_or_create(
            Name=action_name,
            defaults={"Description": f"LexNova legal action: {action_name}."},
        )
        permission, _ = Permissions.objects.update_or_create(
            Code=code,
            defaults={"ModuleID": module, "ActionID": action},
        )
        permission_rows[code] = permission
        ApplicationPermissions.objects.get_or_create(
            ApplicationID=application,
            PermissionID=permission,
        )

    for role_name, permission_codes in ROLE_MATRIX.items():
        role = Roles.objects.filter(Name=role_name).first()
        if role is None:
            continue
        for code in permission_codes:
            RolePermissions.objects.get_or_create(
                RoleID=role,
                PermissionID=permission_rows[code],
            )


def unseed_lexnova_legal_permissions(apps, schema_editor):
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
    dependencies = [
        ("access", "0032_seed_commerce_channel_permissions"),
        ("access", "0032_seed_pricing_promotion_permissions"),
    ]

    operations = [
        migrations.RunPython(
            seed_lexnova_legal_permissions,
            unseed_lexnova_legal_permissions,
        )
    ]
