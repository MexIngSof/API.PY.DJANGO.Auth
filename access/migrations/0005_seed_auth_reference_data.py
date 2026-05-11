from django.db import migrations


APPLICATIONS = [
    ("TECNOTELEC", "Tecno Telec"),
    ("LEXNOVA", "LexNova"),
    ("JOBCRON", "JobCron"),
    ("IMAGRAFITY", "Imagrafity"),
]

ROLES = [
    "ADMIN",
    "MANAGER",
    "SALES_REP",
    "CASHIER",
    "TECHNICIAN",
    "WAREHOUSE_OPERATOR",
    "PURCHASING_AGENT",
    "ACCOUNTING",
    "CUSTOMER",
    "AUDITOR",
]

ACTIONS = [
    ("view", "View records"),
    ("create", "Create records"),
    ("update", "Update records"),
    ("delete", "Delete records"),
    ("approve", "Approve sensitive actions"),
    ("execute", "Execute operational actions"),
]


def seed_reference_data(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    Roles = apps.get_model("roles", "Roles")
    Actions = apps.get_model("access", "Actions")

    for code, name in APPLICATIONS:
        Applications.objects.update_or_create(
            Code=code,
            defaults={"Name": name, "IsActive": True},
        )

    for role_name in ROLES:
        Roles.objects.update_or_create(
            Name=role_name,
            defaults={"Description": f"Base role: {role_name}"},
        )

    for action_name, description in ACTIONS:
        Actions.objects.update_or_create(
            Name=action_name,
            defaults={"Description": description},
        )


class Migration(migrations.Migration):

    dependencies = [
        ("access", "0004_applications_userdevices_usersessions_refreshtokens_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_reference_data, migrations.RunPython.noop),
    ]
