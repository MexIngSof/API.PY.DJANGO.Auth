from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory
from rest_framework_simplejwt.tokens import RefreshToken

from access.models import Applications
from user.mobile_session_views import CustomTokenRefreshView


@override_settings(GATEWAY_INTERNAL_SHARED_SECRET="test-gateway-secret")
class ApplicationScopedRefreshTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.refapart = Applications.objects.create(Code="REFAPART", Name="RefaPart", IsActive=True)
        self.jobcron = Applications.objects.create(Code="JOBCRON", Name="JobCron", IsActive=True)

    def _refresh(self, token, application_code):
        request = self.factory.post(
            "/api/auth/jwt/refresh/",
            {"refresh": str(token)},
            format="json",
            HTTP_X_APPLICATION_CODE=application_code,
            HTTP_X_GATEWAY_INTERNAL_TOKEN="test-gateway-secret",
        )
        view = CustomTokenRefreshView.as_view()
        with patch("user.mobile_session_views.tracked_refresh", return_value=None):
            return view(request)

    def test_refresh_for_same_application_is_allowed(self):
        refresh = RefreshToken()
        refresh["application_id"] = self.refapart.ApplicationID
        refresh["application_code"] = self.refapart.Code

        response = self._refresh(refresh, "REFAPART")

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)

    def test_refresh_for_different_application_is_rejected(self):
        refresh = RefreshToken()
        refresh["application_id"] = self.refapart.ApplicationID
        refresh["application_code"] = self.refapart.Code

        response = self._refresh(refresh, "JOBCRON")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["code"], "APPLICATION_ACCESS_DENIED")

    def test_refresh_without_application_claims_is_rejected(self):
        refresh = RefreshToken()

        response = self._refresh(refresh, "REFAPART")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["code"], "TOKEN_APPLICATION_REQUIRED")
