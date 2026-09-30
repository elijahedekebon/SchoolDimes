from django.urls import re_path

from core.routers import OptionalSlashRouter

from . import views

router = OptionalSlashRouter()
router.register(r"privacy/data-requests", views.DataRequestViewSet, basename="datarequest")

urlpatterns = [re_path(r"^privacy/my-data/?$", views.MyDataView.as_view(), name="privacy-my-data")] + router.urls
