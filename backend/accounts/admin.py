from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import GuardianVerification, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    ordering = ["email"]
    list_display = ["email", "role", "school", "is_active", "is_staff"]
    list_filter = ["role", "school", "is_active"]
    search_fields = ["email", "full_name"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Profile",
            {"fields": ("full_name", "role", "school", "preferred_language", "phone_number")},
        ),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "role", "password1", "password2"),
            },
        ),
    )


@admin.register(GuardianVerification)
class GuardianVerificationAdmin(admin.ModelAdmin):
    list_display = ["parent", "full_name", "status", "verified_at"]
    list_filter = ["status"]
