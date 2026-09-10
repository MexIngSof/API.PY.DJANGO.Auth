from django.test import TestCase

from access.models import ApplicationPermissions, RolePermissions
from roles.models import Roles


REQUIRED_PRICING_PERMISSIONS = {
    "pricing.list.read",
    "pricing.list.write",
    "pricing.rule.read",
    "pricing.rule.write",
    "pricing.simulate",
    "pricing.publish",
    "pricing.rollback",
    "pricing.admin",
}

MANAGER_PERMISSIONS = REQUIRED_PRICING_PERMISSIONS - {"pricing.admin"}
VIEWER_PERMISSIONS = {
    "pricing.list.read",
    "pricing.rule.read",
    "pricing.simulate",
}


class PricingGovernancePermissionTests(TestCase):
    def test_pricing_permissions_are_registered_for_jobcron(self):
        granted = set(
            ApplicationPermissions.objects.filter(
                ApplicationID__Code="JOBCRON",
                PermissionID__Code__in=REQUIRED_PRICING_PERMISSIONS,
            ).values_list("PermissionID__Code", flat=True)
        )
        self.assertEqual(granted, REQUIRED_PRICING_PERMISSIONS)

    def test_pricing_manager_has_operational_permissions_without_admin_bypass(self):
        role = Roles.objects.get(Name="JOBCRON_PRICING_MANAGER")
        granted = set(
            RolePermissions.objects.filter(RoleID=role).values_list(
                "PermissionID__Code", flat=True
            )
        )
        self.assertTrue(MANAGER_PERMISSIONS.issubset(granted))
        self.assertNotIn("pricing.admin", granted)

    def test_pricing_viewer_cannot_publish_or_rollback(self):
        role = Roles.objects.get(Name="JOBCRON_PRICING_VIEWER")
        granted = set(
            RolePermissions.objects.filter(RoleID=role).values_list(
                "PermissionID__Code", flat=True
            )
        )
        self.assertTrue(VIEWER_PERMISSIONS.issubset(granted))
        self.assertNotIn("pricing.publish", granted)
        self.assertNotIn("pricing.rollback", granted)
        self.assertNotIn("pricing.list.write", granted)
        self.assertNotIn("pricing.rule.write", granted)

    def test_super_admin_keeps_pricing_admin_bypass(self):
        role = Roles.objects.get(Name="JOBCRON_SUPER_ADMIN")
        granted = set(
            RolePermissions.objects.filter(RoleID=role).values_list(
                "PermissionID__Code", flat=True
            )
        )
        self.assertTrue(REQUIRED_PRICING_PERMISSIONS.issubset(granted))
