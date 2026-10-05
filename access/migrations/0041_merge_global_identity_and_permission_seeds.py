from django.db import migrations


class Migration(migrations.Migration):
    """Reconcile the two access migration leaves created after 0038."""

    dependencies = [
        ("access", "0039_global_identity_correlation"),
        ("access", "0040_seed_imagrafity_commerce_channel_permissions"),
    ]

    operations = []
