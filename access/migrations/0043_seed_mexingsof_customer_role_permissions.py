from django.db import migrations, models
import django.db.models.deletion


APPLICATION_CODE = "MEXINGSOF"
ROLE_NAME = "CUSTOMER"
PERMISSION_CODES = ("customer.read", "customer.write")


def seed_mexingsof_customer_role_permissions(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    ApplicationPermissions = apps.get_model("access", "ApplicationPermissions")
    ApplicationRolePermissions = apps.get_model("access", "ApplicationRolePermissions")
    ApplicationRoles = apps.get_model("access", "ApplicationRoles")
    Permissions = apps.get_model("access", "Permissions")
    Roles = apps.get_model("roles", "Roles")

    application = Applications.objects.get(Code=APPLICATION_CODE)
    role = Roles.objects.get(Name=ROLE_NAME)
    if not ApplicationRoles.objects.filter(
        ApplicationID=application,
        RoleID=role,
    ).exists():
        raise RuntimeError("MEXINGSOF CUSTOMER must be mapped before its permissions are seeded.")

    permissions = Permissions.objects.filter(Code__in=PERMISSION_CODES)
    if set(permissions.values_list("Code", flat=True)) != set(PERMISSION_CODES):
        raise RuntimeError("Customer capture permissions must exist before role assignment.")
    if set(
        ApplicationPermissions.objects.filter(
            ApplicationID=application,
            PermissionID__in=permissions,
        ).values_list("PermissionID__Code", flat=True)
    ) != set(PERMISSION_CODES):
        raise RuntimeError("Customer capture permissions must be registered for MEXINGSOF.")

    for permission in permissions:
        ApplicationRolePermissions.objects.get_or_create(
            ApplicationID=application,
            RoleID=role,
            PermissionID=permission,
        )


def unseed_mexingsof_customer_role_permissions(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    ApplicationRolePermissions = apps.get_model("access", "ApplicationRolePermissions")
    Permissions = apps.get_model("access", "Permissions")
    Roles = apps.get_model("roles", "Roles")

    application = Applications.objects.filter(Code=APPLICATION_CODE).first()
    role = Roles.objects.filter(Name=ROLE_NAME).first()
    if application is None or role is None:
        return
    permission_ids = Permissions.objects.filter(
        Code__in=PERMISSION_CODES,
    ).values_list("PermissionID", flat=True)
    ApplicationRolePermissions.objects.filter(
        ApplicationID=application,
        RoleID=role,
        PermissionID_id__in=permission_ids,
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("access", "0042_seed_mexingsof_customer_capture_permissions")]

    operations = [
        migrations.CreateModel(
            name="ApplicationRolePermissions",
            fields=[
                (
                    "id",
                    models.BigAutoField(db_column="Id", primary_key=True, serialize=False),
                ),
                (
                    "CreatedAt",
                    models.DateTimeField(auto_now_add=True, db_column="CreatedAt"),
                ),
                (
                    "UpdatedAt",
                    models.DateTimeField(auto_now=True, db_column="UpdatedAt"),
                ),
                (
                    "ApplicationID",
                    models.ForeignKey(
                        db_column="ApplicationId",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="access.applications",
                    ),
                ),
                (
                    "PermissionID",
                    models.ForeignKey(
                        db_column="PermissionId",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="access.permissions",
                    ),
                ),
                (
                    "RoleID",
                    models.ForeignKey(
                        db_column="RoleId",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="roles.roles",
                    ),
                ),
            ],
            options={
                "db_table": '"Auth"."ApplicationRolePermissions"',
                "unique_together": {("ApplicationID", "RoleID", "PermissionID")},
            },
        ),
        migrations.RunPython(
            seed_mexingsof_customer_role_permissions,
            unseed_mexingsof_customer_role_permissions,
        ),
    ]
