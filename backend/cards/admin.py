from django.contrib import admin

from .models import Card


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ["card_uid", "student", "school", "status", "biometric_enrolled"]
    list_filter = ["status", "school"]
    search_fields = ["card_uid"]
    readonly_fields = ["pin_hash"]
