from types import SimpleNamespace

from django.template.loader import get_template
from django.test import SimpleTestCase

from auth.custom_email import jobcron_password_reset_url


JOBCRON_EMAIL_TEMPLATES = [
    "base",
    "register",
    "verify_account",
    "password_reset",
    "password_changed",
    "email_reset",
    "email_changed",
]


class JobCronEmailTemplateTests(SimpleTestCase):
    def test_jobcron_templates_resolve_and_render(self):
        context = {
            "action_url": "https://jobcron.example.test/auth/action",
            "commercial_name": "JobCron",
            "user": SimpleNamespace(email="admin@jobcron.example.test"),
        }

        for template_name in JOBCRON_EMAIL_TEMPLATES:
            with self.subTest(template_name=template_name):
                template = get_template(f"auth_emails/jobcron/{template_name}.html")
                rendered = template.render(context)
                self.assertIn("JobCron", rendered)
                self.assertIn("admin@jobcron.example.test", rendered)
                self.assertNotIn("Tecno Telec", rendered)

    def test_jobcron_child_templates_extend_jobcron_base(self):
        required_blocks = [
            "{% block subject %}",
            "{% block text_body %}",
            "{% block headline %}",
            "{% block intro %}",
            "{% block detail %}",
            "{% block cta %}",
        ]

        for template_name in JOBCRON_EMAIL_TEMPLATES:
            if template_name == "base":
                continue
            with self.subTest(template_name=template_name):
                with open(
                    f"templates/auth_emails/jobcron/{template_name}.html",
                    encoding="utf-8",
                ) as template_file:
                    source = template_file.read()

                self.assertIn('{% extends "auth_emails/jobcron/base.html" %}', source)
                self.assertNotIn("tecnotelec", source.lower())
                for block in required_blocks:
                    self.assertIn(block, source)

    def test_jobcron_password_reset_template_is_jobcron_specific(self):
        context = {
            "action_url": "https://jobcron.example.test/reset-password?uid=u&token=t",
            "commercial_name": "JobCron",
            "user": SimpleNamespace(email="admin@jobcron.example.test"),
        }
        rendered = get_template("auth_emails/jobcron/password_reset.html").render(context)

        self.assertIn("JobCron - recupera tu password", rendered)
        self.assertIn("Registramos una solicitud", rendered)
        self.assertIn("https://jobcron.example.test/reset-password?uid=u&amp;token=t", rendered)
        self.assertNotIn("Tecno Telec", rendered)

    def test_jobcron_password_reset_url_uses_web_route_query_params(self):
        action_url = jobcron_password_reset_url(
            "http://localhost:3000",
            "password-reset/uid-1/token-2",
        )

        self.assertEqual(
            action_url,
            "http://localhost:3000/reset-password?uid=uid-1&token=token-2",
        )
