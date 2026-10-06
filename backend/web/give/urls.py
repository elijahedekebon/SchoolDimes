from django.urls import path

from . import views

urlpatterns = [
    path("give/<str:token>", views.GiveView.as_view(), name="give"),
    path("give/<str:token>/status/<str:reference>", views.GiveStatusView.as_view(), name="give-status"),
]
