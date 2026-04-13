from datetime import timedelta

from django.db.models import Q, Sum
from django.utils import timezone
from rest_framework import serializers

from events.models import SeatTier
from .models import Reservation


class ReservationPerformanceSerializer(serializers.Serializer):
    """予約確認ページ用の公演情報（軽量）"""
    id = serializers.IntegerField()
    label = serializers.CharField()
    starts_at = serializers.DateTimeField()
    event_title = serializers.SerializerMethodField()
    venue_name = serializers.SerializerMethodField()

    def get_event_title(self, obj):
        return obj.event.title

    def get_venue_name(self, obj):
        return obj.event.venue_name


class ReservationSeatTierSerializer(serializers.Serializer):
    """予約確認ページ用の席種情報（軽量）"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    code = serializers.CharField()


class AvailableSeatTierSerializer(serializers.Serializer):
    """draft 予約完成ページ用の席種選択肢"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    code = serializers.CharField()
    price_card = serializers.IntegerField()
    price_cash = serializers.IntegerField()
    remaining = serializers.SerializerMethodField()

    def get_remaining(self, obj):
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


# ---- 予約作成 ----

class ReservationCreateSerializer(serializers.Serializer):
    performance_id = serializers.IntegerField()
    seat_tier_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, max_value=10)
    reservation_type = serializers.ChoiceField(choices=["card", "cash", "invite"])
    guest_name = serializers.CharField(max_length=200)
    guest_email = serializers.EmailField(required=False, allow_blank=True, default="")
    guest_phone = serializers.CharField(max_length=30, required=False, allow_blank=True, default="")

    def validate(self, data):
        from events.models import Performance

        # Performance 存在チェック
        try:
            performance = Performance.objects.select_related("event").get(
                pk=data["performance_id"],
            )
        except Performance.DoesNotExist:
            raise serializers.ValidationError({"performance_id": "公演が見つかりません"})

        # SeatTier 存在 + 整合性チェック
        try:
            seat_tier = SeatTier.objects.get(pk=data["seat_tier_id"])
        except SeatTier.DoesNotExist:
            raise serializers.ValidationError({"seat_tier_id": "席種が見つかりません"})

        if seat_tier.performance_id != performance.pk:
            raise serializers.ValidationError(
                {"seat_tier_id": "この席種は指定した公演に属していません"}
            )

        # invite は rear のみ
        if data["reservation_type"] == "invite" and seat_tier.code != "rear":
            raise serializers.ValidationError(
                {"seat_tier_id": "招待は後方席のみ指定できます"}
            )

        # card はメール必須
        if data["reservation_type"] == "card" and not data.get("guest_email"):
            raise serializers.ValidationError(
                {"guest_email": "カード決済の場合はメールアドレスが必要です"}
            )

        # 在庫チェック
        confirmed_qty = (
            Reservation.objects.filter(
                seat_tier=seat_tier,
                status__in=["pending", "confirmed"],
            )
            .aggregate(total=Sum("quantity"))["total"]
            or 0
        )
        remaining = seat_tier.capacity - confirmed_qty
        if data["quantity"] > remaining:
            raise serializers.ValidationError(
                {"quantity": f"残席が不足しています。{seat_tier.name}: 残り{remaining}枚"}
            )

        data["_performance"] = performance
        data["_seat_tier"] = seat_tier
        return data

    def create(self, validated_data):
        performance = validated_data.pop("_performance")
        seat_tier = validated_data.pop("_seat_tier")
        rtype = validated_data["reservation_type"]

        if rtype == "card":
            status = Reservation.Status.PENDING
            payment_status = Reservation.PaymentStatus.UNPAID
        elif rtype == "cash":
            status = Reservation.Status.CONFIRMED
            payment_status = Reservation.PaymentStatus.UNPAID
        elif rtype == "invite":
            status = Reservation.Status.CONFIRMED
            payment_status = Reservation.PaymentStatus.PAID

        return Reservation.objects.create(
            performance=performance,
            seat_tier=seat_tier,
            quantity=validated_data["quantity"],
            reservation_type=rtype,
            status=status,
            payment_status=payment_status,
            guest_name=validated_data["guest_name"],
            guest_email=validated_data.get("guest_email", ""),
            guest_phone=validated_data.get("guest_phone", ""),
        )


# ---- 予約レスポンス ----

class ReservationDetailSerializer(serializers.ModelSerializer):
    performance = ReservationPerformanceSerializer(read_only=True)
    seat_tier = ReservationSeatTierSerializer(read_only=True, allow_null=True)
    can_self_checkin = serializers.SerializerMethodField()
    checkin_opens_at = serializers.SerializerMethodField()
    available_seat_tiers = serializers.SerializerMethodField()

    class Meta:
        model = Reservation
        fields = [
            "id",
            "token",
            "guest_name",
            "guest_email",
            "guest_phone",
            "performance",
            "seat_tier",
            "quantity",
            "reservation_type",
            "status",
            "payment_status",
            "checked_in",
            "can_self_checkin",
            "checkin_opens_at",
            "available_seat_tiers",
            "created_at",
        ]

    def get_available_seat_tiers(self, obj):
        if obj.status != "draft":
            return None
        tiers = obj.performance.seat_tiers.order_by("sort_order")
        return AvailableSeatTierSerializer(tiers, many=True).data

    def get_can_self_checkin(self, obj):
        if obj.checked_in:
            return False
        if obj.reservation_type == "cash":
            return False
        if obj.status != "confirmed" or obj.payment_status != "paid":
            return False
        now = timezone.now()
        opens_at = obj.performance.starts_at - timedelta(hours=1)
        return now >= opens_at

    def get_checkin_opens_at(self, obj):
        return obj.performance.starts_at - timedelta(hours=1)


# ---- 受付用一覧 ----

class StaffReservationSerializer(serializers.ModelSerializer):
    performance = ReservationPerformanceSerializer(read_only=True)
    seat_tier = ReservationSeatTierSerializer(read_only=True)

    class Meta:
        model = Reservation
        fields = [
            "id",
            "token",
            "guest_name",
            "guest_email",
            "guest_phone",
            "performance",
            "seat_tier",
            "quantity",
            "reservation_type",
            "status",
            "payment_status",
            "checked_in",
            "memo",
        ]


# ---- 当日券 ----

class WalkInCreateSerializer(serializers.Serializer):
    performance_id = serializers.IntegerField()
    seat_tier_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, max_value=10)
    guest_name = serializers.CharField(max_length=200)
    guest_phone = serializers.CharField(max_length=30, required=False, allow_blank=True, default="")
    memo = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, data):
        from events.models import Performance

        try:
            performance = Performance.objects.select_related("event").get(
                pk=data["performance_id"],
            )
        except Performance.DoesNotExist:
            raise serializers.ValidationError({"performance_id": "公演が見つかりません"})

        try:
            seat_tier = SeatTier.objects.get(pk=data["seat_tier_id"])
        except SeatTier.DoesNotExist:
            raise serializers.ValidationError({"seat_tier_id": "席種が見つかりません"})

        if seat_tier.performance_id != performance.pk:
            raise serializers.ValidationError(
                {"seat_tier_id": "この席種は指定した公演に属していません"}
            )

        # 在庫チェック
        confirmed_qty = (
            Reservation.objects.filter(
                seat_tier=seat_tier,
                status__in=["pending", "confirmed"],
            )
            .aggregate(total=Sum("quantity"))["total"]
            or 0
        )
        remaining = seat_tier.capacity - confirmed_qty
        if data["quantity"] > remaining:
            raise serializers.ValidationError(
                {"quantity": f"残席が不足しています。{seat_tier.name}: 残り{remaining}枚"}
            )

        data["_performance"] = performance
        data["_seat_tier"] = seat_tier
        return data

    def create(self, validated_data):
        performance = validated_data.pop("_performance")
        seat_tier = validated_data.pop("_seat_tier")

        return Reservation.objects.create(
            performance=performance,
            seat_tier=seat_tier,
            quantity=validated_data["quantity"],
            reservation_type=Reservation.ReservationType.CASH,
            status=Reservation.Status.CONFIRMED,
            payment_status=Reservation.PaymentStatus.PAID,
            guest_name=validated_data["guest_name"],
            guest_phone=validated_data.get("guest_phone", ""),
            memo=validated_data.get("memo", ""),
        )


# ---- 仮受付 → 予約完成 ----

class CompleteReservationSerializer(serializers.Serializer):
    """draft 予約を完成させる（席種 + 支払方法を確定）"""
    seat_tier_id = serializers.IntegerField()
    reservation_type = serializers.ChoiceField(choices=["card", "cash"])
    guest_email = serializers.EmailField(required=False, allow_blank=True, default="")

    def validate(self, data):
        reservation = self.context["reservation"]

        if reservation.status != "draft":
            raise serializers.ValidationError(
                {"status": "この予約はすでに確定処理が完了しています"}
            )

        # SeatTier 存在 + 整合性チェック
        try:
            seat_tier = SeatTier.objects.get(pk=data["seat_tier_id"])
        except SeatTier.DoesNotExist:
            raise serializers.ValidationError({"seat_tier_id": "席種が見つかりません"})

        if seat_tier.performance_id != reservation.performance_id:
            raise serializers.ValidationError(
                {"seat_tier_id": "この席種は指定した公演に属していません"}
            )

        # card はメール必須
        if data["reservation_type"] == "card" and not data.get("guest_email") and not reservation.guest_email:
            raise serializers.ValidationError(
                {"guest_email": "カード決済の場合はメールアドレスが必要です"}
            )

        # 在庫チェック
        confirmed_qty = (
            Reservation.objects.filter(
                seat_tier=seat_tier,
                status__in=["pending", "confirmed"],
            )
            .aggregate(total=Sum("quantity"))["total"]
            or 0
        )
        remaining = seat_tier.capacity - confirmed_qty
        if reservation.quantity > remaining:
            raise serializers.ValidationError(
                {"seat_tier_id": f"残席が不足しています。{seat_tier.name}: 残り{remaining}枚"}
            )

        data["_seat_tier"] = seat_tier
        return data

    def save(self):
        reservation = self.context["reservation"]
        seat_tier = self.validated_data["_seat_tier"]
        rtype = self.validated_data["reservation_type"]

        reservation.seat_tier = seat_tier
        reservation.reservation_type = rtype

        # メールアドレスが送られてきた場合は更新
        guest_email = self.validated_data.get("guest_email")
        if guest_email:
            reservation.guest_email = guest_email

        if rtype == "card":
            reservation.status = Reservation.Status.PENDING
            reservation.payment_status = Reservation.PaymentStatus.UNPAID
        elif rtype == "cash":
            reservation.status = Reservation.Status.CONFIRMED
            reservation.payment_status = Reservation.PaymentStatus.UNPAID

        reservation.save(update_fields=[
            "seat_tier", "reservation_type", "status",
            "payment_status", "guest_email", "updated_at",
        ])
        return reservation
