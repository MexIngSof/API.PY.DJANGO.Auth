from pathlib import Path
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from auth.email_settings import get_email_settings, resolve_email_backend


class LocalMailpitProviderTests(SimpleTestCase):
    def test_mailpit_is_complete_without_ses_credentials_and_uses_safe_defaults(self):
        with patch.dict("os.environ", {"AUTH_EMAIL_PROVIDER": "mailpit"}, clear=True):
            resolved = get_email_settings("AUTH", development_mode=True)

        self.assertEqual(resolved.provider, "mailpit")
        self.assertTrue(resolved.is_complete)
        self.assertEqual(resolved.smtp_host, "mailpit")
        self.assertEqual(resolved.smtp_port, 1025)
        self.assertFalse(resolved.smtp_use_tls)
        self.assertEqual(
            resolve_email_backend(resolved),
            "django.core.mail.backends.smtp.EmailBackend",
        )

    def test_project_smtp_settings_override_shared_defaults(self):
        env = {
            "AUTH_EMAIL_PROVIDER": "mailpit",
            "AUTH_EMAIL_SMTP_HOST": "shared-mailpit",
            "AUTH_EMAIL_SMTP_PORT": "1125",
            "AUTH_EMAIL_SMTP_USE_TLS": "true",
            "REFAPART_EMAIL_SMTP_HOST": "mailpit",
            "REFAPART_EMAIL_SMTP_PORT": "1025",
            "REFAPART_EMAIL_SMTP_USE_TLS": "false",
        }
        with patch.dict("os.environ", env, clear=True):
            resolved = get_email_settings("REFAPART", development_mode=True)

        self.assertEqual(resolved.smtp_host, "mailpit")
        self.assertEqual(resolved.smtp_port, 1025)
        self.assertFalse(resolved.smtp_use_tls)

    def test_project_provider_precedence_is_preserved(self):
        env = {
            "AUTH_EMAIL_PROVIDER": "mailpit",
            "REFAPART_EMAIL_PROVIDER": "ses",
        }
        with patch.dict("os.environ", env, clear=True):
            resolved = get_email_settings("REFAPART", development_mode=True)

        self.assertEqual(resolved.provider, "ses")
        self.assertEqual(resolved.smtp_host, "")
        self.assertIsNone(resolved.smtp_port)

    def test_django_settings_map_only_mailpit_to_local_smtp_fields(self):
        settings_path = Path(__file__).resolve().parents[2] / "config" / "settings.py"
        source = settings_path.read_text(encoding="utf-8")
        self.assertIn("EMAIL_BACKEND = resolve_email_backend(", source)
        self.assertIn('if AUTH_EMAIL_SETTINGS.provider == "mailpit":', source)
        self.assertIn("EMAIL_HOST = AUTH_EMAIL_SETTINGS.smtp_host", source)
        self.assertIn("EMAIL_PORT = AUTH_EMAIL_SETTINGS.smtp_port", source)
        self.assertIn("EMAIL_USE_TLS = AUTH_EMAIL_SETTINGS.smtp_use_tls", source)
        self.assertIn('EMAIL_HOST_USER = getenv("AUTH_EMAIL_SMTP_USERNAME", "")', source)
        self.assertIn('EMAIL_HOST_PASSWORD = getenv("AUTH_EMAIL_SMTP_PASSWORD", "")', source)
        self.assertNotIn("EMAIL_HOST_USER = AWS_SES_ACCESS_KEY_ID", source)
        self.assertNotIn("EMAIL_HOST_PASSWORD = AWS_SES_SECRET_ACCESS_KEY", source)

    def test_mailpit_is_rejected_outside_development_even_with_deferred_external(self):
        with patch.dict("os.environ", {"AUTH_EMAIL_PROVIDER": "mailpit"}, clear=True):
            with self.assertRaises(ImproperlyConfigured):
                get_email_settings(
                    "AUTH",
                    development_mode=False,
                    allow_deferred_external=True,
                )

    def test_ses_credentials_never_populate_smtp_configuration(self):
        env = {
            "AUTH_EMAIL_PROVIDER": "ses",
            "AUTH_AWS_SES_ACCESS_KEY_ID": "synthetic-ses-access",
            "AUTH_AWS_SES_SECRET_ACCESS_KEY": "synthetic-ses-secret",
            "AUTH_AWS_SES_REGION_NAME": "us-east-1",
            "AUTH_AWS_SES_FROM_EMAIL": "ses@example.invalid",
        }
        with patch.dict("os.environ", env, clear=True):
            resolved = get_email_settings("AUTH", development_mode=True)

        self.assertEqual(resolved.provider, "ses")
        self.assertEqual(resolved.smtp_host, "")
        self.assertIsNone(resolved.smtp_port)
        self.assertFalse(resolved.smtp_use_tls)
        self.assertEqual(resolve_email_backend(resolved), "django_ses.SESBackend")

    def test_explicit_backend_override_and_console_policy_remain_unchanged(self):
        with patch.dict("os.environ", {"AUTH_EMAIL_PROVIDER": "mailpit"}, clear=True):
            mailpit = get_email_settings("AUTH", development_mode=True)
        self.assertEqual(
            resolve_email_backend(mailpit, explicit_backend="custom.EmailBackend"),
            "custom.EmailBackend",
        )
        with patch.dict("os.environ", {}, clear=True):
            console = get_email_settings("AUTH", development_mode=True)
        self.assertEqual(
            resolve_email_backend(console),
            "django.core.mail.backends.console.EmailBackend",
        )

    def test_local_environment_example_documents_only_local_smtp_settings(self):
        example = Path(__file__).resolve().parents[2] / ".env.local.example"
        source = example.read_text(encoding="utf-8")
        for value in [
            "AUTH_EMAIL_PROVIDER=mailpit",
            "AUTH_EMAIL_SMTP_HOST=mailpit",
            "AUTH_EMAIL_SMTP_PORT=1025",
            "AUTH_EMAIL_SMTP_USE_TLS=False",
        ]:
            self.assertIn(value, source)

    def test_invalid_smtp_port_fails_closed(self):
        with patch.dict(
            "os.environ",
            {"AUTH_EMAIL_PROVIDER": "mailpit", "AUTH_EMAIL_SMTP_PORT": "invalid"},
            clear=True,
        ):
            with self.assertRaises(ImproperlyConfigured):
                get_email_settings("AUTH", development_mode=True)

