from django.test import TestCase
from rest_framework.test import APIClient

from access.models import Applications, UserSessions
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

    def login(self):
        return self.client.post(
            "/api/auth/jwt/create/",
            {
                "email": self.user.email,
                "password": self.password,
                "ApplicationCode": self.application.Code,
            },
            format="json",
            HTTP_X_APPLICATION_CODE=self.application.Code,
            HTTP_X_DEVICE_FINGERPRINT="android-mobile-test-device",
            HTTP_X_DEVICE_NAME="Android Test Device",
            HTTP_X_DEVICE_TYPE="ANDROID",
            HTTP_X_DEVICE_OS="Android",
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
