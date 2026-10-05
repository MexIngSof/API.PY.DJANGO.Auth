from unittest.mock import patch

from django.test import SimpleTestCase

from auth.email_settings import get_email_settings


class EmailSenderFallbackContractTests(SimpleTestCase):
    def test_application_sender_falls_back_to_configured_auth_sender(self):
        env = {
            "AUTH_NOTIFICATION_FROM_EMAIL": "auth@example.test",
        }
        with patch.dict("os.environ", env, clear=True):
            settings = get_email_settings("JOBCRON", development_mode=True)

        self.assertEqual(settings.from_email, "auth@example.test")

    def test_sender_has_no_hardcoded_personal_address_when_unconfigured(self):
        with patch.dict("os.environ", {}, clear=True):
            settings = get_email_settings("JOBCRON", development_mode=True)

        self.assertNotEqual(settings.from_email, "cash.1dip1@gmail.com")
