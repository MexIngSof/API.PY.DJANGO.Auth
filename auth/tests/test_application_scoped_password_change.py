from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from access.models import Applications
from user.models import UserAccount
from user.views import RequiredPasswordChangeView


@override_settings(GATEWAY_INTERNAL_SHARED_SECRET="test-gateway-secret")
class ApplicationScopedPasswordChangeTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.refapart = Applications.objects.create(Code="REFAPART", Name="RefaPart", IsActive=True)
        self.jobcron = Applications.objects.create(Code="JOBCRON", Name="JobCron", IsActive=True)
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

    def _change(self, application_code):
        request = self.factory.post(
            "/api/auth/password/change-required/",
            {
                "current_password": "old-password-123!",
                "new_password": "new-password-456!",
                "re_new_password": "new-password-456!",
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

    def test_required_password_change_is_rejected_from_different_application(self):
        response = self._change("JOBCRON")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["code"], "APPLICATION_ACCESS_DENIED")
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("old-password-123!"))
        self.assertTrue(self.user.must_change_password)
