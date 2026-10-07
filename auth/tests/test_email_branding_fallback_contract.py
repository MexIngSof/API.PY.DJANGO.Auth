from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from auth.custom_email import ACTION_ACTIVATION, AuthTransactionalEmailMixin


class EmailBrandingFallbackContractTests(SimpleTestCase):
    def test_base_template_context_keeps_application_identity_without_db_branding(self):
        email = AuthTransactionalEmailMixin()
        email.action_code = ACTION_ACTIVATION
        email.request = object()
        application = SimpleNamespace(ApplicationID=10, Code="REFAPART")
        user = SimpleNamespace(idApp=10, email="user@example.com")

        with patch("auth.custom_email.resolve_application_context", return_value=application), patch(
            "access.models.ApplicationEmailSettings.objects.filter"
        ) as settings_filter, patch(
            "access.models.TransactionalEmailTemplates.objects.filter"
        ) as templates_filter:
            settings_filter.return_value.first.return_value = None
            templates_filter.return_value.first.return_value = None
            resolved_application, email_settings, template = email.resolve_email_metadata(
                {"user": user, "language_code": "es-MX"}
            )

        self.assertIs(resolved_application, application)
        self.assertIsNone(email_settings)
        self.assertIsNone(template)
        self.assertEqual(resolved_application.Code, "REFAPART")
