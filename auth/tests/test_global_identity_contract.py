from django.test import TestCase

from access.models import Applications, GlobalIdentities, GlobalIdentityAccounts
from user.models import UserAccount


class GlobalIdentityContractTests(TestCase):
    def setUp(self):
        self.refapart = Applications.objects.create(Code="REFAPART", Name="RefaPart", IsActive=True)
        self.jobcron = Applications.objects.create(Code="JOBCRON", Name="JobCron", IsActive=True)
        self.refapart_user = UserAccount.objects.create_user(
            email="user@example.com",
            password="refapart-password",
            first_name="Refa",
            last_name="Part",
            idApp=self.refapart.ApplicationID,
        )
        self.jobcron_user = UserAccount.objects.create_user(
            email="user@example.com",
            password="jobcron-password",
            first_name="Job",
            last_name="Cron",
            idApp=self.jobcron.ApplicationID,
        )

    def test_global_identity_can_link_one_account_per_application(self):
        identity = GlobalIdentities.objects.create(IsActive=True)
        GlobalIdentityAccounts.objects.create(
            GlobalIdentityID=identity,
            UserID=self.refapart_user,
            ApplicationID=self.refapart,
            IsVerified=True,
            IsActive=True,
        )
        GlobalIdentityAccounts.objects.create(
            GlobalIdentityID=identity,
            UserID=self.jobcron_user,
            ApplicationID=self.jobcron,
            IsVerified=True,
            IsActive=True,
        )

        self.assertEqual(identity.Accounts.filter(IsActive=True).count(), 2)

    def test_linking_does_not_share_passwords(self):
        identity = GlobalIdentities.objects.create(IsActive=True)
        GlobalIdentityAccounts.objects.create(
            GlobalIdentityID=identity,
            UserID=self.refapart_user,
            ApplicationID=self.refapart,
            IsVerified=True,
            IsActive=True,
        )
        GlobalIdentityAccounts.objects.create(
            GlobalIdentityID=identity,
            UserID=self.jobcron_user,
            ApplicationID=self.jobcron,
            IsVerified=True,
            IsActive=True,
        )

        self.assertTrue(self.refapart_user.check_password("refapart-password"))
        self.assertFalse(self.refapart_user.check_password("jobcron-password"))
        self.assertTrue(self.jobcron_user.check_password("jobcron-password"))
        self.assertFalse(self.jobcron_user.check_password("refapart-password"))

    def test_link_requires_explicit_verification(self):
        identity = GlobalIdentities.objects.create(IsActive=True)
        link = GlobalIdentityAccounts.objects.create(
            GlobalIdentityID=identity,
            UserID=self.refapart_user,
            ApplicationID=self.refapart,
            IsVerified=False,
            IsActive=False,
        )

        self.assertFalse(link.IsVerified)
        self.assertFalse(link.IsActive)
