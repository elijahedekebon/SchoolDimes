from django.urls import path

from . import views

urlpatterns = [path("student", views.PortalView.as_view(), name="student-portal")]
