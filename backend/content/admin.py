from django.contrib import admin

from .models import FinancialLiteracyTip


@admin.register(FinancialLiteracyTip)
class FinancialLiteracyTipAdmin(admin.ModelAdmin):
    list_display = ["title", "language", "school", "target_age_range"]
    list_filter = ["language", "school"]
    search_fields = ["title", "body"]
