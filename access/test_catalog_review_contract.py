from django.test import TestCase

from access.models import ApplicationPermissions, ApplicationRoles, Permissions, RolePermissions
from roles.models import Roles


CATALOG_REVIEW_PERMISSIONS = {
    "catalog.product.read",
    "catalog.product.review.submit",
    "catalog.product.review.approve",
    "catalog.product.review.request_changes",
    "catalog.product.review.reject",
    "catalog.product.publish",
    "catalog.product.unpublish",
    "catalog.product.view_history",
    "catalog.product.bulk",
}


class CatalogReviewPermissionSeedTests(TestCase):
    def test_jobcron_catalog_manager_is_scoped_and_has_review_permissions(self):
        role = Roles.objects.get(Name="JOBCRON_CATALOG_MANAGER")
        self.assertTrue(
            ApplicationRoles.objects.filter(
                ApplicationID__Code="JOBCRON",
                RoleID=role,
            ).exists()
        )

        role_codes = set(
            RolePermissions.objects.filter(RoleID=role).values_list(
                "PermissionID__Code", flat=True
            )
        )
        self.assertTrue(CATALOG_REVIEW_PERMISSIONS.issubset(role_codes))

        app_codes = set(
            ApplicationPermissions.objects.filter(
                ApplicationID__Code="JOBCRON",
                PermissionID__Code__in=CATALOG_REVIEW_PERMISSIONS,
            ).values_list("PermissionID__Code", flat=True)
        )
        self.assertEqual(app_codes, CATALOG_REVIEW_PERMISSIONS)

    def test_permissions_are_canonical_catalog_codes(self):
        stored = set(
            Permissions.objects.filter(Code__in=CATALOG_REVIEW_PERMISSIONS).values_list(
                "Code", flat=True
            )
        )
        self.assertEqual(stored, CATALOG_REVIEW_PERMISSIONS)
        self.assertFalse(
            Permissions.objects.filter(Code__startswith="jobcron.catalog.product.").exists()
        )
