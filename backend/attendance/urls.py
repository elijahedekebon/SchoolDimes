from django.urls import re_path

from core.routers import OptionalSlashRouter

from . import views

router = OptionalSlashRouter()
router.register(r"attendance", views.AttendanceViewSet, basename="attendance")

urlpatterns = [
    re_path(r"^attendance/tap/?$", views.AttendanceTapView.as_view(), name="attendance-tap"),
    re_path(r"^attendance/roster/?$", views.AttendanceRosterView.as_view(), name="attendance-roster"),  # Part 3
] + router.urls
