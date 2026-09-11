from django.test import TestCase

from access.models import ApplicationPermissions, Applications, Permissions, RolePermissions
from roles.models import Roles


class PricingPromotionPermissionSeedTests(TestCase):
    def test_jobcron_exposes_pricing_promotion_permissions(self):
        application = Applications.objects.get(Code="JOBCRON")
        expected = {
            "pricing.promotion.read",
            "pricing.promotion.write",
            "pricing.admin",
        }

        permission_ids = set(
            ApplicationPermissions.objects.filter(ApplicationID=application).values_list(
                "PermissionID__Code", flat=True
            )
        )
        self.assertTrue(expected.issubset(permission_ids))

    def test_super_admin_receives_pricing_promotion_permissions(self):
        role = Roles.objects.get(Name="JOBCRON_SUPER_ADMIN")
        assigned = set(
            RolePermissions.objects.filter(RoleID=role).values_list(
                "PermissionID__Code", flat=True
            )
        )
        self.assertTrue(
            {
                "pricing.promotion.read",
                "pricing.promotion.write",
                "pricing.admin",
            }.issubset(assigned)
        )

    def test_permissions_are_owned_by_pricing_promotions_module(self):
        rows = Permissions.objects.filter(
            Code__in=(
                "pricing.promotion.read",
                "pricing.promotion.write",
                "pricing.admin",
            )
        )
        self.assertEqual(rows.count(), 3)
        self.assertEqual(
            set(rows.values_list("ModuleID__Code", flat=True)),
            {"PRICING_PROMOTIONS"},
        )
