from django.db import migrations


SOCIAL_PROVIDERS = [
    ("GOOGLE", "Google", "google-oauth2"),
    ("FACEBOOK", "Facebook", "facebook"),
]


def seed_social_providers(apps, schema_editor):
    SocialProviders = apps.get_model("access", "SocialProviders")

    for code, name, backend_name in SOCIAL_PROVIDERS:
        SocialProviders.objects.update_or_create(
            Code=code,
            defaults={
                "Name": name,
                "BackendName": backend_name,
                "IsActive": True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("access", "0008_socialproviders_socialloginattempts_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_social_providers, migrations.RunPython.noop),
    ]
