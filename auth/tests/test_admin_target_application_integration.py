from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient, APIRequestFactory, force_authenticate
from access.views import IdentityUserViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from access.models import Actions, ApplicationPermissions, Applications, Modules, Permissions, UserPermissions


@override_settings(GATEWAY_INTERNAL_SHARED_SECRET="admin-scope-test-secret")
class AdminTargetApplicationIntegrationTests(TestCase):
    def setUp(self):
        self.refapart, _ = Applications.objects.get_or_create(
            Code="REFAPART", defaults={"Name": "RefaPart", "IsActive": True}
        )
        self.jobcron, _ = Applications.objects.get_or_create(
            Code="JOBCRON", defaults={"Name": "JobCron", "IsActive": True}
        )
        User = get_user_model()
        self.delegated = User.objects.create_user(
            email="admin-target-delegated@example.com",
            password="test-password",
            idApp=self.refapart.ApplicationID,
            is_staff=True,
            is_active=True,
        )
        self.superadmin = User.objects.create_superuser(
            email="admin-target-superuser@example.com",
            password="test-password",
            idApp=self.refapart.ApplicationID,
        )

    def _client(self, user, *, application_code="REFAPART", gateway_secret="admin-scope-test-secret"):
        token = RefreshToken.for_user(user).access_token
        client = APIClient()
        client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}",
            HTTP_X_APPLICATION_CODE=application_code,
            HTTP_X_GATEWAY_INTERNAL_TOKEN=gateway_secret,
        )
        return client

    def test_normal_admin_cannot_target_another_application(self):
        response = self._client(self.delegated).get(
            "/api/access/identity/users/", {"application_code": "JOBCRON"}
        )
        self.assertEqual(response.status_code, 403, response.data)
        self.assertEqual(response.data["detail"].code, "ADMIN_APPLICATION_SCOPE_DENIED")

    def test_superadmin_can_target_another_application_through_real_endpoint(self):
        response = self._client(self.superadmin).get(
            "/api/access/identity/users/", {"application_code": "JOBCRON"}
        )
        self.assertEqual(response.status_code, 200)

    def test_invalid_admin_target_is_rejected(self):
        response = self._client(self.superadmin).get(
            "/api/access/identity/users/", {"application_code": "UNKNOWN"}
        )
        self.assertEqual(response.status_code, 404)

    def test_conflicting_application_id_still_fails_closed(self):
        response = self._client(self.superadmin).get(
            "/api/access/identity/users/",
            {"application_code": "JOBCRON", "ApplicationId": self.jobcron.ApplicationID},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["detail"].code, "APPLICATION_CONTEXT_MISMATCH")

    def test_missing_application_context_is_rejected(self):
        token = RefreshToken.for_user(self.superadmin).access_token
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = client.get(
            "/api/access/identity/users/", {"application_code": "JOBCRON"}
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["detail"].code, "APPLICATION_CODE_REQUIRED")

    def test_incorrect_gateway_context_is_rejected(self):
        response = self._client(
            self.superadmin, gateway_secret="wrong-secret"
        ).get("/api/access/identity/users/", {"application_code": "JOBCRON"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["detail"].code, "GATEWAY_CONTEXT_REQUIRED")

    def test_same_application_target_keeps_normal_behavior(self):
        response = self._client(self.delegated).get(
            "/api/access/identity/users/", {"application_code": "REFAPART"}
        )
        self.assertEqual(response.status_code, 200)

    def _register_permission_for_flag_test(self):
        module, _ = Modules.objects.get_or_create(
            Code="AUTH_SCOPED_FLAG_TEST",
            defaults={"Name": "Auth scoped flag test", "Path": "/test/rbac"},
        )
        action, _ = Actions.objects.get_or_create(Name="READ")
        permission, _ = Permissions.objects.get_or_create(
            Code="AUTH_SCOPED_FLAG_TEST.READ",
            defaults={"ModuleID": module, "ActionID": action},
        )
        ApplicationPermissions.objects.get_or_create(
            ApplicationID=self.refapart, PermissionID=permission,
        )
        return permission

    def test_explicit_false_permission_flag_is_persisted_as_denial(self):
        permission = self._register_permission_for_flag_test()
        response = self._client(self.delegated).post(
            f"/api/access/identity/users/{self.delegated.pk}/permissions/",
            {"permission_code": permission.Code, "allow": "false"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        row = UserPermissions.objects.get(UserID=self.delegated, PermissionID=permission)
        self.assertIs(row.Allow, False)

    def test_ambiguous_permission_flag_is_rejected_without_grant(self):
        permission = self._register_permission_for_flag_test()
        response = self._client(self.delegated).post(
            f"/api/access/identity/users/{self.delegated.pk}/permissions/",
            {"permission_code": permission.Code, "allow": "false-ish"},
            format="json",
        )
        self.assertEqual(response.status_code, 400, response.data)
        self.assertFalse(UserPermissions.objects.filter(
            UserID=self.delegated, PermissionID=permission,
        ).exists())

    def test_legacy_permission_admin_does_not_turn_false_into_grant(self):
        permission = self._register_permission_for_flag_test()
        request = APIRequestFactory().post(
            f"/api/access/identity/users/{self.delegated.pk}/permissions/",
            {"permission_code": permission.Code, "allow": "false"},
            format="json",
            HTTP_X_APPLICATION_CODE="REFAPART",
        )
        force_authenticate(request, user=self.delegated)
        response = IdentityUserViewSet.as_view({"post": "assign_permission"})(request, pk=self.delegated.pk)
        self.assertEqual(response.status_code, 200, response.data)
        row = UserPermissions.objects.get(UserID=self.delegated, PermissionID=permission)
        self.assertIs(row.Allow, False)
