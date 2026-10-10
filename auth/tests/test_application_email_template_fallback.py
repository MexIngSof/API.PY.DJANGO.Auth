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

    @patch("auth.custom_email.get_email_settings")
    def test_password_reset_uses_configured_public_app_url_over_database_redirect(self, get_email_settings):
        application = SimpleNamespace(Code="JOBCRON")
        database_email_settings = SimpleNamespace(
            RedirectBaseUrl="http://localhost:3000",
            CommercialName="JobCron",
            LogoUrl="",
            PrimaryColor="",
            SenderName="JobCron",
        )
        get_email_settings.return_value = SimpleNamespace(public_app_url="http://jobcron.localhost")

        class ContextEmailBase:
            def get_context_data(self):
                return {
                    "url": "password-reset/uid-value/token-value",
                    "protocol": "http",
                    "domain": "localhost",
                }

        class PasswordResetContextEmail(AuthTransactionalEmailMixin, ContextEmailBase):
            pass

        email = PasswordResetContextEmail()
        email.action_code = ACTION_PASSWORD_RESET

        with patch.object(email, "resolve_email_metadata", return_value=(application, database_email_settings, None)), patch.object(
            email, "resolve_file_template_name", return_value=""
        ):
            context = email.get_context_data()

        self.assertEqual(
            context["action_url"],
            "http://jobcron.localhost/reset-password?uid=uid-value&token=token-value",
        )
        self.assertEqual(context["redirect_base_url"], "http://jobcron.localhost")
        get_email_settings.assert_called_once_with("JOBCRON", development_mode=True)
