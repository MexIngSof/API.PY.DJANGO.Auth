from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from access.models import (
    Actions,
    ApplicationPermissions,
    ApplicationRoles,
    Applications,
    Modules,
    Permissions,
    RolePermissions,
)
from access.views import MePermissionsViewSet
from roles.models import Roles, UserRoles


class ApplicationScopedRbacTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = get_user_model().objects.create_user(
            email="rbac@example.com",
            password="test-password",
        )
        self.application = Applications.objects.create(
            Code="REFAPART",
            Name="RefaPart",
            IsActive=True,
        )
        self.other_application = Applications.objects.create(
            Code="JOBCRON",
            Name="JobCron",
            IsActive=True,
        )
        self.role = Roles.objects.create(Name="GLOBAL_ROLE")
        UserRoles.objects.create(UserID=self.user, RoleID=self.role)

        self.module = Modules.objects.create(Code="AUTH", Name="Auth")
        self.action = Actions.objects.create(Name="READ")
        self.permission = Permissions.objects.create(
            Code="AUTH.READ",
            Name="Read auth",
            ModuleID=self.module,
            ActionID=self.action,
        )
        RolePermissions.objects.create(RoleID=self.role, PermissionID=self.permission)

    def _request(self, application_code):
        request = self.factory.get(
            "/api/access/me/permissions/",
            HTTP_X_APPLICATION_CODE=application_code,
        )
        force_authenticate(request, user=self.user)
        return request

    def _response(self, application_code):
        view = MePermissionsViewSet.as_view({"get": "list_permissions"})
        return view(self._request(application_code))

    def test_missing_application_role_mapping_does_not_fallback_to_global_role(self):
        response = self._response("REFAPART")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["roles"], [])
        self.assertEqual(response.data["permissions"], [])

    def test_missing_application_permission_mapping_does_not_fallback_to_global_permission(self):
        ApplicationRoles.objects.create(
            ApplicationID=self.application,
            RoleID=self.role,
        )

        response = self._response("REFAPART")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["roles"]), 1)
        self.assertEqual(response.data["permissions"], [])

    def test_role_and_permission_are_returned_only_when_both_are_mapped_to_application(self):
        ApplicationRoles.objects.create(
            ApplicationID=self.application,
            RoleID=self.role,
        )
        ApplicationPermissions.objects.create(
            ApplicationID=self.application,
            PermissionID=self.permission,
        )

        response = self._response("REFAPART")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["roles"]), 1)
        self.assertEqual(
            response.data["permissions"],
            [{"code": "AUTH.READ", "allow": True}],
        )

    def test_mapping_in_other_application_does_not_authorize_current_application(self):
        ApplicationRoles.objects.create(
            ApplicationID=self.other_application,
            RoleID=self.role,
        )
        ApplicationPermissions.objects.create(
            ApplicationID=self.other_application,
            PermissionID=self.permission,
        )

        response = self._response("REFAPART")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["roles"], [])
        self.assertEqual(response.data["permissions"], [])
