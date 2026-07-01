from django.db import migrations


ROLE_LABELS = {
    "REFAPART_QUOTER": (
        "Cotizador RefaPart",
        "Gestiona solicitudes asignadas, contacta proveedores y registra cotizaciones.",
    ),
    "REFAPART_SUPPLIER_MANAGER": (
        "Gestor de proveedores RefaPart",
        "Administra proveedores, validaciones, respuestas y relacion operativa con proveedores.",
    ),
    "REFAPART_LOGISTICS": (
        "Logistica RefaPart",
        "Da seguimiento a envios, entregas, incidencias y coordinacion de pedidos.",
    ),
    "REFAPART_FINANCE": (
        "Finanzas RefaPart",
        "Consulta y opera datos financieros, reportes y seguimiento economico de RefaPart.",
    ),
    "REFAPART_SUPPORT": (
        "Soporte RefaPart",
        "Atiende usuarios, solicitudes de soporte y seguimiento operativo no critico.",
    ),
}


def update_display_names(apps, schema_editor):
    Roles = apps.get_model("roles", "Roles")
    for code, (display_name, description) in ROLE_LABELS.items():
        Roles.objects.filter(Name=code).update(
            DisplayName=display_name,
            Description=description,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("roles", "0006_roles_display_name"),
    ]

    operations = [
        migrations.RunPython(update_display_names, migrations.RunPython.noop),
    ]
