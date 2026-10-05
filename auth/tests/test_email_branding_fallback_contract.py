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

        with patch("auth.custom_email.get_application_code", return_value="REFAPART"), patch(
            "access.models.Applications.objects.filter"
        ) as applications_filter, patch(
            "access.models.ApplicationEmailSettings.objects.filter"
        ) as settings_filter, patch(
            "access.models.TransactionalEmailTemplates.objects.filter"
        ) as templates_filter:
            applications_filter.return_value.first.return_value = application
            settings_filter.return_value.first.return_value = None
            templates_filter.return_value.first.return_value = None
            resolved_application, email_settings, template = email.resolve_email_metadata(
                {"user": user, "language_code": "es-MX"}
            )

        self.assertIs(resolved_application, application)
        self.assertIsNone(email_settings)
        self.assertIsNone(template)
        self.assertEqual(resolved_application.Code, "REFAPART")
