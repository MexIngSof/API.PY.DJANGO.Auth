from types import SimpleNamespace

from django.template.loader import get_template
from django.test import SimpleTestCase


BASE_EMAIL_TEMPLATES = [
    "register",
    "verify_account",
    "password_reset",
    "password_changed",
    "email_reset",
    "email_changed",
]


class BaseEmailTemplateTests(SimpleTestCase):
    def test_all_auth_actions_have_reusable_base_templates(self):
        context = {
            "action_url": "https://example.test/auth/action",
            "commercial_name": "Example App",
            "user": SimpleNamespace(email="user@example.test"),
        }

        for template_name in BASE_EMAIL_TEMPLATES:
            with self.subTest(template_name=template_name):
                template = get_template(f"auth_emails/base/{template_name}.html")
                rendered = template.render(context)
                self.assertIn("Example App", rendered)
                self.assertIn("user@example.test", rendered)
