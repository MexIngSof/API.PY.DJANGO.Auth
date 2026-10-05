from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from user.account_scope import find_local_account, normalize_email


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
