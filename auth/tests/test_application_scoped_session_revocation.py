from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from access.models import Applications, RefreshTokens, UserSessions
from access.views import OwnUserSessionViewSet
from user.mobile_session_views import LogoutView
from user.models import UserAccount


@override_settings(GATEWAY_INTERNAL_SHARED_SECRET="test-gateway-secret")
class ApplicationScopedSessionRevocationTests(TestCase):
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
            password="test-password",
            first_name="Test",
            last_name="User",
            idApp=self.refapart.ApplicationID,
        )

    def _request(self, path, application_code, data=None):
        request = self.factory.post(
            path,
            data or {},
            format="json",
            HTTP_X_APPLICATION_CODE=application_code,
            HTTP_X_GATEWAY_INTERNAL_TOKEN="test-gateway-secret",
        )
        force_authenticate(request, user=self.user)
        return request

    def test_revoke_all_only_revokes_sessions_in_effective_application(self):
        refapart_session = UserSessions.objects.create(
            UserID=self.user,
            ApplicationID=self.refapart,
            IsOnline=True,
        )
        jobcron_session = UserSessions.objects.create(
            UserID=self.user,
            ApplicationID=self.jobcron,
            IsOnline=True,
        )

        view = OwnUserSessionViewSet.as_view({"post": "revoke_all"})
        response = view(self._request("/access/me/sessions/revoke-all/", "REFAPART"))

        self.assertEqual(response.status_code, 200)
        refapart_session.refresh_from_db()
        jobcron_session.refresh_from_db()
        self.assertIsNotNone(refapart_session.RevokedAt)
        self.assertIsNone(jobcron_session.RevokedAt)

    def test_logout_rejects_refresh_tracked_to_different_application(self):
        session = UserSessions.objects.create(
            UserID=self.user,
            ApplicationID=self.refapart,
            IsOnline=True,
        )
        tracked = RefreshTokens(UserID=self.user, SessionID=session)

        request = self._request(
            "/api/auth/logout/",
            "JOBCRON",
            {"refresh": "opaque-refresh"},
        )
        view = LogoutView.as_view()
        with patch("user.mobile_session_views.tracked_refresh", return_value=tracked), patch(
            "user.mobile_session_views.revoke_tracked_refresh"
        ) as revoke:
            response = view(request)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["code"], "APPLICATION_ACCESS_DENIED")
        revoke.assert_not_called()
