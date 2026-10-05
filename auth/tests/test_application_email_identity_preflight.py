from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from access.models import Applications


class ApplicationEmailIdentityPreflightTests(TestCase):
    def setUp(self):
        self.application = Applications.objects.create(Code="REFAPART", Name="RefaPart", IsActive=True)
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
        self._create_raw_user("user@example.com", self.application.ApplicationID)
        self._create_raw_user("USER@example.com", self.application.ApplicationID)
        with self.assertRaises(CommandError):
            call_command("audit_application_email_identity", stdout=StringIO())

    def test_orphan_application_identity_fails(self):
        self._create_raw_user("orphan@example.com", 999999)
        with self.assertRaises(CommandError):
            call_command("audit_application_email_identity", stdout=StringIO())

    def test_same_normalized_email_in_different_applications_is_not_duplicate(self):
        other = Applications.objects.create(Code="JOBCRON", Name="JobCron", IsActive=True)
        self._create_raw_user("user@example.com", self.application.ApplicationID)
        self._create_raw_user("USER@example.com", other.ApplicationID)
        with self.assertRaises(CommandError):
            call_command("audit_application_email_identity", stdout=StringIO())
