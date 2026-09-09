from django.test import TestCase

from access.models import ApplicationPermissions, RolePermissions
from roles.models import Roles


REQUIRED_GOVERNANCE_PERMISSIONS = {
    "catalog.product.read",
    "catalog.product.create",
    "catalog.product.update",
    "catalog.product.delete",
    "catalog.product.review.submit",
    "catalog.product.review.approve",
    "catalog.product.review.request_changes",
    "catalog.product.review.reject",
    "catalog.product.publish",
    "catalog.product.unpublish",
    "catalog.product.activate",
    "catalog.product.deactivate",
    "catalog.product.hide",
    "catalog.product.show",
    "catalog.product.suspend",
    "catalog.product.discontinue",
    "catalog.product.archive",
    "catalog.product.restore",
    "catalog.product.view_history",
    "catalog.product.bulk",
}


class CatalogGovernancePermissionTests(TestCase):
    def test_catalog_manager_has_every_permission_required_by_gateway(self):
        role = Roles.objects.get(Name="JOBCRON_CATALOG_MANAGER")
        granted = set(
            RolePermissions.objects.filter(RoleID=role).values_list(
                "PermissionID__Code", flat=True
            )
        )
        self.assertTrue(REQUIRED_GOVERNANCE_PERMISSIONS.issubset(granted))

    def test_permissions_are_available_in_jobcron_application(self):
        granted = set(
            ApplicationPermissions.objects.filter(
                ApplicationID__Code="JOBCRON",
                PermissionID__Code__in=REQUIRED_GOVERNANCE_PERMISSIONS,
            ).values_list("PermissionID__Code", flat=True)
        )
        self.assertEqual(granted, REQUIRED_GOVERNANCE_PERMISSIONS)
