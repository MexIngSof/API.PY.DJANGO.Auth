from django.db import migrations


def seed_refapart_application(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    ApplicationEmailSettings = apps.get_model("access", "ApplicationEmailSettings")
    ApplicationRoles = apps.get_model("access", "ApplicationRoles")
    Roles = apps.get_model("roles", "Roles")

    application, _ = Applications.objects.update_or_create(
        Code="REFAPART",
        defaults={
            "Name": "REFAPART",
            "Description": "Plataforma comercial de localizacion de refacciones automotrices.",
            "IsActive": True,
        },
    )

    ApplicationEmailSettings.objects.update_or_create(
        ApplicationID=application,
        defaults={
            "CommercialName": "REFAPART",
                "LogoUrl": "http://localhost:3008/brand/refapart-logo-dark.png",
            "PrimaryColor": "#E10600",
            "SenderEmail": "no-reply@refapart.local",
            "SenderName": "REFAPART",
            "BaseDomain": "localhost:3008",
            "RedirectBaseUrl": "http://localhost:3008",
            "IsActive": True,
        },
    )

    customer_role, _ = Roles.objects.update_or_create(
        Name="CUSTOMER",
        defaults={"Description": "Cliente de aplicaciones comerciales."},
    )
    ApplicationRoles.objects.get_or_create(
        ApplicationID=application,
        RoleID=customer_role,
    )


def remove_refapart_application(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    Applications.objects.filter(Code="REFAPART").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("access", "0015_seed_lexnova_document_permissions"),
        ("roles", "0005_alter_userroles_id"),
    ]

    operations = [
        migrations.RunPython(seed_refapart_application, remove_refapart_application),
    ]
