from django.db import migrations


APPLICATION_CODE = "JOBCRON"
MODULE_CODE = "CATALOG_REVIEW_ADMIN"

PERMISSIONS = {
    "catalog.product.read": "READ",
    "catalog.product.create": "CREATE",
    "catalog.product.update": "UPDATE",
    "catalog.product.delete": "DELETE",
    "catalog.product.review.submit": "UPDATE",
    "catalog.product.review.approve": "MANAGE",
    "catalog.product.review.request_changes": "MANAGE",
    "catalog.product.review.reject": "MANAGE",
    "catalog.product.publish": "MANAGE",
    "catalog.product.unpublish": "MANAGE",
    "catalog.product.activate": "MANAGE",
    "catalog.product.deactivate": "MANAGE",
    "catalog.product.hide": "MANAGE",
    "catalog.product.show": "MANAGE",
    "catalog.product.suspend": "MANAGE",
    "catalog.product.discontinue": "MANAGE",
    "catalog.product.archive": "MANAGE",
    "catalog.product.restore": "MANAGE",
    "catalog.product.view_history": "READ",
    "catalog.product.bulk": "MANAGE",
}

MANAGER_ROLES = ("JOBCRON_CATALOG_MANAGER", "JOBCRON_SUPER_ADMIN")


def grant_complete_catalog_governance(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    ApplicationPermissions = apps.get_model("access", "ApplicationPermissions")
    Modules = apps.get_model("access", "Modules")
    Actions = apps.get_model("access", "Actions")
    Permissions = apps.get_model("access", "Permissions")
    RolePermissions = apps.get_model("access", "RolePermissions")
    Roles = apps.get_model("roles", "Roles")

    application = Applications.objects.get(Code=APPLICATION_CODE)
    module = Modules.objects.get(Code=MODULE_CODE)

    permission_rows = {}
    for permission_code, action_name in PERMISSIONS.items():
        action, _ = Actions.objects.update_or_create(
            Name=action_name,
            defaults={"Description": f"Acción Catalog {action_name}."},
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

    for role in Roles.objects.filter(Name__in=MANAGER_ROLES):
        for permission in permission_rows.values():
            RolePermissions.objects.get_or_create(
                RoleID=role,
                PermissionID=permission,
            )


def revoke_added_catalog_governance(apps, schema_editor):
    Permissions = apps.get_model("access", "Permissions")
    RolePermissions = apps.get_model("access", "RolePermissions")
    ApplicationPermissions = apps.get_model("access", "ApplicationPermissions")

    added_codes = {
        "catalog.product.create",
        "catalog.product.update",
        "catalog.product.delete",
        "catalog.product.activate",
        "catalog.product.deactivate",
        "catalog.product.hide",
        "catalog.product.show",
        "catalog.product.suspend",
        "catalog.product.discontinue",
        "catalog.product.archive",
        "catalog.product.restore",
    }
    permission_ids = list(
        Permissions.objects.filter(Code__in=added_codes).values_list("PermissionID", flat=True)
    )
    RolePermissions.objects.filter(PermissionID_id__in=permission_ids).delete()
    ApplicationPermissions.objects.filter(
        PermissionID_id__in=permission_ids,
        ApplicationID__Code=APPLICATION_CODE,
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("access", "0030_seed_catalog_review_permissions")]

    operations = [
        migrations.RunPython(
            grant_complete_catalog_governance,
            revoke_added_catalog_governance,
        )
    ]
