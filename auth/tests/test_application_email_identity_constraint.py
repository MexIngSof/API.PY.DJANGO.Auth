from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from access.models import Applications


class ApplicationEmailIdentityConstraintTests(TestCase):
    def setUp(self):
        self.User = get_user_model()
        self.refapart, _ = Applications.objects.get_or_create(
            Code="REFAPART", defaults={"Name": "RefaPart", "IsActive": True}
        )
        self.jobcron, _ = Applications.objects.get_or_create(
            Code="JOBCRON", defaults={"Name": "JobCron", "IsActive": True}
        )

    def _create_raw_user(self, email, application):
        user = self.User(
            email=email.strip(),
            idApp=application.ApplicationID,
            first_name="Test",
            last_name="User",
        )
        user.set_password("test-password")
        user.save()
        return user

    def test_same_normalized_email_is_allowed_in_different_applications(self):
        self._create_raw_user("user@example.com", self.refapart)
        second = self._create_raw_user("USER@example.com", self.jobcron)

        self.assertEqual(second.idApp, self.jobcron.ApplicationID)
        self.assertEqual(second.email, "USER@example.com")

    def test_same_normalized_email_is_rejected_in_same_application(self):
        self._create_raw_user("user@example.com", self.refapart)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._create_raw_user("USER@example.com", self.refapart)
