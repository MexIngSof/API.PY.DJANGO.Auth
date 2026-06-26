from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from auth.email_settings import get_email_settings


class ProjectEmailSettingsTests(SimpleTestCase):
    def test_development_uses_console_fallback_without_ses(self):
        with patch.dict("os.environ", {}, clear=True):
            settings = get_email_settings("REFAPART", development_mode=True)

        self.assertEqual(settings.project_code, "REFAPART")
        self.assertEqual(settings.provider, "console")
        self.assertEqual(settings.from_email, "cash.1dip1@gmail.com")
        self.assertTrue(settings.is_complete)

    def test_project_settings_override_shared_auth_settings(self):
        env = {
            "AUTH_EMAIL_PROVIDER": "ses",
            "AUTH_AWS_SES_REGION_NAME": "us-east-1",
            "AUTH_AWS_SES_ACCESS_KEY_ID": "auth-access",
            "AUTH_AWS_SES_SECRET_ACCESS_KEY": "auth-secret",
            "AUTH_AWS_SES_FROM_EMAIL": "auth@example.com",
            "REFAPART_EMAIL_PROVIDER": "ses",
            "REFAPART_AWS_SES_REGION_NAME": "us-west-2",
            "REFAPART_AWS_SES_ACCESS_KEY_ID": "refapart-access",
            "REFAPART_AWS_SES_SECRET_ACCESS_KEY": "refapart-secret",
            "REFAPART_AWS_SES_FROM_EMAIL": "refapart@example.com",
        }
        with patch.dict("os.environ", env, clear=True):
            settings = get_email_settings("REFAPART", development_mode=True)

        self.assertEqual(settings.provider, "ses")
        self.assertEqual(settings.region_name, "us-west-2")
        self.assertEqual(settings.from_email, "refapart@example.com")
        self.assertTrue(settings.is_complete)

    def test_production_fails_when_email_provider_is_incomplete(self):
        with patch.dict("os.environ", {"AUTH_EMAIL_PROVIDER": "ses"}, clear=True):
            with self.assertRaises(ImproperlyConfigured):
                get_email_settings("AUTH", development_mode=False)
