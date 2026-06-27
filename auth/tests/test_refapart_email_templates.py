from types import SimpleNamespace

from django.template.loader import get_template
from django.test import SimpleTestCase


REFAPART_EMAIL_TEMPLATES = [
    "base",
    "register",
    "verify_account",
    "password_reset",
    "password_changed",
    "email_reset",
    "email_changed",
]


class RefaPartEmailTemplateTests(SimpleTestCase):
    def test_refapart_templates_resolve_and_render(self):
        context = {
            "action_url": "https://refapart.example.test/auth/action",
            "commercial_name": "REFAPART",
            "frontend_url": "https://refapart.example.test",
            "support_email": "soporte@refapart.example.test",
            "current_year": "2026",
            "expiration_minutes": "30",
            "user": SimpleNamespace(email="cliente@refapart.example.test"),
        }

        for template_name in REFAPART_EMAIL_TEMPLATES:
            with self.subTest(template_name=template_name):
                template = get_template(f"auth_emails/refapart/{template_name}.html")
                rendered = template.render(context)
                self.assertIn("REFAPART", rendered)
                self.assertIn("cliente@refapart.example.test", rendered)
                self.assertIn("<table", rendered)
                self.assertIn("</table>", rendered)

    def test_refapart_child_templates_define_required_blocks(self):
        required_blocks = [
            "{% block subject %}",
            "{% block text_body %}",
            "{% block headline %}",
            "{% block intro %}",
            "{% block detail %}",
            "{% block cta %}",
        ]

        for template_name in REFAPART_EMAIL_TEMPLATES:
            if template_name == "base":
                continue
            with self.subTest(template_name=template_name):
                with open(
                    f"templates/auth_emails/refapart/{template_name}.html",
                    encoding="utf-8",
                ) as template_file:
                    source = template_file.read()

                self.assertIn('{% extends "auth_emails/refapart/base.html" %}', source)
                for block in required_blocks:
                    self.assertIn(block, source)

    def test_refapart_base_uses_email_safe_structure(self):
        with open("templates/auth_emails/refapart/base.html", encoding="utf-8") as template_file:
            source = template_file.read().lower()

        self.assertIn("<!doctype html>", source)
        self.assertIn('role="presentation"', source)
        self.assertIn("alt=", source)

        forbidden_patterns = [
            "<script",
            "<form",
            "display:flex",
            "display: flex",
            "grid-template",
            "position:fixed",
            "position: fixed",
            "linear-gradient",
            "box-shadow",
        ]
        for pattern in forbidden_patterns:
            with self.subTest(pattern=pattern):
                self.assertNotIn(pattern, source)
