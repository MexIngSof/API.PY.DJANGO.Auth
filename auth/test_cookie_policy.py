from django.test import SimpleTestCase

from .cookie_policy import resolve_cookie_policy


class CookiePolicyTests(SimpleTestCase):
    def test_local_http_is_host_only_lax_and_not_secure(self):
        policy = resolve_cookie_policy(
            environment="local",
            auth_origin="http://localhost:8000",
            web_origins=["http://localhost:3000"],
            explicit_cross_site_origins=[],
        )
        self.assertFalse(policy.secure)
        self.assertEqual(policy.same_site, "Lax")
        self.assertIsNone(policy.domain)

    def test_https_same_registrable_site_remains_lax(self):
        policy = resolve_cookie_policy(
            environment="pro",
            auth_origin="https://auth.example.mx",
            web_origins=["https://jobcron.example.mx", "https://refapart.example.mx"],
            explicit_cross_site_origins=[],
        )
        self.assertTrue(policy.secure)
        self.assertEqual(policy.same_site, "Lax")
        self.assertIsNone(policy.domain)

    def test_cross_site_requires_explicit_allowlist(self):
        with self.assertRaises(RuntimeError):
            resolve_cookie_policy(
                environment="pro",
                auth_origin="https://auth.example.mx",
                web_origins=["https://frontend.other.test"],
                explicit_cross_site_origins=[],
            )

    def test_explicit_https_cross_site_uses_none_and_secure(self):
        origin = "https://frontend.other.test"
        policy = resolve_cookie_policy(
            environment="pro",
            auth_origin="https://auth.example.mx",
            web_origins=[origin],
            explicit_cross_site_origins=[origin],
        )
        self.assertTrue(policy.secure)
        self.assertEqual(policy.same_site, "None")
        self.assertIsNone(policy.domain)
