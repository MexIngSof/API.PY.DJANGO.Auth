from django.test import TestCase

from access.models import ApplicationPermissions, Applications, Permissions, RolePermissions
from roles.models import Roles


EXPECTED_PERMISSIONS = {
    "customer.read",
    "customer.view",
    "customer.create",
    "customer.write",
    "customer.admin",
}


class CustomerEnterprisePermissionSeedTests(TestCase):
    def test_jobcron_exposes_customer_enterprise_permissions(self):
        application = Applications.objects.get(Code="JOBCRON")
        assigned = set(
            ApplicationPermissions.objects.filter(ApplicationID=application).values_list(
                "PermissionID__Code", flat=True
            )
        )
        self.assertTrue(EXPECTED_PERMISSIONS.issubset(assigned))

    def test_only_jobcron_super_admin_receives_default_customer_enterprise_grant(self):
        super_admin = Roles.objects.get(Name="JOBCRON_SUPER_ADMIN")
        assigned = set(
            RolePermissions.objects.filter(RoleID=super_admin).values_list(
                "PermissionID__Code", flat=True
            )
        )
        self.assertTrue(EXPECTED_PERMISSIONS.issubset(assigned))

        other_roles = set(
            RolePermissions.objects.filter(PermissionID__Code__in=EXPECTED_PERMISSIONS)
            .exclude(RoleID=super_admin)
            .values_list("RoleID__Name", flat=True)
        )
        self.assertEqual(other_roles, set())

    def test_permissions_are_owned_by_customer_enterprise_identity_module(self):
        rows = Permissions.objects.filter(Code__in=EXPECTED_PERMISSIONS)
        self.assertEqual(rows.count(), len(EXPECTED_PERMISSIONS))
        self.assertEqual(
            set(rows.values_list("ModuleID__Code", flat=True)),
            {"CUSTOMER_ENTERPRISE_IDENTITY"},
        )
        self.assertEqual(
            set(rows.values_list("ModuleID__Path", flat=True)),
            {"/api/v1/core/customer/v2"},
        )

    def test_customer_facing_application_roles_do_not_gain_enterprise_admin_by_default(self):
        protected_roles = {
            "REFAPART_ADMIN",
            "REFAPART_CUSTOMER",
            "CUSTOMER",
            "JOBCRON_SUPPORT_ADMIN",
            "JOBCRON_PLATFORM_ADMIN",
        }
        granted = set(
            RolePermissions.objects.filter(
                PermissionID__Code__in=EXPECTED_PERMISSIONS,
                RoleID__Name__in=protected_roles,
            ).values_list("RoleID__Name", flat=True)
        )
        self.assertEqual(granted, set())
