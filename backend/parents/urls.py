from django.urls import re_path

from .views import ParentDashboardView

urlpatterns = [re_path(r"^parent/dashboard/?$", ParentDashboardView.as_view(), name="parent-dashboard")]
