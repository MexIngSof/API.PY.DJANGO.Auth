from django.db import migrations


MODULE_CODE = "COMMERCE_CHANNEL"
APPLICATION_CODES = ("JOBCRON", "REFAPART", "TECNOTELEC", "MEXINGSOF", "IMAGRAFITY")

PERMISSIONS = {
    "commercechannel.channels.read": "READ",
    "commercechannel.accounts.read": "READ",
    "commercechannel.accounts.manage": "MANAGE",
    "commercechannel.accounts.validate": "EXECUTE",
    "commercechannel.accounts.credentials.rotate": "MANAGE",
    "commercechannel.listings.read": "READ",
    "commercechannel.listings.create": "CREATE",
    "commercechannel.listings.update": "UPDATE",
    "commercechannel.listings.publish": "EXECUTE",
    "commercechannel.listings.pause": "EXECUTE",
    "commercechannel.listings.sync": "EXECUTE",
    "commercechannel.mappings.read": "READ",
    "commercechannel.mappings.manage": "MANAGE",
    "commercechannel.sync.read": "READ",
    "commercechannel.sync.run": "EXECUTE",
    "commercechannel.sync.retry": "EXECUTE",
    "commercechannel.webhooks.read": "READ",
    "commercechannel.webhooks.replay": "EXECUTE",
    "commercechannel.audit.read": "READ",
}

ROLE_MATRIX = {
    "CHANNEL_VIEWER": {
        "commercechannel.channels.read",
        "commercechannel.accounts.read",
        "commercechannel.listings.read",
        "commercechannel.mappings.read",
        "commercechannel.sync.read",
    },
    "CHANNEL_OPERATOR": {
        "commercechannel.channels.read",
        "commercechannel.accounts.read",
        "commercechannel.accounts.validate",
        "commercechannel.listings.read",
        "commercechannel.listings.create",
        "commercechannel.listings.update",
        "commercechannel.listings.publish",
        "commercechannel.listings.pause",
        "commercechannel.listings.sync",
        "commercechannel.mappings.read",
        "commercechannel.sync.read",
        "commercechannel.sync.run",
        "commercechannel.sync.retry",
        "commercechannel.webhooks.read",
    },
    "CHANNEL_MANAGER": {
        "commercechannel.channels.read",
        "commercechannel.accounts.read",
        "commercechannel.accounts.manage",
        "commercechannel.accounts.validate",
        "commercechannel.listings.read",
        "commercechannel.listings.create",
        "commercechannel.listings.update",
        "commercechannel.listings.publish",
        "commercechannel.listings.pause",
        "commercechannel.listings.sync",
        "commercechannel.mappings.read",
        "commercechannel.mappings.manage",
        "commercechannel.sync.read",
        "commercechannel.sync.run",
        "commercechannel.sync.retry",
        "commercechannel.webhooks.read",
        "commercechannel.webhooks.replay",
        "commercechannel.audit.read",
    },
    "CHANNEL_ADMIN": set(PERMISSIONS),
}


def seed_commerce_channel_permissions(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    ApplicationPermissions = apps.get_model("access", "ApplicationPermissions")
    ApplicationRoles = apps.get_model("access", "ApplicationRoles")
    Modules = apps.get_model("access", "Modules")
    Actions = apps.get_model("access", "Actions")
    Permissions = apps.get_model("access", "Permissions")
    RolePermissions = apps.get_model("access", "RolePermissions")
    Roles = apps.get_model("roles", "Roles")

    module, _ = Modules.objects.update_or_create(
        Code=MODULE_CODE,
        defaults={
            "Name": "Commerce Channel",
            "Description": "Reusable commerce-channel operations through Gateway.",
            "Path": "/commerce-channel",
        },
    )

    permission_rows = {}
    for code, action_name in PERMISSIONS.items():
        action, _ = Actions.objects.update_or_create(
            Name=action_name,
            defaults={"Description": f"CommerceChannel action: {action_name}."},
        )
        permission, _ = Permissions.objects.update_or_create(
            Code=code,
            defaults={"ModuleID": module, "ActionID": action},
        )
        permission_rows[code] = permission

    applications = list(
        Applications.objects.filter(Code__in=APPLICATION_CODES, IsActive=True)
    )
    for application in applications:
        for permission in permission_rows.values():
            ApplicationPermissions.objects.get_or_create(
                ApplicationID=application,
                PermissionID=permission,
            )

    for role_name, granted_codes in ROLE_MATRIX.items():
        role, _ = Roles.objects.update_or_create(
            Name=role_name,
            defaults={"Description": f"CommerceChannel role: {role_name}"},
        )
        for application in applications:
            ApplicationRoles.objects.get_or_create(
                ApplicationID=application,
                RoleID=role,
            )
        for code in granted_codes:
            RolePermissions.objects.get_or_create(
                RoleID=role,
                PermissionID=permission_rows[code],
            )


def unseed_commerce_channel_permissions(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    ApplicationPermissions = apps.get_model("access", "ApplicationPermissions")
    ApplicationRoles = apps.get_model("access", "ApplicationRoles")
    Permissions = apps.get_model("access", "Permissions")
    RolePermissions = apps.get_model("access", "RolePermissions")
    Roles = apps.get_model("roles", "Roles")

    permission_ids = list(
        Permissions.objects.filter(Code__in=PERMISSIONS).values_list("PermissionID", flat=True)
    )
    roles = Roles.objects.filter(Name__in=ROLE_MATRIX)
    application_ids = list(
        Applications.objects.filter(Code__in=APPLICATION_CODES).values_list("ApplicationID", flat=True)
    )

    RolePermissions.objects.filter(RoleID__in=roles, PermissionID_id__in=permission_ids).delete()
    ApplicationRoles.objects.filter(ApplicationID_id__in=application_ids, RoleID__in=roles).delete()
    ApplicationPermissions.objects.filter(
        ApplicationID_id__in=application_ids,
        PermissionID_id__in=permission_ids,
    ).delete()
    Permissions.objects.filter(PermissionID__in=permission_ids).delete()
    roles.delete()


class Migration(migrations.Migration):
    dependencies = [("access", "0031_complete_catalog_governance_permissions")]

    operations = [
        migrations.RunPython(
            seed_commerce_channel_permissions,
            unseed_commerce_channel_permissions,
        )
    ]
