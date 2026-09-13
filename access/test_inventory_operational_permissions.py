from django.test import TestCase

from access.models import ApplicationPermissions, Applications, Permissions, RolePermissions
from roles.models import Roles


EXPECTED_PERMISSIONS = {
    "inventory.stock.read",
    "inventory.reservations.read",
    "inventory.reservations.create",
    "inventory.reservations.manage",
}


class InventoryOperationalPermissionSeedTests(TestCase):
    def test_jobcron_exposes_inventory_operational_permissions(self):
        application = Applications.objects.get(Code="JOBCRON")
        assigned = set(
            ApplicationPermissions.objects.filter(ApplicationID=application).values_list(
                "PermissionID__Code", flat=True
            )
        )
        self.assertTrue(EXPECTED_PERMISSIONS.issubset(assigned))

    def test_active_customer_facing_apps_do_not_receive_operational_inventory_permissions(self):
        for application_code in ("TECNOTELEC", "REFAPART", "MEXINGSOF"):
            application = Applications.objects.filter(Code=application_code).first()
            if application is None:
                continue
            assigned = set(
                ApplicationPermissions.objects.filter(ApplicationID=application).values_list(
                    "PermissionID__Code", flat=True
                )
            )
            self.assertTrue(EXPECTED_PERMISSIONS.isdisjoint(assigned))

    def test_only_super_admin_receives_default_inventory_operational_grant(self):
        super_admin = Roles.objects.get(Name="JOBCRON_SUPER_ADMIN")
        assigned = set(
            RolePermissions.objects.filter(RoleID=super_admin).values_list(
                "PermissionID__Code", flat=True
            )
        )
        self.assertTrue(EXPECTED_PERMISSIONS.issubset(assigned))

        other_roles_with_inventory_permissions = set(
            RolePermissions.objects.filter(
                PermissionID__Code__in=EXPECTED_PERMISSIONS
            )
            .exclude(RoleID=super_admin)
            .values_list("RoleID__Name", flat=True)
        )
        self.assertEqual(other_roles_with_inventory_permissions, set())

    def test_permissions_are_owned_by_inventory_operations_module(self):
        rows = Permissions.objects.filter(Code__in=EXPECTED_PERMISSIONS)
        self.assertEqual(rows.count(), len(EXPECTED_PERMISSIONS))
        self.assertEqual(
            set(rows.values_list("ModuleID__Code", flat=True)),
            {"INVENTORY_OPERATIONS"},
        )
        self.assertEqual(
            set(rows.values_list("ModuleID__Path", flat=True)),
            {"/api/v1/core/inventory"},
        )
