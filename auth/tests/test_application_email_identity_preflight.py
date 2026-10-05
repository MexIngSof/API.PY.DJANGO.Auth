from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from access.models import Applications


class ApplicationEmailIdentityPreflightTests(TestCase):
    def setUp(self):
        self.application = Applications.objects.create(
            Code="REFAPART",
            Name="RefaPart",
            IsActive=True,
        )
        self.User = get_user_model()

    def test_clean_application_identity_data_passes(self):
        self.User.objects.create_user(
            email="user@example.com",
            password="test-password",
            idApp=self.application.ApplicationID,
        )
        output = StringIO()
        call_command("audit_application_email_identity", stdout=output)
        self.assertIn("preflight passed", output.getvalue())

    def test_case_insensitive_duplicate_in_same_application_fails(self):
        self.User.objects.create_user(
            email="user@example.com",
            password="test-password",
            idApp=self.application.ApplicationID,
        )
        self.User.objects.create_user(
            email="USER@example.com",
            password="test-password",
            idApp=self.application.ApplicationID,
        )
        with self.assertRaises(CommandError):
            call_command("audit_application_email_identity", stdout=StringIO())

    def test_orphan_application_identity_fails(self):
        self.User.objects.create_user(
            email="orphan@example.com",
            password="test-password",
            idApp=999999,
        )
        with self.assertRaises(CommandError):
            call_command("audit_application_email_identity", stdout=StringIO())

    def test_same_email_in_different_applications_is_not_a_duplicate_group(self):
        other = Applications.objects.create(Code="JOBCRON", Name="JobCron", IsActive=True)
        self.User.objects.create_user(
            email="user@example.com",
            password="test-password",
            idApp=self.application.ApplicationID,
        )
        self.User.objects.create_user(
            email="USER@example.com",
            password="test-password",
            idApp=other.ApplicationID,
        )
        output = StringIO()
        call_command("audit_application_email_identity", stdout=output)
        self.assertIn("preflight passed", output.getvalue())
