from django.db import migrations, models


ROLE_LABELS = {
    "JOBCRON_SUPER_ADMIN": (
        "Super administrador JobCron",
        "Control total del centro administrativo JobCron, usuarios, roles, permisos y configuracion global.",
    ),
    "JOBCRON_PLATFORM_ADMIN": (
        "Administrador de plataforma JobCron",
        "Administra usuarios, roles, permisos, modulos y configuracion operativa del ecosistema.",
    ),
    "JOBCRON_SUPPORT_ADMIN": (
        "Soporte operativo JobCron",
        "Consulta usuarios, roles y permisos para soporte sin operar configuracion critica.",
    ),
    "REFAPART_ADMIN": (
        "Administrador RefaPart",
        "Administra usuarios, catalogo, proveedores, solicitudes, cotizaciones y operacion de RefaPart.",
    ),
    "REFAPART_OPERATOR": (
        "Operador RefaPart",
        "Gestiona solicitudes, cotizaciones y seguimiento operativo de RefaPart.",
    ),
    "REFAPART_SUPPLIER": (
        "Proveedor RefaPart",
        "Responde solicitudes, publica disponibilidad y da seguimiento a piezas asignadas.",
    ),
    "CUSTOMER": (
        "Cliente",
        "Usuario cliente de aplicaciones comerciales con acceso a sus solicitudes, pedidos y perfil.",
    ),
}


def seed_role_display_names(apps, schema_editor):
    Roles = apps.get_model("roles", "Roles")
    for code, (display_name, description) in ROLE_LABELS.items():
        Roles.objects.filter(Name=code).update(
            DisplayName=display_name,
            Description=description,
        )
    for role in Roles.objects.filter(DisplayName__isnull=True):
        role.DisplayName = role.Name.replace("_", " ").title()
        role.save(update_fields=["DisplayName"])


class Migration(migrations.Migration):

    dependencies = [
        ("roles", "0005_alter_userroles_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="roles",
            name="DisplayName",
            field=models.CharField(blank=True, db_column="DisplayName", max_length=160, null=True),
        ),
        migrations.RunPython(seed_role_display_names, migrations.RunPython.noop),
    ]
