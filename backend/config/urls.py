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
    path("api/v1/", include("disputes.urls")),
    path("api/v1/", include("notifications.urls")),
    path("api/v1/", include("privacy.urls")),
    path("api/v1/", include("analytics.urls")),
    # Part 4A
    path("api/v1/", include("backoffice.urls")),
    path("api/v1/", include("parents.urls")),
    # Web surfaces (Django templates + HTMX), same paths as the old Next.js app
    path("", include("web.core.urls")),
    path("", include("web.school.urls")),
    path("", include("web.platform.urls")),
    path("", include("web.student.urls")),
    path("", include("web.give.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
