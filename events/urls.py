from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"events", views.EventViewSet, basename="event")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "events/<slug:event_slug>/performances/",
        views.PerformanceViewSet.as_view({"get": "list"}),
        name="performance-list",
    ),
    path(
        "events/<slug:event_slug>/performances/<int:pk>/",
        views.PerformanceViewSet.as_view({"get": "retrieve"}),
        name="performance-detail",
    ),
]
