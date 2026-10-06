from django.urls import path

from . import views, views_students as d

urlpatterns = [
    # B
    path("school", views.OverviewView.as_view(), name="school-overview"),
    path("school/sales", views.SalesView.as_view(), name="school-sales"),
    path("school/sales/transactions/<int:pk>", views.TransactionDrawerView.as_view(), name="school-transaction"),
    path("school/reconciliation", views.ReconciliationView.as_view(), name="school-reconciliation"),
    path("school/reconciliation/export", views.ReconciliationExportView.as_view(), name="school-reconciliation-csv"),
    path("school/shortfalls", views.ShortfallsView.as_view(), name="school-shortfalls"),
    path("school/shortfalls/<int:pk>/resolve", views.ResolveReviewView.as_view(), name="school-shortfall-resolve"),
    path("school/_picker/students", views.StudentPickerView.as_view(), name="school-student-picker"),
    # C
    path("school/analytics", views.AnalyticsView.as_view(), name="school-analytics"),
    # D
    path("school/students", d.StudentsView.as_view(), name="school-students"),
    path("school/students/new", d.StudentFormView.as_view(), name="school-student-new"),
    path("school/students/<int:pk>", d.StudentDetailView.as_view(), name="school-student"),
    path("school/students/<int:pk>/edit", d.StudentFormView.as_view(), name="school-student-edit"),
    path("school/students/<int:pk>/guardian-lookup", d.GuardianLookupView.as_view(), name="school-guardian-lookup"),
    path("school/students/<int:pk>/link-guardian", d.LinkGuardianView.as_view(), name="school-guardian-link"),
    path("school/students/<int:pk>/portal/create", d.PortalCreateView.as_view(), name="school-portal-create"),
    path("school/students/<int:pk>/portal/remove", d.PortalRemoveView.as_view(), name="school-portal-remove"),
    path("school/guardians", d.GuardiansView.as_view(), name="school-guardians"),
    path("school/guardians/<int:pk>/unlink", d.UnlinkGuardianView.as_view(), name="school-guardian-unlink"),
    path("school/guardians/kyc/<int:pk>/review", d.ReviewKycView.as_view(), name="school-kyc-review"),
    path("school/cards", d.CardsView.as_view(), name="school-cards"),
    path("school/cards/issue", d.IssueCardView.as_view(), name="school-card-issue"),
    path("school/cards/uid-preview", d.CardUidPreviewView.as_view(), name="school-card-uid-preview"),
    path("school/cards/<int:pk>/reissue", d.IssueCardView.as_view(), name="school-card-reissue"),
    path("school/cards/<int:pk>/freeze", d.FreezeCardView.as_view(), name="school-card-freeze"),
    path("school/cards/<int:pk>/unfreeze", d.UnfreezeCardView.as_view(), name="school-card-unfreeze"),
    path("school/cards/<int:pk>/mark-lost", d.MarkLostView.as_view(), name="school-card-lost"),
    path("school/cards/<int:pk>/reset-pin", d.ResetPinView.as_view(), name="school-card-reset-pin"),
]
