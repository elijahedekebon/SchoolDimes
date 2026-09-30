from django.contrib import admin

from .models import Contributor, Deposit, GiftVoucher, Payout, RecurringTopUp, StudentTopUpLink, UnmatchedWebhook


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    list_display = ["reference", "purpose", "amount", "channel", "status", "school", "created_at"]
    list_filter = ["status", "purpose", "channel", "school"]
    search_fields = ["reference", "aggregator_ref", "idempotency_key"]
    readonly_fields = [f.name for f in Deposit._meta.fields]


@admin.register(UnmatchedWebhook)
class UnmatchedWebhookAdmin(admin.ModelAdmin):
    list_display = ["reference", "reason", "reviewed", "received_at"]
    list_filter = ["reason", "reviewed"]


admin.site.register([Contributor, StudentTopUpLink, GiftVoucher, RecurringTopUp, Payout])
