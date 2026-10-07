from django.db import migrations


APPLICATION_CODE = "MEXINGSOF"
CAPTURE_PERMISSIONS = ("customer.read", "customer.write")


def add_mexingsof_customer_capture_permissions(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    ApplicationPermissions = apps.get_model("access", "ApplicationPermissions")
    Permissions = apps.get_model("access", "Permissions")

    application = Applications.objects.get(Code=APPLICATION_CODE)
    permissions = Permissions.objects.filter(Code__in=CAPTURE_PERMISSIONS)
    if set(permissions.values_list("Code", flat=True)) != set(CAPTURE_PERMISSIONS):
        raise RuntimeError("Customer capture permissions must be seeded before MEXINGSOF registration.")
    for permission in permissions:
        ApplicationPermissions.objects.get_or_create(
            ApplicationID=application,
            PermissionID=permission,
        )


def remove_mexingsof_customer_capture_permissions(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    ApplicationPermissions = apps.get_model("access", "ApplicationPermissions")
    Permissions = apps.get_model("access", "Permissions")

    application = Applications.objects.filter(Code=APPLICATION_CODE).first()
    if application is None:
        return
    permission_ids = Permissions.objects.filter(
        Code__in=CAPTURE_PERMISSIONS
    ).values_list("PermissionID", flat=True)
    ApplicationPermissions.objects.filter(
        ApplicationID=application,
        PermissionID_id__in=permission_ids,
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("access", "0041_merge_global_identity_and_permission_seeds")]

    operations = [
        migrations.RunPython(
            add_mexingsof_customer_capture_permissions,
            remove_mexingsof_customer_capture_permissions,
        )
    ]