from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent

TARGETS = (
    ".env.local.example",
    "access/management/commands/seed_auth_e2e_users.py",
    "access/migrations/0005_seed_auth_reference_data.py",
    "auth/email_settings.py",
    "access/migrations/0012_brand_transactional_email_templates.py",
    "access/migrations/0018_seed_web_applications_email_settings.py",
)


class CreactivaBrandIdentitySourceTests(unittest.TestCase):
    def test_legacy_brand_name_is_absent_from_auth_source(self):
        legacy = "imagrafity"
        offenders = []
        for relative in TARGETS:
            source = (ROOT / relative).read_text(encoding="utf-8")
            if legacy in source.lower():
                offenders.append(relative)
        self.assertEqual(offenders, [])

    def test_creactiva_brand_identity_is_present(self):
        source = "\n".join(
            (ROOT / relative).read_text(encoding="utf-8")
            for relative in TARGETS
        )
        for token in (
            "CREACTIVA",
            "Creactiva",
            "AUTH_E2E_CREACTIVA_USER",
            "AUTH_E2E_CREACTIVA_PASSWORD",
            "CREACTIVA_EMAIL_PROVIDER",
        ):
            self.assertIn(token, source)


if __name__ == "__main__":
    unittest.main()
