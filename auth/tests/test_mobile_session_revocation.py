from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from access.models import Applications, RefreshTokens, UserSessions
from user.models import UserAccount


class MobileSessionContractTests(TestCase):
    def setUp(self):
        self.application = Applications.objects.create(
            Code="MOBILE_TEST",
            Name="Mobile Test",
            IsActive=True,
        )
        self.password = "StrongPassword123!"
        self.user = UserAccount.objects.create_user(
            email="mobile.session@example.test",
            password=self.password,
            first_name="Mobile",
            last_name="Session",
            idApp=self.application.ApplicationID,
        )
        self.user.is_active = True
        self.user.save(update_fields=["is_active"])
        self.client = APIClient()

    def login(self, fingerprint="android-mobile-test-device"):
        return self.client.post(
            "/api/auth/jwt/create/",
            {
                "email": self.user.email,
                "password": self.password,
                "ApplicationCode": self.application.Code,
            },
            format="json",
            HTTP_X_APPLICATION_CODE=self.application.Code,
            HTTP_X_DEVICE_FINGERPRINT=fingerprint,
            HTTP_X_DEVICE_NAME="Android Test Device",
            HTTP_X_DEVICE_TYPE="ANDROID",
            HTTP_X_DEVICE_OS="Android",
        )

    def bearer_get(self, path, access):
        return self.client.get(
            path,
            HTTP_AUTHORIZATION=f"Bearer {access}",
            HTTP_X_APPLICATION_CODE=self.application.Code,
        )

    def test_login_returns_session_id_for_mobile_session_binding(self):
        response = self.login()

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("session_id", response.data)

        session = UserSessions.objects.get(SessionID=response.data["session_id"])
        self.assertEqual(session.UserID_id, self.user.id)
        self.assertEqual(session.ApplicationID_id, self.application.ApplicationID)

    def test_refresh_body_works_while_tracked_session_is_active(self):
        login = self.login()

        response = self.client.post(
            "/api/auth/jwt/refresh/",
            {"refresh": login.data["refresh"]},
            format="json",
            HTTP_X_APPLICATION_CODE=self.application.Code,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)

    def test_logout_revokes_refresh_and_session_and_is_idempotent(self):
        login = self.login()
        access = login.data["access"]
        refresh = login.data["refresh"]
        session_id = login.data["session_id"]

        response = self.client.post(
            "/api/auth/logout/",
            {"refresh": refresh},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {access}",
            HTTP_X_APPLICATION_CODE=self.application.Code,
        )
        self.assertEqual(response.status_code, 204)

        session = UserSessions.objects.get(SessionID=session_id)
        tracked_refresh = RefreshTokens.objects.get(SessionID_id=session_id)
        self.assertIsNotNone(session.RevokedAt)
        self.assertFalse(session.IsOnline)
        self.assertIsNotNone(tracked_refresh.RevokedAt)

        repeated = self.client.post(
            "/api/auth/logout/",
            {"refresh": refresh},
            format="json",
            HTTP_X_APPLICATION_CODE=self.application.Code,
        )
        self.assertEqual(repeated.status_code, 204)

    def test_revoked_refresh_token_is_rejected(self):
        login = self.login()
        tracked_refresh = RefreshTokens.objects.get(
            SessionID_id=login.data["session_id"]
        )
        tracked_refresh.RevokedAt = timezone.now()
        tracked_refresh.RevokedReason = "TEST_REVOKED"
        tracked_refresh.save(update_fields=["RevokedAt", "RevokedReason"])

        response = self.client.post(
            "/api/auth/jwt/refresh/",
            {"refresh": login.data["refresh"]},
            format="json",
            HTTP_X_APPLICATION_CODE=self.application.Code,
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["code"], "REFRESH_REVOKED")

    def test_revoked_session_rejects_its_access_token(self):
        login = self.login()
        session = UserSessions.objects.get(SessionID=login.data["session_id"])
        session.RevokedAt = timezone.now()
        session.RevokedReason = "TEST_REVOKED"
        session.IsOnline = False
        session.save(update_fields=["RevokedAt", "RevokedReason", "IsOnline"])

        response = self.bearer_get("/api/users/me/", login.data["access"])

        self.assertEqual(response.status_code, 401)

    def test_revoking_another_session_keeps_current_session_valid(self):
        first = self.login(fingerprint="android-device-first")
        second = self.login(fingerprint="android-device-second")

        revoke_other = self.client.delete(
            f"/api/access/me/sessions/{first.data['session_id']}/",
            HTTP_AUTHORIZATION=f"Bearer {second.data['access']}",
            HTTP_X_APPLICATION_CODE=self.application.Code,
        )
        self.assertEqual(revoke_other.status_code, 204)

        still_valid = self.bearer_get("/api/users/me/", second.data["access"])
        self.assertEqual(still_valid.status_code, 200)
