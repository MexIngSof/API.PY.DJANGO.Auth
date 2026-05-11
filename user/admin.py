from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from user.models import UserAccount


@admin.register(UserAccount)
class UserAccountAdmin(UserAdmin):
    model = UserAccount
    ordering = ("email",)
    list_display = ("email", "first_name", "last_name", "idApp", "is_active", "is_staff")
    list_filter = ("is_active", "is_staff", "is_superuser", "idApp")
    search_fields = ("email", "first_name", "last_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "idApp")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "idApp",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                ),
            },
        ),
    )
