from django.db.models import Sum
from rest_framework import serializers

from events.models import SeatTier
from .models import AccessLink, Reservation


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
    capacity = serializers.IntegerField(required=False)
    price_card = serializers.IntegerField(required=False)
    price_cash = serializers.IntegerField(required=False)


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
    quantity = serializers.IntegerField(min_value=1, max_value=4)
    reservation_type = serializers.ChoiceField(
        choices=["cash", "invite"],
        required=False,
        default="cash",
    )
    guest_name = serializers.CharField(max_length=200)
    guest_email = serializers.EmailField(required=False, allow_blank=True, default="")
    guest_phone = serializers.CharField(max_length=30, required=False, allow_blank=True, default="")
    link_token = serializers.CharField(required=False, allow_blank=True, default="")

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

        # invite は rear のみ（現行ルール温存）
        if data.get("reservation_type") == "invite" and seat_tier.code != "rear":
            raise serializers.ValidationError(
                {"seat_tier_id": "招待は後方席のみ指定できます"}
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

        # link_token 検証（任意）
        link = None
        link_token = (data.get("link_token") or "").strip()
        if link_token:
            try:
                link = AccessLink.objects.get(token=link_token)
            except AccessLink.DoesNotExist:
                raise serializers.ValidationError({"link_token": "無効なリンクです"})
            if not link.is_active:
                raise serializers.ValidationError({"link_token": "このリンクは無効です"})
            if link.mode != AccessLink.Mode.RESERVATION:
                raise serializers.ValidationError({"link_token": "このリンクは予約用ではありません"})
            if link.event_id != performance.event_id:
                raise serializers.ValidationError({"link_token": "リンクの作品と一致しません"})

        data["_performance"] = performance
        data["_seat_tier"] = seat_tier
        data["_link"] = link
        return data

    def create(self, validated_data):
        performance = validated_data.pop("_performance")
        seat_tier = validated_data.pop("_seat_tier")
        link = validated_data.pop("_link", None)
        rtype = validated_data.get("reservation_type", "cash")

        if rtype == "invite":
            status = Reservation.Status.CONFIRMED
            payment_status = Reservation.PaymentStatus.PAID
        else:
            status = Reservation.Status.CONFIRMED
            payment_status = Reservation.PaymentStatus.UNPAID

        # link があればその sales_channel、なければ general
        sales_channel = link.sales_channel if link else Reservation.SalesChannel.GENERAL

        return Reservation.objects.create(
            performance=performance,
            seat_tier=seat_tier,
            quantity=validated_data["quantity"],
            reservation_type=rtype,
            sales_channel=sales_channel,
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
    sales_channel_display = serializers.CharField(source="get_sales_channel_display", read_only=True)

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
            "sales_channel",
            "sales_channel_display",
            "status",
            "payment_status",
            "checked_in",
            "can_self_checkin",
            "checkin_opens_at",
            "available_seat_tiers",
            "created_at",
        ]

    def get_available_seat_tiers(self, obj):
        # Phase A: draft 完成フロー停止
        return None

    def get_can_self_checkin(self, obj):
        # Phase A: セルフチェックイン全廃（当日精算前提のため）
        return False

    def get_checkin_opens_at(self, obj):
        return None


# ---- 受付用一覧 ----

class StaffReservationSerializer(serializers.ModelSerializer):
    performance = ReservationPerformanceSerializer(read_only=True)
    seat_tier = ReservationSeatTierSerializer(read_only=True)
    sales_channel_display = serializers.CharField(source="get_sales_channel_display", read_only=True)

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
            "sales_channel",
            "sales_channel_display",
            "status",
            "payment_status",
            "checked_in",
            "memo",
            "is_fanclub_member",
        ]


# ---- 当日券 ----

class WalkInCreateSerializer(serializers.Serializer):
    performance_id = serializers.IntegerField()
    seat_tier_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, max_value=4)
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
            sales_channel=Reservation.SalesChannel.WALK_IN,
            status=Reservation.Status.CONFIRMED,
            payment_status=Reservation.PaymentStatus.PAID,
            guest_name=validated_data["guest_name"],
            guest_phone=validated_data.get("guest_phone", ""),
            memo=validated_data.get("memo", ""),
        )


# ---- 仮受付 → 予約完成 ----

class CompleteReservationSerializer(serializers.Serializer):
    """draft 予約を完成させる（Phase A で休眠。将来の席種後選択フロー用に温存）"""
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


# ---- 応募受付（二次先行） ----

class ApplicationCreateSerializer(serializers.Serializer):
    """公開URL経由の応募フォーム。Reservation を status=applied で作成する。"""
    performance_id = serializers.IntegerField()
    first_choice_seat_tier_id = serializers.IntegerField()
    second_choice_seat_tier_id = serializers.IntegerField(
        required=False, allow_null=True, default=None,
    )
    allow_any_seat = serializers.BooleanField(required=False, default=False)
    quantity = serializers.IntegerField(min_value=1, max_value=4)
    guest_name = serializers.CharField(max_length=200)
    guest_email = serializers.EmailField(required=False, allow_blank=True, default="")
    guest_phone = serializers.CharField(max_length=30, required=False, allow_blank=True, default="")
    memo = serializers.CharField(required=False, allow_blank=True, default="")
    link_token = serializers.CharField(required=False, allow_blank=True, default="")
    is_fanclub_member = serializers.BooleanField(required=False, default=False)

    def validate(self, data):
        from events.models import Performance

        try:
            performance = Performance.objects.select_related("event").get(
                pk=data["performance_id"],
            )
        except Performance.DoesNotExist:
            raise serializers.ValidationError({"performance_id": "公演が見つかりません"})

        try:
            first_tier = SeatTier.objects.get(pk=data["first_choice_seat_tier_id"])
        except SeatTier.DoesNotExist:
            raise serializers.ValidationError(
                {"first_choice_seat_tier_id": "第一希望席が見つかりません"}
            )
        if first_tier.performance_id != performance.pk:
            raise serializers.ValidationError(
                {"first_choice_seat_tier_id": "第一希望席は指定した公演に属していません"}
            )

        second_tier = None
        second_id = data.get("second_choice_seat_tier_id")
        if second_id:
            try:
                second_tier = SeatTier.objects.get(pk=second_id)
            except SeatTier.DoesNotExist:
                raise serializers.ValidationError(
                    {"second_choice_seat_tier_id": "第二希望席が見つかりません"}
                )
            if second_tier.performance_id != performance.pk:
                raise serializers.ValidationError(
                    {"second_choice_seat_tier_id": "第二希望席は指定した公演に属していません"}
                )
            if second_tier.pk == first_tier.pk:
                raise serializers.ValidationError(
                    {"second_choice_seat_tier_id": "第一希望と第二希望は別の席種を選択してください"}
                )

        # link_token 検証（任意）
        link = None
        link_token = (data.get("link_token") or "").strip()
        if link_token:
            try:
                link = AccessLink.objects.get(token=link_token)
            except AccessLink.DoesNotExist:
                raise serializers.ValidationError({"link_token": "無効なリンクです"})
            if not link.is_active:
                raise serializers.ValidationError({"link_token": "このリンクは無効です"})
            if link.mode != AccessLink.Mode.APPLICATION:
                raise serializers.ValidationError({"link_token": "このリンクは応募用ではありません"})
            if link.event_id != performance.event_id:
                raise serializers.ValidationError({"link_token": "リンクの作品と一致しません"})

        # 応募は在庫を減らさない（在庫チェック不要、定員超過の応募も許容）
        data["_performance"] = performance
        data["_first_tier"] = first_tier
        data["_second_tier"] = second_tier
        data["_link"] = link
        return data

    def create(self, validated_data):
        performance = validated_data.pop("_performance")
        first_tier = validated_data.pop("_first_tier")
        second_tier = validated_data.pop("_second_tier")
        link = validated_data.pop("_link", None)

        sales_channel = link.sales_channel if link else Reservation.SalesChannel.ADVANCE

        return Reservation.objects.create(
            performance=performance,
            seat_tier=None,
            first_choice_seat_tier=first_tier,
            second_choice_seat_tier=second_tier,
            allow_any_seat=validated_data.get("allow_any_seat", False),
            quantity=validated_data["quantity"],
            reservation_type=Reservation.ReservationType.CASH,
            sales_channel=sales_channel,
            status=Reservation.Status.APPLIED,
            payment_status=Reservation.PaymentStatus.UNPAID,
            guest_name=validated_data["guest_name"],
            guest_email=validated_data.get("guest_email", ""),
            guest_phone=validated_data.get("guest_phone", ""),
            memo=validated_data.get("memo", ""),
            is_fanclub_member=validated_data.get("is_fanclub_member", False),
        )


class AccessLinkPublicSerializer(serializers.Serializer):
    """公開 GET /api/links/<token>/ 用（mode と event + 公演一覧を返す）"""
    token = serializers.CharField()
    mode = serializers.CharField()
    sales_channel = serializers.CharField()
    label = serializers.CharField()
    header_image_url = serializers.CharField(allow_blank=True)
    is_active = serializers.BooleanField()
    event = serializers.SerializerMethodField()

    def get_event(self, obj):
        event = obj.event
        performances = event.performances.all().order_by("starts_at")
        return {
            "id": event.id,
            "slug": event.slug,
            "title": event.title,
            "venue_name": event.venue_name,
            "flyer_image_url": event.flyer_image_url,
            "performances": [
                {
                    "id": perf.id,
                    "label": perf.label,
                    "starts_at": perf.starts_at,
                    "open_at": perf.open_at,
                    "seat_tiers": AvailableSeatTierSerializer(
                        perf.seat_tiers.all().order_by("sort_order"), many=True
                    ).data,
                }
                for perf in performances
            ],
        }
