from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^analytics/sales-summary/?$", views.SalesSummaryView.as_view(), name="analytics-sales-summary"),
    re_path(r"^analytics/best-sellers/?$", views.BestSellersView.as_view(), name="analytics-best-sellers"),
    re_path(r"^analytics/peak-hours/?$", views.PeakHoursView.as_view(), name="analytics-peak-hours"),
    re_path(r"^analytics/category-breakdown/?$", views.CategoryBreakdownView.as_view(), name="analytics-category-breakdown"),
    re_path(r"^analytics/students/(?P<student_id>\d+)/spending/?$", views.StudentSpendingView.as_view(),
            name="analytics-student-spending"),
    re_path(r"^analytics/reconciliation/?$", views.ReconciliationView.as_view(), name="analytics-reconciliation"),
]
