from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from django.urls import resolve
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory

from user.views import CustomUserViewSet


class PasswordSetupResetTests(SimpleTestCase):
    def test_canonical_reset_route_uses_custom_viewset(self):
        match = resolve("/api/users/reset_password/")

        self.assertEqual(match.func.actions, {"post": "reset_password"})
        self.assertEqual(match.func.cls, CustomUserViewSet)

    @patch("user.views.record_access_event")
    @patch("user.views.djoser_settings")
    @patch("user.views.get_application")
    @patch("user.views.get_user_model")
    def test_unusable_password_receives_first_access_reset(
        self,
        get_user_model_mock,
        get_application_mock,
        djoser_settings_mock,
        record_access_event_mock,
    ):
        application = SimpleNamespace(ApplicationID=3)
        user = SimpleNamespace(
            email="super.admin.jobcron@example.test",
            idApp=3,
            is_active=True,
            must_change_password=True,
            has_usable_password=lambda: False,
        )
        get_application_mock.return_value = application
        get_user_model_mock.return_value.objects.filter.return_value.first.return_value = user
        message = Mock()
        djoser_settings_mock.EMAIL.password_reset.return_value = message
        request = APIRequestFactory().post(
            "/api/users/reset_password/",
            {
                "email": user.email,
                "ApplicationCode": "JOBCRON",
            },
            format="json",
            HTTP_X_APPLICATION_CODE="JOBCRON",
        )

        response = CustomUserViewSet.as_view({"post": "reset_password"})(request)

        self.assertEqual(response.status_code, 204)
        message.send.assert_called_once_with([user.email])
        record_access_event_mock.assert_called_once()

    @patch("djoser.views.UserViewSet.reset_password")
    @patch("user.views.get_application")
    @patch("user.views.get_user_model")
    def test_usable_password_keeps_standard_reset_contract(
        self,
        get_user_model_mock,
        get_application_mock,
        standard_reset_mock,
    ):
        application = SimpleNamespace(ApplicationID=1)
        user = SimpleNamespace(
            email="user@example.test",
            idApp=1,
            is_active=True,
            must_change_password=False,
            has_usable_password=lambda: True,
        )
        get_application_mock.return_value = application
        get_user_model_mock.return_value.objects.filter.return_value.first.return_value = user
        standard_reset_mock.return_value = Response(status=status.HTTP_204_NO_CONTENT)
        request = APIRequestFactory().post(
            "/api/users/reset_password/",
            {
                "email": user.email,
                "ApplicationCode": "REFAPART",
            },
            format="json",
            HTTP_X_APPLICATION_CODE="REFAPART",
        )

        response = CustomUserViewSet.as_view({"post": "reset_password"})(request)

        self.assertEqual(response.status_code, 204)
        standard_reset_mock.assert_called_once()
