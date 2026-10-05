from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from access.models import Applications


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
