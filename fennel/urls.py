from django.contrib import admin
from django.urls import include, path
from django.conf import settings

urlpatterns = [
    path("api/v1/", include("main.urls")),
    path("api/dashboard/", include("dashboard.urls")),
    path("api/admin/", admin.site.urls),
]

# Only include Silk URLs in debug mode
if settings.DEBUG:
    urlpatterns.append(path("api/silk/", include("silk.urls", namespace="silk")))
