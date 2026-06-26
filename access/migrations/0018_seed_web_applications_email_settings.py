from django.db import migrations


NOTIFICATION_FROM_EMAIL = "cash.1dip1@gmail.com"

APPLICATIONS = [
    {
        "code": "REFAPART",
        "name": "REFAPART",
        "description": "Plataforma comercial de localizacion de refacciones automotrices.",
        "host": "http://localhost:3008",
        "logo": "http://localhost:3008/brand/refapart-logo-dark.png",
        "primary": "#E10600",
        "sender": "REFAPART",
    },
    {
        "code": "JOBCRON",
        "name": "JobCron",
        "description": "Centro operativo y administrativo del ecosistema.",
        "host": "http://localhost:3000",
        "logo": "http://localhost:3000/brand/logo.png",
        "primary": "#2563EB",
        "sender": "JobCron",
    },
    {
        "code": "DOCUCORE",
        "name": "DocuCore",
        "description": "Motor documental y herramientas de procesamiento de archivos.",
        "host": "http://localhost:3002",
        "logo": "http://localhost:3002/brand/logo.png",
        "primary": "#D93025",
        "sender": "DocuCore",
    },
    {
        "code": "LEXNOVA",
        "name": "LexNova",
        "description": "Plataforma legal profesional.",
        "host": "http://localhost:3004",
        "logo": "http://localhost:3004/brand/logo.png",
        "primary": "#1D4ED8",
        "sender": "LexNova",
    },
    {
        "code": "TECNOTELEC",
        "name": "Tecno Telec",
        "description": "Comercio tecnico, soluciones y catalogo operativo.",
        "host": "http://localhost:3001",
        "logo": "http://localhost:3001/brand/logo.png",
        "primary": "#0070DE",
        "sender": "Tecno Telec",
    },
    {
        "code": "IMAGRAFITY",
        "name": "Imagrafity",
        "description": "Personalizacion creativa y comercio visual.",
        "host": "http://localhost:3006",
        "logo": "http://localhost:3006/brand/logo.png",
        "primary": "#8B5CF6",
        "sender": "Imagrafity",
    },
    {
        "code": "FISCORA",
        "name": "Fiscora",
        "description": "Producto fiscal y administracion CFDI.",
        "host": "http://localhost:3005",
        "logo": "http://localhost:3005/brand/logo.png",
        "primary": "#0F766E",
        "sender": "Fiscora",
    },
    {
        "code": "LEADHUNTER",
        "name": "LeadHunter",
        "description": "Prospeccion y gestion comercial.",
        "host": "http://localhost:3007",
        "logo": "http://localhost:3007/brand/logo.png",
        "primary": "#136F63",
        "sender": "LeadHunter",
    },
    {
        "code": "MEXINGSOF",
        "name": "MexIngSof",
        "description": "Sitio corporativo y comercial MexIngSof.",
        "host": "http://localhost:3009",
        "logo": "http://localhost:3009/brand/logo.png",
        "primary": "#22C55E",
        "sender": "MexIngSof",
    },
]


def seed_web_applications(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    ApplicationEmailSettings = apps.get_model("access", "ApplicationEmailSettings")
    Roles = apps.get_model("roles", "Roles")
    ApplicationRoles = apps.get_model("access", "ApplicationRoles")

    customer_role, _ = Roles.objects.update_or_create(
        Name="CUSTOMER",
        defaults={"Description": "Cliente de aplicaciones comerciales."},
    )

    for item in APPLICATIONS:
        application, _ = Applications.objects.update_or_create(
            Code=item["code"],
            defaults={
                "Name": item["name"],
                "Description": item["description"],
                "IsActive": True,
            },
        )
        ApplicationEmailSettings.objects.update_or_create(
            ApplicationID=application,
            defaults={
                "CommercialName": item["name"],
                "LogoUrl": item["logo"],
                "PrimaryColor": item["primary"],
                "SenderEmail": NOTIFICATION_FROM_EMAIL,
                "SenderName": item["sender"],
                "BaseDomain": item["host"].replace("http://", "").replace("https://", ""),
                "RedirectBaseUrl": item["host"],
                "IsActive": True,
            },
        )
        ApplicationRoles.objects.get_or_create(
            ApplicationID=application,
            RoleID=customer_role,
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("access", "0017_seed_refapart_operational_permissions"),
    ]

    operations = [
        migrations.RunPython(seed_web_applications, noop_reverse),
    ]
