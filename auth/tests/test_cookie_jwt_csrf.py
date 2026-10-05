from types import SimpleNamespace
from unittest.mock import patch

from rest_framework import status
from rest_framework.response import Response

from django.test import SimpleTestCase, override_settings
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from user.authentication import CustomJWTAuthentication
from user.mobile_session_views import CustomTokenRefreshView, LogoutView
from user.scoped_views import ApplicationScopedTokenObtainPairView


@override_settings(
    AUTH_COOKIE="access",
    CSRF_COOKIE_NAME="csrftoken",
    GATEWAY_INTERNAL_SHARED_SECRET="cookie-csrf-test-secret",
    ALLOWED_HOSTS=["testserver"],
)
class CookieJWTCSRFAuthenticationTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory(enforce_csrf_checks=True)
        self.authentication = CustomJWTAuthentication()
        self.user = SimpleNamespace(idApp=17, is_authenticated=True)

    def _request(self, method, *, csrf_cookie=None, csrf_header=None, bearer=False):
        cookie = "access=valid.jwt.token"
        if csrf_cookie:
            cookie += f"; csrftoken={csrf_cookie}"
        kwargs = {"HTTP_COOKIE": cookie}
        if csrf_header:
            kwargs["HTTP_X_CSRFTOKEN"] = csrf_header
        if bearer:
            kwargs["HTTP_AUTHORIZATION"] = "Bearer valid.jwt.token"
        builder = getattr(self.factory, method.lower())
        raw_request = builder(
            "/api/auth/protected-test/",
            HTTP_X_APPLICATION_CODE="REFAPART",
            HTTP_X_GATEWAY_INTERNAL_TOKEN="cookie-csrf-test-secret",
            **kwargs,
        )
        return Request(raw_request)

    def _authenticate(self, request):
        with (
            patch.object(self.authentication, "get_validated_token", return_value={"jti": ""}),
            patch.object(self.authentication, "get_user", return_value=self.user),
            patch(
                "user.authentication.resolve_application_context",
                return_value=SimpleNamespace(ApplicationID=17),
            ),
        ):
            return self.authentication.authenticate(request)

    def test_state_changing_cookie_request_without_csrf_is_rejected(self):
        with self.assertRaises(PermissionDenied):
            self._authenticate(self._request("post"))

    def test_state_changing_cookie_request_with_invalid_csrf_is_rejected(self):
        with self.assertRaises(PermissionDenied):
            self._authenticate(
                self._request("post", csrf_cookie="a" * 32, csrf_header="b" * 32)
            )

    def test_state_changing_cookie_request_with_valid_csrf_is_accepted(self):
        token = "a" * 32
        self.assertEqual(
            self._authenticate(
                self._request("post", csrf_cookie=token, csrf_header=token)
            )[0],
            self.user,
        )

    def test_safe_cookie_request_does_not_require_csrf(self):
        self.assertEqual(self._authenticate(self._request("get"))[0], self.user)

    def test_explicit_bearer_token_does_not_use_cookie_csrf_contract(self):
        self.assertEqual(
            self._authenticate(self._request("post", bearer=True))[0],
            self.user,
        )

    def test_refresh_cookie_without_csrf_is_rejected(self):
        request = self.factory.post(
            "/api/auth/jwt/refresh/",
            {},
            format="json",
            HTTP_COOKIE="refresh=refresh-token",
        )
        response = CustomTokenRefreshView.as_view()(request)
        self.assertEqual(response.status_code, 403)

    def test_logout_refresh_cookie_without_csrf_is_rejected(self):
        request = self.factory.post(
            "/api/auth/logout/",
            {},
            format="json",
            HTTP_COOKIE="refresh=refresh-token",
        )
        response = LogoutView.as_view()(request)
        self.assertEqual(response.status_code, 403)

    @override_settings(AUTH_COOKIE_PATH="/api/auth/")
    def test_logout_deletes_auth_cookies_using_configured_path(self):
        request = self.factory.post("/api/auth/logout/", {}, format="json")
        with (
            patch(
                "user.mobile_session_views.resolve_application_context",
                return_value=SimpleNamespace(ApplicationID=17, Code="REFAPART"),
            ),
            patch("user.mobile_session_views.revoke_tracked_refresh", return_value=None),
        ):
            response = LogoutView.as_view()(request)

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.cookies["access"]["path"], "/api/auth/")
        self.assertEqual(response.cookies["refresh"]["path"], "/api/auth/")

    def test_browser_login_without_csrf_is_rejected(self):
        request = self.factory.post(
            "/api/auth/jwt/create/",
            {"email": "user@example.test", "password": "password"},
            format="json",
            HTTP_ORIGIN="http://testserver",
            HTTP_X_APPLICATION_CODE="REFAPART",
            HTTP_X_GATEWAY_INTERNAL_TOKEN="cookie-csrf-test-secret",
        )
        with (
            patch(
                "user.scoped_views.resolve_application_context",
                return_value=SimpleNamespace(ApplicationID=17, Code="REFAPART"),
            ),
            patch("user.scoped_views.find_local_account", return_value=None),
            patch("user.scoped_views.record_login_attempt"),
            patch(
                "rest_framework_simplejwt.views.TokenObtainPairView.post",
                return_value=Response(
                    {"detail": "invalid credentials"},
                    status=status.HTTP_401_UNAUTHORIZED,
                ),
            ),
        ):
            response = ApplicationScopedTokenObtainPairView.as_view()(request)
        self.assertEqual(response.status_code, 403)

    def test_browser_login_with_valid_csrf_is_accepted(self):
        token = "a" * 32
        request = self.factory.post(
            "/api/auth/jwt/create/",
            {"email": "user@example.test", "password": "password"},
            format="json",
            HTTP_ORIGIN="http://testserver",
            HTTP_COOKIE=f"csrftoken={token}",
            HTTP_X_CSRFTOKEN=token,
            HTTP_X_APPLICATION_CODE="REFAPART",
            HTTP_X_GATEWAY_INTERNAL_TOKEN="cookie-csrf-test-secret",
        )
        with (
            patch(
                "user.scoped_views.resolve_application_context",
                return_value=SimpleNamespace(ApplicationID=17, Code="REFAPART"),
            ),
            patch("user.scoped_views.find_local_account", return_value=None),
            patch("user.scoped_views.record_login_attempt"),
            patch(
                "rest_framework_simplejwt.views.TokenObtainPairView.post",
                return_value=Response(
                    {"access": "new-access-token", "refresh": "new-refresh-token"},
                    status=status.HTTP_200_OK,
                ),
            ),
        ):
            response = ApplicationScopedTokenObtainPairView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.cookies)
        self.assertIn("refresh", response.cookies)
    def test_csrf_bootstrap_view_returns_browser_token_and_sets_cookie(self):
        from django.middleware.csrf import CsrfViewMiddleware
        from user.scoped_views import CsrfTokenView

        raw_request = self.factory.get("/api/auth/csrf/")
        response = CsrfTokenView.as_view()(raw_request)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["csrfToken"])
        response.render()
        response = CsrfViewMiddleware(lambda request: None).process_response(
            raw_request, response
        )
        self.assertIn("csrftoken", response.cookies)
        self.assertEqual(response.cookies["csrftoken"]["httponly"], "")

    def test_refresh_rotation_updates_refresh_cookie(self):
        request = self.factory.post(
            "/api/auth/jwt/refresh/",
            {},
            format="json",
            HTTP_COOKIE="refresh=old-refresh-token",
        )
        application = SimpleNamespace(ApplicationID=17, Code="REFAPART")
        token = SimpleNamespace(
            get=lambda key: {
                "application_id": 17,
                "application_code": "REFAPART",
            }.get(key)
        )
        with (
            patch("user.mobile_session_views.SessionAuthentication.enforce_csrf"),
            patch(
                "user.mobile_session_views.resolve_application_context",
                return_value=application,
            ),
            patch("user.mobile_session_views.RefreshToken", return_value=token),
            patch("user.mobile_session_views.tracked_refresh", return_value=None),
            patch("user.mobile_session_views.tracked_refresh_is_revoked", return_value=False),
            patch(
                "rest_framework_simplejwt.views.TokenRefreshView.post",
                return_value=Response(
                    {"access": "new-access-token", "refresh": "new-refresh-token"},
                    status=status.HTTP_200_OK,
                ),
            ),
        ):
            response = CustomTokenRefreshView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.cookies["refresh"].value, "new-refresh-token")
        self.assertTrue(response.cookies["refresh"]["httponly"])
        self.assertEqual(response.cookies["refresh"]["samesite"], "Lax")