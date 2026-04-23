from django.db.models import Sum
from rest_framework import serializers

from .models import Event, Performance, SeatTier


class SeatTierSerializer(serializers.ModelSerializer):
    remaining = serializers.SerializerMethodField()

    class Meta:
        model = SeatTier
        fields = [
            "id",
            "code",
            "name",
            "capacity",
            "price_card",
            "price_cash",
            "sort_order",
            "is_staff_only",
            "remaining",
        ]

    def get_remaining(self, obj):
        confirmed_qty = getattr(obj, "_confirmed_qty", None)
        if confirmed_qty is not None:
            return obj.capacity - confirmed_qty
        # フォールバック（annotate されていない場合）
        from reservations.models import Reservation

        used = (
            Reservation.objects.filter(
                seat_tier=obj,
                status__in=["pending", "confirmed"],
            )
            .aggregate(total=Sum("quantity"))["total"]
            or 0
        )
        return obj.capacity - used


class PerformanceSerializer(serializers.ModelSerializer):
    seat_tiers = SeatTierSerializer(many=True, read_only=True)

    class Meta:
        model = Performance
        fields = [
            "id",
            "label",
            "starts_at",
            "open_at",
            "show_fanclub_question",
            "seat_tiers",
        ]


class EventSerializer(serializers.ModelSerializer):
    performances = PerformanceSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "venue_name",
            "venue_address",
            "cast",
            "flyer_image_url",
            "public_entry_enabled",
            "performances",
        ]


class EventListSerializer(serializers.ModelSerializer):
    """一覧用。performances はネストしない。"""

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "slug",
            "flyer_image_url",
        ]
