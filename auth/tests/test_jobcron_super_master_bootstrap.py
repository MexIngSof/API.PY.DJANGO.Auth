from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from access.management.commands.ensure_super_master import send_setup_email


class JobCronSuperMasterBootstrapTests(SimpleTestCase):
    @patch("access.management.commands.ensure_super_master.get_email_settings")
    @patch("access.management.commands.ensure_super_master.djoser_settings")
    def test_setup_email_uses_jobcron_password_reset_flow(self, settings_mock, email_settings_mock):
        email_settings_mock.return_value = SimpleNamespace(
            public_app_url="https://jobcron.example.test"
        )
        message = Mock()
        settings_mock.EMAIL.password_reset.return_value = message
        user = SimpleNamespace(email="super.admin.jobcron@example.test")

        send_setup_email(user)

        request, context = settings_mock.EMAIL.password_reset.call_args.args
        self.assertEqual(request.headers["X-Application-Code"], "JOBCRON")
        self.assertEqual(request.META["HTTP_HOST"], "jobcron.example.test")
        self.assertTrue(request.is_secure())
        self.assertEqual(context, {"user": user})
        message.send.assert_called_once_with([user.email])
