from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("api/v1/", include("main.urls")),
    path("api/dashboard/", include("dashboard.urls")),
    path("explorer-api/", include("explorer.urls")),  # WhiteFlag Explorer - public read-only API
    path("api/admin/", admin.site.urls),
    # path("api/silk/", include("silk.urls", namespace="silk")),  # DISABLED: Silk removed
]
