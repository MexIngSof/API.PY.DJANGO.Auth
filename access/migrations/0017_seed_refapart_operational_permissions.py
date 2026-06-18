from django.db import migrations


PERMISSIONS = (
    "CanViewPartRequests",
    "CanAssignPartRequests",
    "CanContactSuppliers",
    "CanRegisterSupplierResponse",
    "CanViewSupplierPrices",
    "CanEditFinalPrice",
    "CanGenerateQuote",
    "CanSendCustomerQuote",
    "CanConvertQuoteToOrder",
    "CanManageSuppliers",
    "CanManageProducts",
    "CanViewSearchLogs",
    "CanViewDemandDashboard",
    "CanManageOrders",
    "CanManageLogistics",
    "CanClosePartRequest",
)


def seed_refapart_permissions(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    ApplicationPermissions = apps.get_model("access", "ApplicationPermissions")
    ApplicationRoles = apps.get_model("access", "ApplicationRoles")
    Modules = apps.get_model("access", "Modules")
    Actions = apps.get_model("access", "Actions")
    Permissions = apps.get_model("access", "Permissions")
    RolePermissions = apps.get_model("access", "RolePermissions")
    Roles = apps.get_model("roles", "Roles")

    application = Applications.objects.get(Code="REFAPART")
    module, _ = Modules.objects.update_or_create(
        Code="REFAPART_OPERATIONS",
        defaults={"Name": "REFAPART Operations", "Description": "REFAPART commercial operations", "Path": "/admin/refapart"},
    )
    action, _ = Actions.objects.update_or_create(
        Name="Operate REFAPART",
        defaults={"Description": "Execute an authorized REFAPART operation"},
    )
    admin_role, _ = Roles.objects.update_or_create(
        Name="REFAPART_ADMIN",
        defaults={"Description": "Full REFAPART operational administration."},
    )
    ApplicationRoles.objects.get_or_create(ApplicationID=application, RoleID=admin_role)

    for code in PERMISSIONS:
        permission, _ = Permissions.objects.update_or_create(
            Code=code,
            defaults={"ModuleID": module, "ActionID": action},
        )
        ApplicationPermissions.objects.get_or_create(ApplicationID=application, PermissionID=permission)
        RolePermissions.objects.get_or_create(RoleID=admin_role, PermissionID=permission)


class Migration(migrations.Migration):
    dependencies = [("access", "0016_seed_refapart_application")]
    operations = [migrations.RunPython(seed_refapart_permissions, migrations.RunPython.noop)]
