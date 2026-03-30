from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("events.urls")),
    path("api/", include("reservations.urls")),
    path("api/", include("payments.urls")),
]
