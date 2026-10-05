from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIRequestFactory

from user.account_scope import find_local_account, normalize_email
from user.scoped_views import ApplicationScopedUserViewSet


@override_settings(GATEWAY_INTERNAL_SHARED_SECRET="test-context")
class ApplicationScopedIdentityFlowTests(SimpleTestCase):
    def test_normalize_email_is_case_insensitive_and_trimmed(self):
        self.assertEqual(normalize_email("  USER@Example.COM  "), "user@example.com")

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
