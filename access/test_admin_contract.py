from django.test import SimpleTestCase
from rest_framework.permissions import IsAdminUser

from access import views


class IdentityAdministrationContractTests(SimpleTestCase):
    ADMIN_SURFACES = (
        views.IdentityUserViewSet,
        views.RoleViewSet,
        views.PermissionViewSet,
        views.RolePermissionViewSet,
        views.UserPermissionViewSet,
        views.ApplicationRoleViewSet,
        views.ApplicationPermissionViewSet,
        views.UserSessionViewSet,
        views.UserDeviceViewSet,
        views.AccessAuditEventViewSet,
    )

    def test_administration_surfaces_require_admin(self):
        for viewset in self.ADMIN_SURFACES:
            self.assertIn(IsAdminUser, viewset.permission_classes, viewset.__name__)

    def test_role_admin_supports_permission_replacement(self):
        self.assertTrue(hasattr(views.RoleViewSet, "set_permissions"))

    def test_user_admin_surface_is_crud_capable(self):
        self.assertTrue(issubclass(views.IdentityUserViewSet, views.AdminModelViewSet))

    def test_matrix_contains_roles_permissions_users_and_audit(self):
        names = {surface.__name__ for surface in self.ADMIN_SURFACES}
        self.assertTrue({
            "IdentityUserViewSet", "RoleViewSet", "PermissionViewSet",
            "RolePermissionViewSet", "UserPermissionViewSet", "AccessAuditEventViewSet",
        }.issubset(names))
