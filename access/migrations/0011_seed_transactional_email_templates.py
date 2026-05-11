from django.db import migrations


EMAIL_ACTIONS = [
    ("REGISTER", "Registro de usuario"),
    ("VERIFY_ACCOUNT", "Confirmacion de cuenta"),
    ("RESEND_ACTIVATION", "Reenvio de activacion"),
    ("PASSWORD_RESET", "Recuperacion de password"),
    ("PASSWORD_CHANGED", "Password cambiado"),
    ("EMAIL_RESET", "Cambio de email solicitado"),
    ("EMAIL_CHANGED", "Email cambiado"),
    ("VERIFICATION_CODE", "Codigo de verificacion"),
    ("NEW_DEVICE_LOGIN", "Inicio desde nuevo dispositivo"),
    ("ACCOUNT_BLOCKED", "Cuenta bloqueada"),
    ("ORGANIZATION_INVITATION", "Invitacion a organizacion o proyecto"),
]


def seed_email_templates(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    ApplicationEmailSettings = apps.get_model("access", "ApplicationEmailSettings")
    TransactionalEmailTemplates = apps.get_model("access", "TransactionalEmailTemplates")

    brand_defaults = {
        "TECNOTELEC": {
            "CommercialName": "Tecno Telec",
            "PrimaryColor": "#0E5A8A",
            "SenderEmail": "no-reply@tecnotelec.local",
            "SenderName": "Tecno Telec",
            "BaseDomain": "tecnotelec.local",
            "RedirectBaseUrl": "http://localhost:3000",
        },
        "LEXNOVA": {
            "CommercialName": "LexNova",
            "PrimaryColor": "#0E2A47",
            "SenderEmail": "no-reply@lexnova.local",
            "SenderName": "LexNova",
            "BaseDomain": "lexnova.local",
            "RedirectBaseUrl": "http://localhost:3001",
        },
        "JOBCRON": {
            "CommercialName": "JobCron",
            "PrimaryColor": "#162033",
            "SenderEmail": "no-reply@jobcron.local",
            "SenderName": "JobCron",
            "BaseDomain": "jobcron.local",
            "RedirectBaseUrl": "http://localhost:3002",
        },
    }

    for application in Applications.objects.all():
        defaults = brand_defaults.get(
            application.Code,
            {
                "CommercialName": application.Name,
                "PrimaryColor": "#1F2937",
                "SenderEmail": "no-reply@auth.local",
                "SenderName": application.Name,
                "BaseDomain": "",
                "RedirectBaseUrl": "",
            },
        )
        ApplicationEmailSettings.objects.update_or_create(
            ApplicationID=application,
            defaults={**defaults, "IsActive": True},
        )

        for action_code, action_name in EMAIL_ACTIONS:
            TransactionalEmailTemplates.objects.update_or_create(
                ApplicationID=application,
                ActionCode=action_code,
                LanguageCode="es-MX",
                Channel="EMAIL",
                defaults={
                    "SubjectTemplate": "{{ commercial_name }} - " + action_name,
                    "TextBodyTemplate": (
                        "Hola{% if user %} {{ user.email }}{% endif %}. "
                        "{{ action_name }}. Ingresa aqui: {{ action_url }}"
                    ),
                    "HtmlBodyTemplate": (
                        "<h1>{{ commercial_name }}</h1>"
                        "<p>{{ action_name }}</p>"
                        "<p><a href=\"{{ action_url }}\">Continuar</a></p>"
                    ),
                    "IsActive": True,
                },
            )


class Migration(migrations.Migration):

    dependencies = [
        ("access", "0010_transactionalemailtemplates_emaildeliverylogs_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_email_templates, migrations.RunPython.noop),
    ]
