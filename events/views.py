from django.db.models import Q, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import Event, Performance
from .serializers import EventListSerializer, EventSerializer, PerformanceSerializer


def _annotate_seat_tiers(qs):
    """SeatTier に confirmed_qty を annotate する Prefetch を返す"""
    from django.db.models import Prefetch
    from .models import SeatTier

    return qs.prefetch_related(
        Prefetch(
            "performances__seat_tiers",
            queryset=SeatTier.objects.annotate(
                _confirmed_qty=Coalesce(
                    Sum(
                        "reservations__quantity",
                        filter=Q(
                            reservations__status__in=["pending", "confirmed"],
                        ),
                    ),
                    Value(0),
                ),
            ),
        ),
    )


class EventViewSet(viewsets.ReadOnlyModelViewSet):
    """作品の一覧・詳細（公開API）"""

    permission_classes = [AllowAny]
    lookup_field = "slug"

    def get_queryset(self):
        qs = Event.objects.all()
        if self.action == "retrieve":
            qs = _annotate_seat_tiers(qs)
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return EventListSerializer
        return EventSerializer


class PerformanceViewSet(viewsets.ReadOnlyModelViewSet):
    """公演の一覧・詳細（公開API）"""

    permission_classes = [AllowAny]
    serializer_class = PerformanceSerializer

    def get_queryset(self):
        from django.db.models import Prefetch
        from .models import SeatTier

        return Performance.objects.filter(
            event__slug=self.kwargs["event_slug"],
        ).prefetch_related(
            Prefetch(
                "seat_tiers",
                queryset=SeatTier.objects.annotate(
                    _confirmed_qty=Coalesce(
                        Sum(
                            "reservations__quantity",
                            filter=Q(
                                reservations__status__in=["pending", "confirmed"],
                            ),
                        ),
                        Value(0),
                    ),
                ),
            ),
        )
