from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from access.models import (
    Actions,
    ApplicationPermissions,
    ApplicationRolePermissions,
    ApplicationRoles,
    Applications,
    Modules,
    Permissions,
    RolePermissions,
    UserPermissions,
)
from access.scoped_rbac_views import ApplicationScopedMePermissionsViewSet
from roles.models import Roles, UserRoles


@override_settings(GATEWAY_INTERNAL_SHARED_SECRET="rbac-test-secret")
class ApplicationScopedRbacTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.application, _ = Applications.objects.get_or_create(
            Code="REFAPART", defaults={"Name": "RefaPart", "IsActive": True}
        )
        self.other_application, _ = Applications.objects.get_or_create(
            Code="JOBCRON", defaults={"Name": "JobCron", "IsActive": True}
        )
        self.user = get_user_model().objects.create_user(
            email="rbac@example.com",
            password="test-password",
            idApp=self.application.ApplicationID,
        )
        self.role = Roles.objects.create(Name="GLOBAL_ROLE")
        UserRoles.objects.create(UserID=self.user, RoleID=self.role)
        self.module = Modules.objects.create(Code="AUTH", Name="Auth")
        self.action, _ = Actions.objects.get_or_create(Name="READ")
        self.permission = Permissions.objects.create(
            Code="AUTH.READ",
            ModuleID=self.module,
            ActionID=self.action,
        )
        RolePermissions.objects.create(RoleID=self.role, PermissionID=self.permission)

    def _request(self, gateway_application_code, **query):
        request = self.factory.get(
            "/api/access/me/permissions/",
            data=query,
            HTTP_X_APPLICATION_CODE=gateway_application_code,
            HTTP_X_GATEWAY_INTERNAL_TOKEN="rbac-test-secret",
        )
        force_authenticate(request, user=self.user)
        return request

    def _response(self, gateway_application_code, **query):
        view = ApplicationScopedMePermissionsViewSet.as_view({"get": "list_permissions"})
        return view(self._request(gateway_application_code, **query))

    def test_missing_application_role_mapping_does_not_fallback_to_global_role(self):
        response = self._response("REFAPART")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["roles"], [])
        self.assertEqual(response.data["permissions"], [])

    def test_missing_application_permission_mapping_does_not_fallback_to_global_permission(self):
        ApplicationRoles.objects.create(ApplicationID=self.application, RoleID=self.role)
        response = self._response("REFAPART")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["roles"]), 1)
        self.assertEqual(response.data["permissions"], [])

    def test_role_and_permission_are_returned_only_when_both_are_mapped_to_application(self):
        ApplicationRoles.objects.create(ApplicationID=self.application, RoleID=self.role)
        ApplicationPermissions.objects.create(ApplicationID=self.application, PermissionID=self.permission)
        response = self._response("REFAPART")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["roles"]), 1)
        self.assertEqual(response.data["permissions"], [{"code": "AUTH.READ", "allow": True}])

    def test_application_role_permission_does_not_leak_to_another_application(self):
        RolePermissions.objects.filter(
            RoleID=self.role,
            PermissionID=self.permission,
        ).delete()
        ApplicationRoles.objects.create(ApplicationID=self.application, RoleID=self.role)
        ApplicationRoles.objects.create(ApplicationID=self.other_application, RoleID=self.role)
        ApplicationPermissions.objects.create(
            ApplicationID=self.application,
            PermissionID=self.permission,
        )
        ApplicationPermissions.objects.create(
            ApplicationID=self.other_application,
            PermissionID=self.permission,
        )
        ApplicationRolePermissions.objects.create(
            ApplicationID=self.application,
            RoleID=self.role,
            PermissionID=self.permission,
        )

        scoped_response = self._response("REFAPART")
        other_response = self._response("JOBCRON")

        self.assertEqual(scoped_response.data["permissions"], [{"code": "AUTH.READ", "allow": True}])
        self.assertEqual(other_response.data["permissions"], [])

    def test_direct_application_permission_is_effective_without_role_grant(self):
        direct_permission = Permissions.objects.create(
            Code="AUTH.DIRECT",
            ModuleID=self.module,
            ActionID=self.action,
        )
        ApplicationPermissions.objects.create(
            ApplicationID=self.application,
            PermissionID=direct_permission,
        )
        UserPermissions.objects.create(
            UserID=self.user,
            PermissionID=direct_permission,
            Allow=True,
            Reason="scoped direct grant",
        )

        response = self._response("REFAPART")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            {"code": "AUTH.DIRECT", "allow": True},
            response.data["permissions"],
        )

    def test_direct_application_denial_is_effective_without_role_grant(self):
        direct_permission = Permissions.objects.create(
            Code="AUTH.DIRECT",
            ModuleID=self.module,
            ActionID=self.action,
        )
        ApplicationPermissions.objects.create(
            ApplicationID=self.application,
            PermissionID=direct_permission,
        )
        UserPermissions.objects.create(
            UserID=self.user,
            PermissionID=direct_permission,
            Allow=False,
            Reason="scoped direct denial",
        )

        response = self._response("REFAPART")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            {"code": "AUTH.DIRECT", "allow": False},
            response.data["permissions"],
        )

    def test_mapping_in_other_application_does_not_authorize_current_application(self):
        ApplicationRoles.objects.create(ApplicationID=self.other_application, RoleID=self.role)
        ApplicationPermissions.objects.create(ApplicationID=self.other_application, PermissionID=self.permission)
        response = self._response("REFAPART")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["roles"], [])
        self.assertEqual(response.data["permissions"], [])

    def test_query_application_cannot_override_trusted_gateway_application(self):
        response = self._response("REFAPART", application_code="JOBCRON")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["detail"].code, "APPLICATION_CONTEXT_MISMATCH")

    def test_untrusted_gateway_context_is_rejected(self):
        request = self.factory.get(
            "/api/access/me/permissions/",
            HTTP_X_APPLICATION_CODE="REFAPART",
            HTTP_X_GATEWAY_INTERNAL_TOKEN="wrong-secret",
        )
        force_authenticate(request, user=self.user)
        view = ApplicationScopedMePermissionsViewSet.as_view({"get": "list_permissions"})
        response = view(request)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["detail"].code, "GATEWAY_CONTEXT_REQUIRED")
