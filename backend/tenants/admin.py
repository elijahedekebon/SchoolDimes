from django.contrib import admin

from .models import School, SchoolReferral


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at"]
    search_fields = ["name"]


@admin.register(SchoolReferral)
class SchoolReferralAdmin(admin.ModelAdmin):
    list_display = ["referring_school", "referred_school", "status", "reward_applied"]
    list_filter = ["status", "reward_applied"]
