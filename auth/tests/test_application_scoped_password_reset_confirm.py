from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from access.models import Applications
from user.models import UserAccount
from user.views import CustomUserViewSet


@override_settings(GATEWAY_INTERNAL_SHARED_SECRET="test-gateway-secret")
class ApplicationScopedPasswordResetConfirmTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.refapart, _ = Applications.objects.get_or_create(
            Code="REFAPART", defaults={"Name": "RefaPart", "IsActive": True}
        )
        self.jobcron, _ = Applications.objects.get_or_create(
            Code="JOBCRON", defaults={"Name": "JobCron", "IsActive": True}
        )
        self.user = UserAccount.objects.create_user(
            email="reset@example.com",
            password="old-password-123!",
            first_name="Reset",
            last_name="User",
            idApp=self.refapart.ApplicationID,
        )

    def _request(self, application_code):
        return Request(
            self.factory.post(
                "/api/auth/users/reset_password_confirm/",
                {"uid": "unused", "token": "unused", "new_password": "new-password-456!"},
                format="json",
                HTTP_X_APPLICATION_CODE=application_code,
                HTTP_X_GATEWAY_INTERNAL_TOKEN="test-gateway-secret",
            ),
            parsers=[JSONParser()],
        )

    def _view_with_valid_serializer(self, request):
        serializer = Mock()
        serializer.user = self.user
        serializer.data = {"new_password": "new-password-456!"}
        serializer.is_valid.return_value = None
        view = CustomUserViewSet()
        view.request = request
        view.action = "reset_password_confirm"
        view.get_serializer = Mock(return_value=serializer)
        return view

    @patch("user.views.djoser_settings")
    def test_reset_confirm_rejects_cross_application_before_password_mutation(self, djoser_settings):
        djoser_settings.PASSWORD_CHANGED_EMAIL_CONFIRMATION = False
        request = self._request("JOBCRON")
        view = self._view_with_valid_serializer(request)

        response = view.reset_password_confirm(request)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["code"], "APPLICATION_ACCESS_DENIED")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("old-password-123!"))

    @patch("user.views.djoser_settings")
    def test_reset_confirm_allows_account_application(self, djoser_settings):
        djoser_settings.PASSWORD_CHANGED_EMAIL_CONFIRMATION = False
        request = self._request("REFAPART")
        view = self._view_with_valid_serializer(request)

        response = view.reset_password_confirm(request)

        self.assertEqual(response.status_code, 204)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("new-password-456!"))
