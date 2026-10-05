from types import SimpleNamespace
from unittest.mock import patch

from django.template import TemplateDoesNotExist
from django.test import SimpleTestCase

from auth.custom_email import (
    ACTION_PASSWORD_RESET,
    AuthTransactionalEmailMixin,
)


class ApplicationEmailTemplateFallbackTests(SimpleTestCase):
    def setUp(self):
        self.email = AuthTransactionalEmailMixin()
        self.email.action_code = ACTION_PASSWORD_RESET

    @patch("auth.custom_email.get_template")
    def test_application_template_wins_over_base_template(self, get_template):
        application = SimpleNamespace(Code="REFAPART")
        get_template.return_value = object()

        resolved = self.email.resolve_file_template_name(application)

        self.assertEqual(resolved, "auth_emails/refapart/password_reset.html")
        get_template.assert_called_once_with("auth_emails/refapart/password_reset.html")

    @patch("auth.custom_email.get_template")
    def test_missing_application_template_falls_back_to_base_template(self, get_template):
        application = SimpleNamespace(Code="JOBCRON")

        def lookup(name):
            if name == "auth_emails/jobcron/password_reset.html":
                raise TemplateDoesNotExist(name)
            if name == "auth_emails/base/password_reset.html":
                return object()
            raise AssertionError(f"Unexpected template lookup: {name}")

        get_template.side_effect = lookup

        resolved = self.email.resolve_file_template_name(application)

        self.assertEqual(resolved, "auth_emails/base/password_reset.html")
        self.assertEqual(
            [call.args[0] for call in get_template.call_args_list],
            [
                "auth_emails/jobcron/password_reset.html",
                "auth_emails/base/password_reset.html",
            ],
        )

    @patch("auth.custom_email.get_template")
    def test_missing_application_and_base_templates_use_non_file_fallback(self, get_template):
        application = SimpleNamespace(Code="JOBCRON")
        get_template.side_effect = TemplateDoesNotExist("missing")

        resolved = self.email.resolve_file_template_name(application)

        self.assertEqual(resolved, "")
