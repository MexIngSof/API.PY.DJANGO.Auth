from django.db import migrations


def remove_erp_admin_application(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    Applications.objects.filter(Code="ERP_ADMIN").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("access", "0012_brand_transactional_email_templates"),
    ]

    operations = [
        migrations.RunPython(remove_erp_admin_application, migrations.RunPython.noop),
    ]
