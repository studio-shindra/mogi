from django.contrib import admin
from django.urls import include, path

from reservations.views import link_ogp_html

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("events.urls")),
    path("api/", include("reservations.urls")),
    path("api/", include("payments.urls")),
    path("r/<str:token>/", link_ogp_html, name="link-ogp-html"),
]
