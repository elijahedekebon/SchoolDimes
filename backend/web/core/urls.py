from django.urls import path

from . import views

urlpatterns = [
    path("", views.HomeRedirectView.as_view(), name="web-home"),
    path("login", views.LoginView.as_view(), name="web-login"),
    path("logout", views.LogoutView.as_view(), name="web-logout"),
    path("locale", views.LocaleView.as_view(), name="web-locale"),
    path("notifications/bell", views.NotificationBellView.as_view(), name="web-bell"),
    path("notifications/<int:pk>/read", views.NotificationReadView.as_view(), name="web-bell-read"),
    path("notifications/read-all", views.NotificationReadAllView.as_view(), name="web-bell-read-all"),
]
