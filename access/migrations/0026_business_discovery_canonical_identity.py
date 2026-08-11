from django.db import migrations


PERMISSION_RENAMES = {
    "leadhunter.dashboard.read": "business_discovery.dashboard.read",
    "leadhunter.leads.read": "business_discovery.businesses.read",
    "leadhunter.leads.create": "business_discovery.businesses.create",
    "leadhunter.leads.update": "business_discovery.businesses.update",
    "leadhunter.leads.convert": "business_discovery.businesses.convert",
    "leadhunter.rules.read": "business_discovery.rules.read",
    "leadhunter.apify.read": "business_discovery.apify.read",
    "leadhunter.apify.execute": "business_discovery.apify.execute",
}


def rename_domain(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    ApplicationEmailSettings = apps.get_model("access", "ApplicationEmailSettings")
    Modules = apps.get_model("access", "Modules")
    Permissions = apps.get_model("access", "Permissions")

    application = Applications.objects.filter(Code="LEADHUNTER").first()
    if application:
        application.Code = "BUSINESS_DISCOVERY"
        application.Name = "Business Discovery"
        application.Description = "Descubrimiento y clasificación comercial de organizaciones."
        application.save(update_fields=["Code", "Name", "Description", "UpdatedAt"])
        ApplicationEmailSettings.objects.filter(ApplicationID=application).update(
            CommercialName="Business Discovery",
            SenderName="Business Discovery",
        )

    Modules.objects.filter(Code="LEADHUNTER_OPERATIONS").update(
        Code="BUSINESS_DISCOVERY_OPERATIONS",
        Name="Business Discovery Operations",
        Description="Operaciones autorizadas de Business Discovery.",
        Path="/admin/business-discovery",
    )
    for old_code, new_code in PERMISSION_RENAMES.items():
        Permissions.objects.filter(Code=old_code).update(Code=new_code)


def restore_legacy_names(apps, schema_editor):
    Applications = apps.get_model("access", "Applications")
    ApplicationEmailSettings = apps.get_model("access", "ApplicationEmailSettings")
    Modules = apps.get_model("access", "Modules")
    Permissions = apps.get_model("access", "Permissions")

    application = Applications.objects.filter(Code="BUSINESS_DISCOVERY").first()
    if application:
        application.Code = "LEADHUNTER"
        application.Name = "LeadHunter"
        application.save(update_fields=["Code", "Name", "UpdatedAt"])
        ApplicationEmailSettings.objects.filter(ApplicationID=application).update(
            CommercialName="LeadHunter",
            SenderName="LeadHunter",
        )
    Modules.objects.filter(Code="BUSINESS_DISCOVERY_OPERATIONS").update(
        Code="LEADHUNTER_OPERATIONS",
        Name="Leadhunter Operations",
        Path="/admin/prospectos",
    )
    for old_code, new_code in PERMISSION_RENAMES.items():
        Permissions.objects.filter(Code=new_code).update(Code=old_code)


class Migration(migrations.Migration):
    dependencies = [("access", "0025_register_supplier_profile_permissions")]
    operations = [migrations.RunPython(rename_domain, restore_legacy_names)]
