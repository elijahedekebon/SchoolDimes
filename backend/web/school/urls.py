from django.urls import path

from . import views

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
]
