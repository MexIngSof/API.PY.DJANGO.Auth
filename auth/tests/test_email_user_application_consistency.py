from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.exceptions import AuthenticationFailed

from auth.custom_email import ACTION_PASSWORD_RESET, AuthTransactionalEmailMixin


class EmailUserApplicationConsistencyTests(SimpleTestCase):
    def test_email_metadata_rejects_user_from_different_application(self):
        email = AuthTransactionalEmailMixin()
        email.action_code = ACTION_PASSWORD_RESET
        email.request = object()
        trusted_application = SimpleNamespace(ApplicationID=10, Code="REFAPART")
        user = SimpleNamespace(idApp=20)

        with patch("auth.custom_email.resolve_application_context", return_value=trusted_application):
            with self.assertRaises(AuthenticationFailed) as context:
                email.resolve_email_metadata({"user": user, "language_code": "es-MX"})

        self.assertEqual(context.exception.get_codes(), "APPLICATION_ACCOUNT_MISMATCH")
