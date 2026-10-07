from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from unittest.mock import Mock, patch

from access.models import Applications


class ApplicationEmailIdentityPreflightTests(TestCase):
    def setUp(self):
        self.application, _ = Applications.objects.get_or_create(
            Code="REFAPART", defaults={"Name": "RefaPart", "IsActive": True}
        )
        self.User = get_user_model()

    def _create_raw_user(self, email, application_id):
        user = self.User(email=email, idApp=application_id)
        user.set_password("test-password")
        user.save()
        return user

    def test_clean_application_identity_data_passes(self):
        self._create_raw_user("user@example.com", self.application.ApplicationID)
        output = StringIO()
        call_command("audit_application_email_identity", stdout=output)
        self.assertIn("preflight passed", output.getvalue())

    def test_case_insensitive_duplicate_in_same_application_fails(self):
        mock_user_model = Mock()
        mock_user_model.objects.values_list.return_value = [self.application.ApplicationID]

        duplicate_rows = Mock()
        mock_user_model.objects.annotate.return_value = duplicate_rows
        duplicate_rows.values.return_value.annotate.return_value.filter.return_value.order_by.return_value = [
            {
                "idApp": self.application.ApplicationID,
                "normalized_email": "user@example.com",
                "count": 2,
            }
        ]

        normalized_rows = Mock()
        mock_user_model.objects.exclude.return_value = normalized_rows
        normalized_rows.values_list.return_value.order_by.return_value = []

        with patch(
            "user.management.commands.audit_application_email_identity.get_user_model",
            return_value=mock_user_model,
        ):
            with self.assertRaises(CommandError):
                call_command("audit_application_email_identity", stdout=StringIO())

    def test_orphan_application_identity_fails(self):
        self._create_raw_user("orphan@example.com", 999999)
        with self.assertRaises(CommandError):
            call_command("audit_application_email_identity", stdout=StringIO())

    def test_same_normalized_email_in_different_apps_is_not_duplicate_group(self):
        other, _ = Applications.objects.get_or_create(
            Code="JOBCRON", defaults={"Name": "JobCron", "IsActive": True}
        )
        self._create_raw_user("user@example.com", self.application.ApplicationID)
        self._create_raw_user("USER@example.com", other.ApplicationID)
        output = StringIO()
        with self.assertRaises(CommandError):
            call_command("audit_application_email_identity", "--json", stdout=output)
        self.assertIn('"duplicate_application_email_groups": []', output.getvalue())
        self.assertIn('"non_normalized_user_ids":', output.getvalue())
