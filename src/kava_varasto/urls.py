from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path

from . import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path("api/accounts/", include("kava_varasto.accounts.urls")),
    path("api/inventory/", include("kava_varasto.inventory.urls")),
    path("api/loans/", include("kava_varasto.loans.urls")),
    # Client-side routes handled by the SPA; keep this last so it doesn't
    # shadow admin/i18n/api/static/media.
    re_path(r"^(?!admin/|i18n/|api/|static/|media/).*$", views.spa, name="spa"),
]

# In production the reverse proxy serves MEDIA_ROOT; static() is a no-op there.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
