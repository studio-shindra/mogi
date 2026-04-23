from django.db.models import Q, Sum, Value
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Event, Performance, SeatTier
from .serializers import EventListSerializer, EventSerializer, PerformanceSerializer


def seat_tiers_for_performance(request):
    """管理画面用: performance_id で席種を返す"""
    performance_id = request.GET.get("performance_id")
    if not performance_id:
        return JsonResponse([], safe=False)
    tiers = SeatTier.objects.filter(performance_id=performance_id).order_by("sort_order")
    data = [{"id": t.id, "name": t.name} for t in tiers]
    return JsonResponse(data, safe=False)


def _seat_tier_queryset(include_staff_only=False):
    """confirmed_qty を annotate した SeatTier queryset。
    include_staff_only=False なら is_staff_only=True を除外（公開API用）。
    """
    qs = SeatTier.objects.annotate(
        _confirmed_qty=Coalesce(
            Sum(
                "reservations__quantity",
                filter=Q(reservations__status__in=["pending", "confirmed"]),
            ),
            Value(0),
        ),
    )
    if not include_staff_only:
        qs = qs.filter(is_staff_only=False)
    return qs


def _annotate_seat_tiers(qs, include_staff_only=False):
    """Event queryset に performances__seat_tiers の Prefetch を付与"""
    from django.db.models import Prefetch

    return qs.prefetch_related(
        Prefetch(
            "performances__seat_tiers",
            queryset=_seat_tier_queryset(include_staff_only=include_staff_only),
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

        return Performance.objects.filter(
            event__slug=self.kwargs["event_slug"],
        ).prefetch_related(
            Prefetch(
                "seat_tiers",
                queryset=_seat_tier_queryset(include_staff_only=False),
            ),
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def staff_event_detail(request, slug):
    """GET /api/staff/event-detail/<slug>/
    スタッフ専用席種（is_staff_only=True）も含めて返す。
    """
    if not (request.user.is_staff or request.user.is_superuser):
        return Response({"detail": "スタッフ権限が必要です"}, status=403)

    qs = _annotate_seat_tiers(Event.objects.all(), include_staff_only=True)
    event = get_object_or_404(qs, slug=slug)
    return Response(EventSerializer(event).data)
