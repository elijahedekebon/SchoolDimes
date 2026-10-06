from django.urls import path

from . import views

urlpatterns = [
    path("platform", views.SchoolsView.as_view(), name="platform-schools"),
    path("platform/onboard", views.OnboardView.as_view(), name="platform-onboard"),
    path("platform/referrals", views.ReferralsView.as_view(), name="platform-referrals"),
    path("platform/referrals/new", views.NewReferralView.as_view(), name="platform-referral-new"),
    path("platform/referrals/<int:pk>/apply", views.ApplyReferralView.as_view(), name="platform-referral-apply"),
    path("platform/support", views.SupportView.as_view(), name="platform-support"),
    path("platform/support/transactions/<int:pk>", views.SupportTransactionView.as_view(), name="platform-transaction"),
    path("platform/payment-issues", views.PaymentIssuesView.as_view(), name="platform-payment-issues"),
    path("platform/payment-issues/webhooks/<int:pk>/mark-reviewed", views.MarkWebhookReviewedView.as_view(),
         name="platform-webhook-reviewed"),
    path("platform/audit-log", views.AuditLogView.as_view(), name="platform-audit-log"),
    path("platform/tips", views.TipsView.as_view(), name="platform-tips"),
    path("platform/tips/new", views.PlatformTipFormView.as_view(), name="platform-tip-new"),
    path("platform/tips/<int:pk>/edit", views.PlatformTipFormView.as_view(), name="platform-tip-edit"),
    path("platform/tips/<int:pk>/delete", views.PlatformTipDeleteView.as_view(), name="platform-tip-delete"),
]
