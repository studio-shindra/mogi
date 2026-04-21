import secrets
import uuid

from django.db import models


def _generate_token():
    return uuid.uuid4().hex


def _generate_link_token():
    return secrets.token_hex(16)


class Reservation(models.Model):

    class ReservationType(models.TextChoices):
        CARD = "card", "カード決済"
        CASH = "cash", "現金"
        INVITE = "invite", "招待"

    class Status(models.TextChoices):
        DRAFT = "draft", "仮受付"
        PENDING = "pending", "仮予約"
        APPLIED = "applied", "応募"
        CONFIRMED = "confirmed", "確定"
        CANCELLED = "cancelled", "キャンセル"

    class PaymentStatus(models.TextChoices):
        UNPAID = "unpaid", "未払い"
        PAID = "paid", "支払い済み"
        REFUNDED = "refunded", "返金済み"

    class SalesChannel(models.TextChoices):
        ADVANCE = "advance", "先行"
        GENERAL = "general", "一般"
        STAFF = "staff", "関係者"
        INVITE = "invite", "招待"
        HOLD = "hold", "取り置き"
        WALK_IN = "walk_in", "当日券"

    # --- リレーション ---
    performance = models.ForeignKey(
        "events.Performance",
        on_delete=models.CASCADE,
        related_name="reservations",
        verbose_name="公演",
    )
    seat_tier = models.ForeignKey(
        "events.SeatTier",
        on_delete=models.PROTECT,
        related_name="reservations",
        verbose_name="席種",
        null=True,
        blank=True,
    )

    # --- 枚数 ---
    quantity = models.PositiveSmallIntegerField("枚数", default=1)

    # --- トークン ---
    token = models.CharField(
        "確認トークン",
        max_length=32,
        unique=True,
        default=_generate_token,
        editable=False,
    )

    # --- ゲスト情報 ---
    guest_name = models.CharField("氏名", max_length=200)
    guest_email = models.EmailField("メール", blank=True)
    guest_phone = models.CharField("電話番号", max_length=30, blank=True)

    # --- 予約種別・状態 ---
    reservation_type = models.CharField(
        "予約種別",
        max_length=10,
        choices=ReservationType.choices,
        blank=True,
        default="",
    )
    status = models.CharField(
        "ステータス",
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )
    payment_status = models.CharField(
        "支払状態",
        max_length=10,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
    )

    # --- チェックイン ---
    checked_in = models.BooleanField("入場済み", default=False)
    checked_in_at = models.DateTimeField("入場日時", null=True, blank=True)

    # --- Stripe ---
    stripe_checkout_session_id = models.CharField(
        "Stripe Session ID",
        max_length=255,
        blank=True,
    )

    # --- 販売区分 ---
    sales_channel = models.CharField(
        "販売区分",
        max_length=10,
        choices=SalesChannel.choices,
        default=SalesChannel.GENERAL,
    )

    # --- 先行受付・メモ ---
    pre_sale_type = models.CharField("先行種別", max_length=50, blank=True)
    memo = models.TextField("メモ", blank=True)

    # --- 応募時の付帯情報 ---
    is_fanclub_member = models.BooleanField("FC会員", default=False)

    # --- 応募時の希望席（確定席は seat_tier を使う） ---
    first_choice_seat_tier = models.ForeignKey(
        "events.SeatTier",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="第一希望席",
        null=True,
        blank=True,
    )
    second_choice_seat_tier = models.ForeignKey(
        "events.SeatTier",
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="第二希望席",
        null=True,
        blank=True,
    )
    allow_any_seat = models.BooleanField("どの席でも可", default=False)

    # --- タイムスタンプ ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "予約"
        verbose_name_plural = "予約"

    def __str__(self):
        return f"{self.guest_name} / {self.performance} ({self.get_reservation_type_display()})"


class AccessLink(models.Model):
    """限定URL: 作品への入口を token で 1本発行し、mode/販売区分を backend が決める。"""

    class Mode(models.TextChoices):
        RESERVATION = "reservation", "予約"
        APPLICATION = "application", "応募"

    token = models.CharField(
        "トークン",
        max_length=32,
        unique=True,
        default=_generate_link_token,
    )
    event = models.ForeignKey(
        "events.Event",
        on_delete=models.CASCADE,
        related_name="access_links",
        verbose_name="作品",
    )
    mode = models.CharField(
        "モード",
        max_length=12,
        choices=Mode.choices,
    )
    sales_channel = models.CharField(
        "販売区分",
        max_length=10,
        choices=Reservation.SalesChannel.choices,
        default=Reservation.SalesChannel.ADVANCE,
    )
    label = models.CharField("ラベル", max_length=100)
    header_image_url = models.URLField(
        "ヘッダー画像URL",
        max_length=500,
        blank=True,
    )
    is_active = models.BooleanField("有効", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "限定URL"
        verbose_name_plural = "限定URL"

    def __str__(self):
        return f"{self.label} ({self.get_mode_display()})"
