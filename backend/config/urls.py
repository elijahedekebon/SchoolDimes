from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("accounts.urls")),
    path("api/v1/", include("tenants.urls")),
    path("api/v1/", include("students.urls")),
    path("api/v1/", include("cards.urls")),
    path("api/v1/", include("wallets.urls")),
    path("api/v1/", include("content.urls")),
    # Part 2
    path("api/v1/", include("payments.urls")),
    path("api/v1/", include("pooled_funds.urls")),
    path("api/v1/", include("policies.urls")),
    path("api/v1/", include("pos.urls")),
    path("api/v1/", include("fees.urls")),
    path("api/v1/", include("attendance.urls")),
    path("api/v1/", include("merchants.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
