from types import SimpleNamespace
from unittest.mock import ANY, Mock, patch

from django.test import SimpleTestCase, override_settings
from django.urls import resolve
from rest_framework.test import APIRequestFactory

from user.scoped_views import ApplicationScopedUserViewSet


@override_settings(GATEWAY_INTERNAL_SHARED_SECRET="test-context")
class PasswordSetupResetTests(SimpleTestCase):
    def request(self, email, application_code="JOBCRON"):
        return APIRequestFactory().post(
            "/api/users/reset_password/",
            {"email": email},
            format="json",
            HTTP_X_APPLICATION_CODE=application_code,
            HTTP_X_GATEWAY_INTERNAL_TOKEN="test-context",
        )

    def test_canonical_reset_route_uses_scoped_viewset(self):
        match = resolve("/api/users/reset_password/")

        self.assertEqual(match.func.actions, {"post": "reset_password"})
        self.assertEqual(match.func.cls, ApplicationScopedUserViewSet)

    @patch("user.scoped_views.get_user_email", side_effect=lambda user: user.email)
    @patch("user.scoped_views.record_access_event")
    @patch("user.scoped_views.djoser_settings")
    @patch("user.scoped_views.find_local_account")
    @patch("user.scoped_views.resolve_application_context")
    def test_unusable_password_receives_first_access_reset_within_application(
        self,
        resolve_application_context_mock,
        find_local_account_mock,
        djoser_settings_mock,
        record_access_event_mock,
        _get_user_email_mock,
    ):
        application = SimpleNamespace(ApplicationID=3, Code="JOBCRON")
        user = SimpleNamespace(
            email="super.admin.jobcron@example.test",
            idApp=3,
            is_active=True,
            must_change_password=True,
            has_usable_password=lambda: False,
        )
        resolve_application_context_mock.return_value = application
        find_local_account_mock.return_value = user
        message = Mock()
        djoser_settings_mock.EMAIL.password_reset.return_value = message

        response = ApplicationScopedUserViewSet.as_view({"post": "reset_password"})(
            self.request(user.email)
        )

        self.assertEqual(response.status_code, 204)
        find_local_account_mock.assert_called_once_with(
            application,
            user.email,
            active_only=True,
        )
        message.send.assert_called_once_with([user.email])
        record_access_event_mock.assert_called_once_with(
            ANY,
            "identity.password.reset.requested",
            user=user,
            application=application,
            metadata={"first_access": True},
        )

    @patch("user.scoped_views.get_user_email", side_effect=lambda user: user.email)
    @patch("user.scoped_views.record_access_event")
    @patch("user.scoped_views.djoser_settings")
    @patch("user.scoped_views.find_local_account")
    @patch("user.scoped_views.resolve_application_context")
    def test_usable_password_reset_remains_application_scoped(
        self,
        resolve_application_context_mock,
        find_local_account_mock,
        djoser_settings_mock,
        record_access_event_mock,
        _get_user_email_mock,
    ):
        application = SimpleNamespace(ApplicationID=1, Code="REFAPART")
        user = SimpleNamespace(
            email="user@example.test",
            idApp=1,
            is_active=True,
            must_change_password=False,
            has_usable_password=lambda: True,
        )
        resolve_application_context_mock.return_value = application
        find_local_account_mock.return_value = user
        message = Mock()
        djoser_settings_mock.EMAIL.password_reset.return_value = message

        response = ApplicationScopedUserViewSet.as_view({"post": "reset_password"})(
            self.request(user.email, "REFAPART")
        )

        self.assertEqual(response.status_code, 204)
        find_local_account_mock.assert_called_once_with(
            application,
            user.email,
            active_only=True,
        )
        message.send.assert_called_once_with([user.email])
        record_access_event_mock.assert_called_once()

    @patch("user.scoped_views.find_local_account")
    @patch("user.scoped_views.resolve_application_context")
    def test_unknown_email_keeps_anti_enumeration_contract(
        self,
        resolve_application_context_mock,
        find_local_account_mock,
    ):
        application = SimpleNamespace(ApplicationID=1, Code="REFAPART")
        resolve_application_context_mock.return_value = application
        find_local_account_mock.return_value = None

        response = ApplicationScopedUserViewSet.as_view({"post": "reset_password"})(
            self.request("missing@example.test", "REFAPART")
        )

        self.assertEqual(response.status_code, 204)
        find_local_account_mock.assert_called_once_with(
            application,
            "missing@example.test",
            active_only=True,
        )
