from django.contrib import admin

from .models import LedgerEntry, SavingsGoal, Wallet


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ["student", "wallet_type", "cached_balance", "school"]
    list_filter = ["wallet_type", "school"]


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ["wallet", "direction", "amount", "entry_type", "created_at"]
    list_filter = ["direction", "entry_type", "school"]
    readonly_fields = [f.name for f in LedgerEntry._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SavingsGoal)
class SavingsGoalAdmin(admin.ModelAdmin):
    list_display = ["goal_name", "wallet", "target_amount", "target_date"]
