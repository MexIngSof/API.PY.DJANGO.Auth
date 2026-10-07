from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from access.models import Applications, PasswordHistory, RefreshTokens, UserSessions
from user.models import UserAccount
from user.views import RequiredPasswordChangeView


@override_settings(GATEWAY_INTERNAL_SHARED_SECRET="test-gateway-secret")
class ApplicationScopedPasswordChangeTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.refapart, _ = Applications.objects.get_or_create(
            Code="REFAPART", defaults={"Name": "RefaPart", "IsActive": True}
        )
        self.jobcron, _ = Applications.objects.get_or_create(
            Code="JOBCRON", defaults={"Name": "JobCron", "IsActive": True}
        )
        self.user = UserAccount.objects.create_user(
            email="user@example.com",
            password="old-password-123!",
            first_name="Test",
            last_name="User",
            idApp=self.refapart.ApplicationID,
        )
        self.user.is_active = True
        self.user.must_change_password = True
        self.user.save(update_fields=["is_active", "must_change_password"])

    def _change(self, application_code, new_password="new-password-456!"):
        request = self.factory.post(
            "/api/auth/password/change-required/",
            {
                "current_password": "old-password-123!",
                "new_password": new_password,
                "re_new_password": new_password,
            },
            format="json",
            HTTP_X_APPLICATION_CODE=application_code,
            HTTP_X_GATEWAY_INTERNAL_TOKEN="test-gateway-secret",
        )
        force_authenticate(request, user=self.user)
        return RequiredPasswordChangeView.as_view()(request)

    def test_required_password_change_is_allowed_in_account_application(self):
        response = self._change("REFAPART")

        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("new-password-456!"))
        self.assertFalse(self.user.must_change_password)
        self.assertEqual(PasswordHistory.objects.filter(UserID=self.user).count(), 1)

    def test_required_password_change_rejects_common_password(self):
        response = self._change("REFAPART", new_password="password")

        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("old-password-123!"))

    def test_required_password_change_rejects_numeric_password(self):
        response = self._change("REFAPART", new_password="123456789012")

        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("old-password-123!"))

    def test_required_password_change_revokes_sessions_and_refresh_tokens(self):
        session = UserSessions.objects.create(
            UserID=self.user,
            ApplicationID=self.refapart,
            IsOnline=True,
        )
        refresh = RefreshTokens.objects.create(
            UserID=self.user,
            SessionID=session,
            TokenHash="test-password-change-token-hash",
        )

        response = self._change("REFAPART")

        self.assertEqual(response.status_code, 200)
        session.refresh_from_db()
        refresh.refresh_from_db()
        self.assertIsNotNone(session.RevokedAt)
        self.assertEqual(session.RevokedReason, "PASSWORD_CHANGED")
        self.assertFalse(session.IsOnline)
        self.assertIsNotNone(refresh.RevokedAt)
        self.assertEqual(refresh.RevokedReason, "PASSWORD_CHANGED")

    def test_required_password_change_is_rejected_from_different_application(self):
        response = self._change("JOBCRON")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["code"], "APPLICATION_ACCESS_DENIED")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("old-password-123!"))
        self.assertTrue(self.user.must_change_password)
