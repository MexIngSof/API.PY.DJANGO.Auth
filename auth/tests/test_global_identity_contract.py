from django.core.exceptions import ValidationError
from django.test import TestCase

from access.global_identity import link_account, unlink_account, verify_link
from access.models import Applications, GlobalIdentities, GlobalIdentityAccounts
from user.models import UserAccount


class GlobalIdentityContractTests(TestCase):
    def setUp(self):
        self.refapart, _ = Applications.objects.get_or_create(
            Code="REFAPART", defaults={"Name": "RefaPart", "IsActive": True}
        )
        self.jobcron, _ = Applications.objects.get_or_create(
            Code="JOBCRON", defaults={"Name": "JobCron", "IsActive": True}
        )
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
        link = link_account(
            global_identity=identity,
            user=self.refapart_user,
            application=self.refapart,
        )

        self.assertFalse(link.IsVerified)
        self.assertFalse(link.IsActive)

        verified = verify_link(
            global_identity=identity,
            user=self.refapart_user,
            application=self.refapart,
        )
        self.assertTrue(verified.IsVerified)
        self.assertTrue(verified.IsActive)
        self.assertIsNotNone(verified.VerifiedAt)

    def test_link_rejects_account_from_another_application(self):
        identity = GlobalIdentities.objects.create(IsActive=True)
        with self.assertRaisesMessage(ValidationError, "APPLICATION_ACCOUNT_MISMATCH"):
            link_account(
                global_identity=identity,
                user=self.refapart_user,
                application=self.jobcron,
            )

    def test_account_cannot_be_active_in_two_global_identities(self):
        first = GlobalIdentities.objects.create(IsActive=True)
        second = GlobalIdentities.objects.create(IsActive=True)
        first_link = link_account(
            global_identity=first,
            user=self.refapart_user,
            application=self.refapart,
        )
        verify_link(
            global_identity=first,
            user=self.refapart_user,
            application=self.refapart,
        )

        with self.assertRaisesMessage(ValidationError, "GLOBAL_IDENTITY_ACCOUNT_ALREADY_LINKED"):
            link_account(
                global_identity=second,
                user=self.refapart_user,
                application=self.refapart,
            )
        first_link.refresh_from_db()
        self.assertTrue(first_link.IsActive)

    def test_unlink_allows_explicit_relink_without_auto_linking(self):
        first = GlobalIdentities.objects.create(IsActive=True)
        second = GlobalIdentities.objects.create(IsActive=True)
        link_account(global_identity=first, user=self.refapart_user, application=self.refapart)
        verify_link(global_identity=first, user=self.refapart_user, application=self.refapart)
        unlinked = unlink_account(
            global_identity=first,
            user=self.refapart_user,
            application=self.refapart,
        )
        self.assertFalse(unlinked.IsActive)
        self.assertIsNotNone(unlinked.UnlinkedAt)

        replacement = link_account(
            global_identity=second,
            user=self.refapart_user,
            application=self.refapart,
        )
        self.assertFalse(replacement.IsVerified)
        self.assertFalse(replacement.IsActive)
        self.assertNotEqual(replacement.GlobalIdentityAccountID, unlinked.GlobalIdentityAccountID)

        # Same email in another application remains unrelated until explicitly linked.
        self.assertFalse(GlobalIdentityAccounts.objects.filter(UserID=self.jobcron_user).exists())
