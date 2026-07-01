from django.db import migrations


ROLE_PERMISSIONS = {
    "REFAPART_ADMIN": (
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
        "CanAuthorizeSuppliers",
        "CanManageProducts",
        "CanViewSearchLogs",
        "CanViewDemandDashboard",
        "CanManageOrders",
        "CanManageLogistics",
        "CanManagePayments",
        "CanClosePartRequest",
        "CanViewInternalCosts",
        "CanViewMargins",
    ),
    "REFAPART_QUOTER": (
        "CanViewPartRequests",
        "CanContactSuppliers",
        "CanRegisterSupplierResponse",
        "CanViewSupplierPrices",
        "CanGenerateQuote",
        "CanSendCustomerQuote",
        "CanViewSearchLogs",
        "CanViewDemandDashboard",
        "CanClosePartRequest",
    ),
    "REFAPART_SUPPLIER_MANAGER": (
        "CanContactSuppliers",
        "CanRegisterSupplierResponse",
        "CanViewSupplierPrices",
        "CanManageSuppliers",
        "CanAuthorizeSuppliers",
    ),
    "REFAPART_LOGISTICS": (
        "CanManageOrders",
        "CanManageLogistics",
    ),
    "REFAPART_FINANCE": (
        "CanViewSupplierPrices",
        "CanEditFinalPrice",
        "CanGenerateQuote",
        "CanConvertQuoteToOrder",
        "CanManageOrders",
        "CanManagePayments",
        "CanViewInternalCosts",
        "CanViewMargins",
    ),
    "REFAPART_SUPPORT": (
        "CanViewPartRequests",
        "CanSendCustomerQuote",
        "CanViewSearchLogs",
        "CanViewDemandDashboard",
        "CanManageOrders",
        "CanClosePartRequest",
    ),
}


ROLE_DESCRIPTIONS = {
    "REFAPART_ADMIN": "Administracion completa REFAPART.",
    "REFAPART_QUOTER": "Cotizador operativo REFAPART.",
    "REFAPART_SUPPLIER_MANAGER": "Gestion de proveedores REFAPART.",
    "REFAPART_LOGISTICS": "Logistica y seguimiento REFAPART.",
    "REFAPART_FINANCE": "Pagos, margenes y conciliacion REFAPART.",
    "REFAPART_SUPPORT": "Atencion y seguimiento de cliente REFAPART.",
}


def seed_refapart_specialized_roles(apps, schema_editor):
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
        defaults={
            "Name": "REFAPART Operations",
            "Description": "REFAPART commercial operations",
            "Path": "/admin/refapart",
        },
    )
    action, _ = Actions.objects.update_or_create(
        Name="Operate REFAPART",
        defaults={"Description": "Execute an authorized REFAPART operation"},
    )

    permissions_by_code = {}
    for permission_codes in ROLE_PERMISSIONS.values():
        for code in permission_codes:
            permission, _ = Permissions.objects.update_or_create(
                Code=code,
                defaults={"ModuleID": module, "ActionID": action},
            )
            permissions_by_code[code] = permission
            ApplicationPermissions.objects.get_or_create(
                ApplicationID=application,
                PermissionID=permission,
            )

    for role_name, permission_codes in ROLE_PERMISSIONS.items():
        role, _ = Roles.objects.update_or_create(
            Name=role_name,
            defaults={"Description": ROLE_DESCRIPTIONS[role_name]},
        )
        ApplicationRoles.objects.get_or_create(ApplicationID=application, RoleID=role)
        for code in permission_codes:
            RolePermissions.objects.get_or_create(
                RoleID=role,
                PermissionID=permissions_by_code[code],
            )


class Migration(migrations.Migration):
    dependencies = [("access", "0019_emaildeliverylogs_diagnostics")]
    operations = [
        migrations.RunPython(seed_refapart_specialized_roles, migrations.RunPython.noop),
    ]
