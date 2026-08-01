from types import SimpleNamespace
from unittest.mock import ANY, patch

from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from user.views import CustomTokenObtainPairView


class PasswordSetupLoginTests(SimpleTestCase):
    @patch("user.views.record_login_attempt")
    @patch("user.views.get_user_model")
    def test_pending_password_returns_specific_contract(
        self,
        get_user_model_mock,
        record_login_attempt_mock,
    ):
        user = SimpleNamespace(
            is_active=True,
            must_change_password=True,
            has_usable_password=lambda: False,
        )
        get_user_model_mock.return_value.objects.filter.return_value.first.return_value = user
        request = APIRequestFactory().post(
            "/api/auth/jwt/create/",
            {
                "email": "super.admin.jobcron@example.test",
                "password": "not-used",
                "ApplicationCode": "JOBCRON",
            },
            format="json",
        )

        response = CustomTokenObtainPairView.as_view()(request)

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["code"], "PASSWORD_SETUP_REQUIRED")
        record_login_attempt_mock.assert_called_once_with(
            ANY,
            "super.admin.jobcron@example.test",
            False,
            "password_setup_required",
            user=user,
        )

    @patch("user.views.record_login_attempt")
    @patch("user.views.get_user_model")
    @patch("rest_framework_simplejwt.views.TokenObtainPairView.post")
    def test_usable_password_keeps_standard_login_contract(
        self,
        standard_login_mock,
        get_user_model_mock,
        record_login_attempt_mock,
    ):
        user = SimpleNamespace(
            is_active=True,
            must_change_password=False,
            has_usable_password=lambda: True,
        )
        get_user_model_mock.return_value.objects.filter.return_value.first.return_value = user
        standard_login_mock.return_value = Response(
            {"detail": "Invalid credentials."},
            status=status.HTTP_401_UNAUTHORIZED,
        )
        request = APIRequestFactory().post(
            "/api/auth/jwt/create/",
            {
                "email": "user@example.test",
                "password": "wrong-password",
                "ApplicationCode": "REFAPART",
            },
            format="json",
        )

        response = CustomTokenObtainPairView.as_view()(request)

        self.assertEqual(response.status_code, 401)
        standard_login_mock.assert_called_once()
        record_login_attempt_mock.assert_called_once()
