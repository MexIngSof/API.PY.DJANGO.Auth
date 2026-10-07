from django.conf import settings
from config.settings import resolve_allowed_hosts
from django.test import SimpleTestCase


class AuthenticationCookieSettingsTests(SimpleTestCase):
    def test_jwt_authentication_uses_the_access_cookie(self):
        self.assertEqual(settings.AUTH_COOKIE, "access")

    def test_cookie_lifetimes_match_the_jwt_lifetimes(self):
        self.assertEqual(settings.AUTH_COOKIE_ACCESS_MAX_AGE, 15 * 60)
        self.assertEqual(settings.AUTH_COOKIE_REFRESH_MAX_AGE, 7 * 24 * 60 * 60)

    def test_auth_cookies_are_http_only_and_share_the_configured_policy(self):
        self.assertTrue(settings.AUTH_COOKIE_HTTP_ONLY)
        self.assertEqual(settings.AUTH_COOKIE_PATH, "/")
        self.assertEqual(settings.AUTH_COOKIE_SAMESITE, "Lax")
        self.assertFalse(settings.AUTH_COOKIE_SECURE)

    def test_csrf_cookie_shares_authentication_cookie_site_and_transport_policy(self):
        self.assertEqual(settings.CSRF_COOKIE_SAMESITE, settings.AUTH_COOKIE_SAMESITE)
        self.assertEqual(settings.CSRF_COOKIE_SECURE, settings.AUTH_COOKIE_SECURE)
        self.assertFalse(settings.CSRF_COOKIE_HTTPONLY)
    def test_allowed_hosts_uses_django_compose_alias_when_primary_is_empty(self):
        self.assertEqual(
            resolve_allowed_hosts("", "localhost,127.0.0.1,api-multiproyecto"),
            ["localhost", "127.0.0.1", "api-multiproyecto"],
        )

    def test_allowed_hosts_prefers_explicit_primary_setting(self):
        self.assertEqual(
            resolve_allowed_hosts("auth.example.test", "localhost,api-multiproyecto"),
            ["auth.example.test"],
        )