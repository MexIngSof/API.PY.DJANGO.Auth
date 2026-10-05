from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings
from django.urls import resolve
from rest_framework.test import APIRequestFactory

from user.account_scope import find_local_account, normalize_email
from user.models import UserAccount
from user.scoped_views import ApplicationScopedUserViewSet


@override_settings(GATEWAY_INTERNAL_SHARED_SECRET="test-context")
class ApplicationScopedIdentityFlowTests(SimpleTestCase):
    def test_normalize_email_is_case_insensitive_and_trimmed(self):
        self.assertEqual(normalize_email("  USER@Example.COM  "), "user@example.com")

    def test_task3_preserves_global_email_unique_until_identity_migration(self):
        self.assertTrue(UserAccount._meta.get_field("email").unique)

    @patch("user.account_scope.get_user_model")
    def test_account_lookup_uses_application_and_normalized_email(self, get_user_model_mock):
        application = SimpleNamespace(ApplicationID=4, Code="REFAPART")
        query = Mock()
        query.first.return_value = SimpleNamespace(id=17)
        get_user_model_mock.return_value.objects.filter.return_value = query

        user = find_local_account(application, "  USER@Example.COM  ")

        self.assertEqual(user.id, 17)
        get_user_model_mock.return_value.objects.filter.assert_called_once_with(
            idApp=4,
            email__iexact="user@example.com",
        )

    @patch("user.account_scope.get_user_model")
    def test_active_account_lookup_adds_active_filter(self, get_user_model_mock):
        application = SimpleNamespace(ApplicationID=9, Code="JOBCRON")
        base_query = Mock()
        active_query = Mock()
        active_query.first.return_value = None
        base_query.filter.return_value = active_query
        get_user_model_mock.return_value.objects.filter.return_value = base_query

        user = find_local_account(application, "user@example.com", active_only=True)

        self.assertIsNone(user)
        base_query.filter.assert_called_once_with(is_active=True)

    @patch("user.scoped_views.get_user_model")
    @patch("user.scoped_views.decode_uid", return_value="17")
    @patch("user.scoped_views.resolve_application_context")
    def test_activation_rejects_user_from_another_application(
        self,
        resolve_application_context_mock,
        _decode_uid_mock,
        get_user_model_mock,
    ):
        application = SimpleNamespace(ApplicationID=4, Code="REFAPART")
        user = SimpleNamespace(id=17, idApp=9)
        resolve_application_context_mock.return_value = application
        get_user_model_mock.return_value.objects.filter.return_value.first.return_value = user
        request = APIRequestFactory().post(
            "/api/users/activation/",
            {"uid": "encoded", "token": "activation-token"},
            format="json",
            HTTP_X_APPLICATION_CODE="REFAPART",
            HTTP_X_GATEWAY_INTERNAL_TOKEN="test-context",
        )

        response = ApplicationScopedUserViewSet.as_view({"post": "activation"})(request)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["code"], "APPLICATION_ACCESS_DENIED")

    @patch("user.scoped_views.djoser_settings")
    @patch("user.scoped_views.find_local_account")
    @patch("user.scoped_views.resolve_application_context")
    def test_email_reset_request_uses_application_scoped_account(
        self,
        resolve_application_context_mock,
        find_local_account_mock,
        djoser_settings_mock,
    ):
        application = SimpleNamespace(ApplicationID=4, Code="REFAPART")
        user = SimpleNamespace(email="user@example.com", idApp=4, is_active=True)
        resolve_application_context_mock.return_value = application
        find_local_account_mock.return_value = user
        message = Mock()
        djoser_settings_mock.EMAIL.username_reset.return_value = message
        request = APIRequestFactory().post(
            "/api/users/reset_email/",
            {"email": " USER@example.com "},
            format="json",
            HTTP_X_APPLICATION_CODE="REFAPART",
            HTTP_X_GATEWAY_INTERNAL_TOKEN="test-context",
        )

        response = ApplicationScopedUserViewSet.as_view({"post": "reset_username"})(request)

        self.assertEqual(response.status_code, 204)
        find_local_account_mock.assert_called_once_with(
            application,
            "user@example.com",
            active_only=True,
        )
        message.send.assert_called_once_with([user.email])

    @patch("user.scoped_views.find_local_account")
    @patch("user.scoped_views.resolve_application_context")
    def test_unknown_email_reset_keeps_anti_enumeration_contract(
        self,
        resolve_application_context_mock,
        find_local_account_mock,
    ):
        application = SimpleNamespace(ApplicationID=4, Code="REFAPART")
        resolve_application_context_mock.return_value = application
        find_local_account_mock.return_value = None
        request = APIRequestFactory().post(
            "/api/users/reset_email/",
            {"email": "missing@example.com"},
            format="json",
            HTTP_X_APPLICATION_CODE="REFAPART",
            HTTP_X_GATEWAY_INTERNAL_TOKEN="test-context",
        )

        response = ApplicationScopedUserViewSet.as_view({"post": "reset_username"})(request)

        self.assertEqual(response.status_code, 204)
        find_local_account_mock.assert_called_once_with(
            application,
            "missing@example.com",
            active_only=True,
        )

    @patch("user.scoped_views.find_local_account")
    @patch("user.scoped_views.resolve_application_context")
    def test_unknown_resend_activation_keeps_anti_enumeration_contract(
        self,
        resolve_application_context_mock,
        find_local_account_mock,
    ):
        application = SimpleNamespace(ApplicationID=4, Code="REFAPART")
        resolve_application_context_mock.return_value = application
        find_local_account_mock.return_value = None
        request = APIRequestFactory().post(
            "/api/users/resend_activation/",
            {"email": "missing@example.com"},
            format="json",
            HTTP_X_APPLICATION_CODE="REFAPART",
            HTTP_X_GATEWAY_INTERNAL_TOKEN="test-context",
        )

        response = ApplicationScopedUserViewSet.as_view({"post": "resend_activation"})(request)

        self.assertEqual(response.status_code, 204)
        find_local_account_mock.assert_called_once_with(application, "missing@example.com")

    @patch("user.scoped_views.account_belongs_to_application", return_value=False)
    @patch("user.scoped_views.resolve_application_context")
    def test_password_reset_confirm_rejects_cross_application_account(
        self,
        resolve_application_context_mock,
        _belongs_mock,
    ):
        application = SimpleNamespace(ApplicationID=4, Code="REFAPART")
        foreign_user = SimpleNamespace(id=17, idApp=9)
        resolve_application_context_mock.return_value = application
        request = APIRequestFactory().post(
            "/api/users/reset_password_confirm/",
            {"uid": "encoded", "token": "token", "new_password": "Secret123!"},
            format="json",
            HTTP_X_APPLICATION_CODE="REFAPART",
            HTTP_X_GATEWAY_INTERNAL_TOKEN="test-context",
        )
        view = ApplicationScopedUserViewSet.as_view({"post": "reset_password_confirm"})

        with patch.object(ApplicationScopedUserViewSet, "get_serializer") as get_serializer:
            serializer = Mock()
            serializer.user = foreign_user
            serializer.data = {"new_password": "Secret123!"}
            get_serializer.return_value = serializer
            response = view(request)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["code"], "APPLICATION_ACCESS_DENIED")

    @patch("user.scoped_views.account_belongs_to_application", return_value=False)
    @patch("user.scoped_views.resolve_application_context")
    def test_email_reset_confirm_rejects_cross_application_account(
        self,
        resolve_application_context_mock,
        _belongs_mock,
    ):
        application = SimpleNamespace(ApplicationID=4, Code="REFAPART")
        foreign_user = SimpleNamespace(id=17, idApp=9)
        resolve_application_context_mock.return_value = application
        request = APIRequestFactory().post(
            "/api/users/reset_email_confirm/",
            {"uid": "encoded", "token": "token", "new_email": "new@example.com"},
            format="json",
            HTTP_X_APPLICATION_CODE="REFAPART",
            HTTP_X_GATEWAY_INTERNAL_TOKEN="test-context",
        )
        view = ApplicationScopedUserViewSet.as_view({"post": "reset_username_confirm"})

        with patch.object(ApplicationScopedUserViewSet, "get_serializer") as get_serializer:
            serializer = Mock()
            serializer.user = foreign_user
            serializer.data = {"new_email": "new@example.com"}
            get_serializer.return_value = serializer
            response = view(request)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["code"], "APPLICATION_ACCESS_DENIED")

    def test_all_live_identity_mutation_routes_use_scoped_viewset(self):
        routes = (
            "/api/users/activation/",
            "/api/users/resend_activation/",
            "/api/users/reset_password/",
            "/api/users/reset_password_confirm/",
            "/api/users/set_email/",
            "/api/users/reset_email/",
            "/api/users/reset_email_confirm/",
        )

        for route in routes:
            with self.subTest(route=route):
                self.assertEqual(resolve(route).func.cls, ApplicationScopedUserViewSet)
