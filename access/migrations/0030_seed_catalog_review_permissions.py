from django.db import migrations


APPLICATION_CODE = "JOBCRON"
MODULE_CODE = "CATALOG_REVIEW_ADMIN"
MODULE_PATH = "/admin/catalogo/productos"

PERMISSIONS = {
    "catalog.product.read": "READ",
    "catalog.product.review.submit": "UPDATE",
    "catalog.product.review.approve": "MANAGE",
    "catalog.product.review.request_changes": "MANAGE",
    "catalog.product.review.reject": "MANAGE",
    "catalog.product.publish": "MANAGE",
    "catalog.product.unpublish": "MANAGE",
    "catalog.product.view_history": "READ",
    "catalog.product.bulk": "MANAGE",
}

CATALOG_MANAGER_PERMISSIONS = tuple(PERMISSIONS.keys())
PLATFORM_ADMIN_PERMISSIONS = (
    "catalog.product.read",
    "catalog.product.view_history",
)


def seed_catalog_review_permissions(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    ApplicationPermissions = apps.get_model("access", "ApplicationPermissions")
    ApplicationRoles = apps.get_model("access", "ApplicationRoles")
    Modules = apps.get_model("access", "Modules")
    Actions = apps.get_model("access", "Actions")
    Permissions = apps.get_model("access", "Permissions")
    RolePermissions = apps.get_model("access", "RolePermissions")
    Roles = apps.get_model("roles", "Roles")

    application = Applications.objects.get(Code=APPLICATION_CODE)
    module, _ = Modules.objects.update_or_create(
        Code=MODULE_CODE,
        defaults={
            "Name": "Catalog Product Review",
            "Description": "Revisión, autorización y publicación central de productos Catalog.",
            "Path": MODULE_PATH,
        },
    )

    actions = {}
    for action_name in set(PERMISSIONS.values()):
        action, _ = Actions.objects.update_or_create(
            Name=action_name,
            defaults={"Description": f"Acción Catalog {action_name}."},
        )
        actions[action_name] = action

    permissions = {}
    for permission_code, action_name in PERMISSIONS.items():
        permission, _ = Permissions.objects.update_or_create(
            Code=permission_code,
            defaults={
                "ModuleID": module,
                "ActionID": actions[action_name],
            },
        )
        permissions[permission_code] = permission
        ApplicationPermissions.objects.get_or_create(
            ApplicationID=application,
            PermissionID=permission,
        )

    catalog_manager, _ = Roles.objects.update_or_create(
        Name="JOBCRON_CATALOG_MANAGER",
        defaults={
            "DisplayName": "Administrador de catálogo",
            "Description": "Revisa, autoriza y publica productos Catalog desde JobCron.",
        },
    )
    ApplicationRoles.objects.get_or_create(
        ApplicationID=application,
        RoleID=catalog_manager,
    )
    for permission_code in CATALOG_MANAGER_PERMISSIONS:
        RolePermissions.objects.get_or_create(
            RoleID=catalog_manager,
            PermissionID=permissions[permission_code],
        )

    super_admin = Roles.objects.filter(Name="JOBCRON_SUPER_ADMIN").first()
    if super_admin is not None:
        ApplicationRoles.objects.get_or_create(
            ApplicationID=application,
            RoleID=super_admin,
        )
        for permission_code in CATALOG_MANAGER_PERMISSIONS:
            RolePermissions.objects.get_or_create(
                RoleID=super_admin,
                PermissionID=permissions[permission_code],
            )

    platform_admin = Roles.objects.filter(Name="JOBCRON_PLATFORM_ADMIN").first()
    if platform_admin is not None:
        ApplicationRoles.objects.get_or_create(
            ApplicationID=application,
            RoleID=platform_admin,
        )
        for permission_code in PLATFORM_ADMIN_PERMISSIONS:
            RolePermissions.objects.get_or_create(
                RoleID=platform_admin,
                PermissionID=permissions[permission_code],
            )


def revoke_catalog_review_permissions(apps, schema_editor):
    ApplicationPermissions = apps.get_model("access", "ApplicationPermissions")
    ApplicationRoles = apps.get_model("access", "ApplicationRoles")
    Permissions = apps.get_model("access", "Permissions")
    RolePermissions = apps.get_model("access", "RolePermissions")
    Roles = apps.get_model("roles", "Roles")

    permission_ids = list(
        Permissions.objects.filter(Code__in=PERMISSIONS.keys()).values_list(
            "PermissionID", flat=True
        )
    )
    managed_roles = Roles.objects.filter(
        Name__in=[
            "JOBCRON_CATALOG_MANAGER",
            "JOBCRON_SUPER_ADMIN",
            "JOBCRON_PLATFORM_ADMIN",
        ]
    )
    RolePermissions.objects.filter(
        RoleID__in=managed_roles,
        PermissionID_id__in=permission_ids,
    ).delete()

    catalog_manager = managed_roles.filter(Name="JOBCRON_CATALOG_MANAGER").first()
    if catalog_manager is not None:
        ApplicationRoles.objects.filter(RoleID=catalog_manager).delete()
        catalog_manager.delete()

    ApplicationPermissions.objects.filter(
        PermissionID_id__in=permission_ids,
        ApplicationID__Code=APPLICATION_CODE,
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("access", "0029_refapart_supplier_manager_automotive_compatibility")]

    operations = [
        migrations.RunPython(
            seed_catalog_review_permissions,
            revoke_catalog_review_permissions,
        )
    ]
