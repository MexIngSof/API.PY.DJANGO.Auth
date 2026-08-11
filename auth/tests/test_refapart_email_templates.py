from types import SimpleNamespace

from django.template.loader import get_template
from django.test import RequestFactory
from django.test import SimpleTestCase

from auth.custom_email import (
    ACTION_ACTIVATION,
    ActivationEmail,
    canonical_password_reset_url,
    TEMPLATE_SOURCE_DB_FALLBACK,
    TEMPLATE_SOURCE_DJOSER_FALLBACK,
    TEMPLATE_SOURCE_FILE,
)


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
    def test_refapart_password_reset_url_uses_canonical_web_route(self):
        action_url = canonical_password_reset_url(
            "http://localhost:3008",
            "password-reset/uid-refapart/token-refapart",
        )

        self.assertEqual(
            action_url,
            "http://localhost:3008/reset-password?uid=uid-refapart&token=token-refapart",
        )

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
        self.assertIn("cid:refapart-logo", source)
        self.assertNotIn("data:image/svg+xml", source)
        self.assertNotIn("logo_url", source)
        self.assertNotIn("logo_cid", source)

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


class RefaPartEmailTemplateSourceTests(SimpleTestCase):
    def make_activation_email(self):
        email = object.__new__(ActivationEmail)
        email.action_code = ACTION_ACTIVATION
        email.template_name = "djoser/email/activation.html"
        return email

    def test_refapart_file_template_wins_over_db_template(self):
        email = self.make_activation_email()
        application = SimpleNamespace(Code="REFAPART")
        db_template = SimpleNamespace(
            SubjectTemplate="DB subject",
            TextBodyTemplate="DB body",
            HtmlBodyTemplate="<p>DB</p>",
        )

        file_template_name = email.resolve_file_template_name(application)
        template_source = email.resolve_template_source(file_template_name, db_template)

        self.assertEqual(file_template_name, "auth_emails/refapart/verify_account.html")
        self.assertEqual(template_source, TEMPLATE_SOURCE_FILE)

    def test_refapart_file_template_renders_subject_text_and_html(self):
        email = self.make_activation_email()
        context = {
            "action_url": "https://refapart.example.test/auth/action",
            "commercial_name": "REFAPART",
            "user": SimpleNamespace(email="cliente@refapart.example.test"),
        }

        subject = email.render_block_from_file_template(
            "auth_emails/refapart/verify_account.html",
            "subject",
            context,
        )
        text_body = email.render_block_from_file_template(
            "auth_emails/refapart/verify_account.html",
            "text_body",
            context,
        )
        html = get_template("auth_emails/refapart/verify_account.html").render(context)

        self.assertEqual(subject, "REFAPART - Verifica tu cuenta")
        self.assertIn("cliente@refapart.example.test", text_body)
        self.assertIn("https://refapart.example.test/auth/action", text_body)
        self.assertIn("Verifica tu cuenta REFAPART", html)

    def test_refapart_file_email_renders_as_html_without_visible_plain_text_prefix(self):
        email = self.make_activation_email()
        email.request = RequestFactory().post(
            "/api/users/resend_activation/",
            HTTP_HOST="localhost:3008",
            HTTP_X_APPLICATION_CODE="REFAPART",
        )
        email.context = {
            "action_url": "https://refapart.example.test/auth/action",
            "commercial_name": "REFAPART",
            "user": SimpleNamespace(email="cliente@refapart.example.test"),
        }
        email.auth_email_file_template_name = "auth_emails/refapart/verify_account.html"
        email.auth_email_template_source = TEMPLATE_SOURCE_FILE
        email.get_context_data = lambda: email.context

        email.render()

        self.assertEqual(email.subject, "REFAPART - Verifica tu cuenta")
        self.assertEqual(email.content_subtype, "html")
        self.assertTrue(email.body.lstrip().lower().startswith("<!doctype html>"))
        self.assertIn("Verifica tu cuenta REFAPART", email.body)
        self.assertIn("cid:refapart-logo", email.body)
        self.assertNotIn("data:image/svg+xml", email.body)
        self.assertNotIn("Tu cuenta REFAPART fue creada correctamente.", email.body[:300])
        self.assertTrue(
            any(
                hasattr(attachment, "get")
                and attachment.get("Content-ID") == "<refapart-logo>"
                for attachment in email.attachments
            )
        )

    def test_db_template_is_only_fallback_when_file_template_is_missing(self):
        email = self.make_activation_email()
        application = SimpleNamespace(Code="APP_WITHOUT_FILE")
        db_template = SimpleNamespace(
            SubjectTemplate="DB subject",
            TextBodyTemplate="DB body",
            HtmlBodyTemplate="<p>DB</p>",
        )

        file_template_name = email.resolve_file_template_name(application)
        template_source = email.resolve_template_source(file_template_name, db_template)

        self.assertEqual(file_template_name, "")
        self.assertEqual(template_source, TEMPLATE_SOURCE_DB_FALLBACK)

    def test_missing_application_uses_djoser_fallback(self):
        email = self.make_activation_email()

        file_template_name = email.resolve_file_template_name(None)
        template_source = email.resolve_template_source(file_template_name, None)

        self.assertEqual(file_template_name, "")
        self.assertEqual(template_source, TEMPLATE_SOURCE_DJOSER_FALLBACK)
