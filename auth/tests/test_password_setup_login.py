from types import SimpleNamespace
from unittest.mock import ANY, patch

from django.test import SimpleTestCase, override_settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from user.scoped_views import ApplicationScopedTokenObtainPairView


@override_settings(GATEWAY_INTERNAL_SHARED_SECRET="test-context")
class PasswordSetupLoginTests(SimpleTestCase):
    def request(self, email, password="not-used", application_code="JOBCRON"):
        return APIRequestFactory().post(
            "/api/auth/jwt/create/",
            {"email": email, "password": password},
            format="json",
            HTTP_X_APPLICATION_CODE=application_code,
            HTTP_X_GATEWAY_INTERNAL_TOKEN="test-context",
        )

    @patch("user.scoped_views.record_login_attempt")
    @patch("user.scoped_views.find_local_account")
    @patch("user.scoped_views.resolve_application_context")
    def test_pending_password_returns_specific_contract(
        self,
        resolve_application_context_mock,
        find_local_account_mock,
        record_login_attempt_mock,
    ):
        application = SimpleNamespace(ApplicationID=3, Code="JOBCRON")
        user = SimpleNamespace(
            is_active=True,
            must_change_password=True,
            has_usable_password=lambda: False,
        )
        resolve_application_context_mock.return_value = application
        find_local_account_mock.return_value = user

        response = ApplicationScopedTokenObtainPairView.as_view()(
            self.request("super.admin.jobcron@example.test")
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["code"], "PASSWORD_SETUP_REQUIRED")
        find_local_account_mock.assert_called_once_with(
            application,
            "super.admin.jobcron@example.test",
        )
        record_login_attempt_mock.assert_called_once_with(
            ANY,
            "super.admin.jobcron@example.test",
            False,
            "password_setup_required",
            user=user,
        )

    @patch("user.scoped_views.record_login_attempt")
    @patch("user.scoped_views.find_local_account")
    @patch("user.scoped_views.resolve_application_context")
    @patch("rest_framework_simplejwt.views.TokenObtainPairView.post")
    def test_usable_password_keeps_scoped_login_contract(
        self,
        standard_login_mock,
        resolve_application_context_mock,
        find_local_account_mock,
        record_login_attempt_mock,
    ):
        application = SimpleNamespace(ApplicationID=1, Code="REFAPART")
        user = SimpleNamespace(
            is_active=True,
            must_change_password=False,
            has_usable_password=lambda: True,
        )
        resolve_application_context_mock.return_value = application
        find_local_account_mock.return_value = user
        standard_login_mock.return_value = Response(
            {"detail": "Invalid credentials."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

        response = ApplicationScopedTokenObtainPairView.as_view()(
            self.request("user@example.test", "wrong-password", "REFAPART")
        )

        self.assertEqual(response.status_code, 401)
        standard_login_mock.assert_called_once()
        record_login_attempt_mock.assert_called_once_with(
            ANY,
            "user@example.test",
            False,
            "invalid_credentials",
            user=user,
        )
