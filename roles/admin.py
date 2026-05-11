from django.contrib import admin

from roles.models import Roles, UserRoles


@admin.register(Roles)
class RolesAdmin(admin.ModelAdmin):
    list_display = ("Name", "Description", "UpdatedAt")
    search_fields = ("Name", "Description")


@admin.register(UserRoles)
class UserRolesAdmin(admin.ModelAdmin):
    list_display = ("UserID", "RoleID", "UpdatedAt")
    list_filter = ("RoleID",)
    search_fields = ("UserID__email", "RoleID__Name")
