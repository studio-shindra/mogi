import uuid

from django.db import models


def _generate_token():
    return uuid.uuid4().hex


class Reservation(models.Model):

    class ReservationType(models.TextChoices):
        CARD = "card", "カード決済"
        CASH = "cash", "現金"
        INVITE = "invite", "招待"

    class Status(models.TextChoices):
        DRAFT = "draft", "仮受付"
        PENDING = "pending", "仮予約"
        CONFIRMED = "confirmed", "確定"
        CANCELLED = "cancelled", "キャンセル"

    class PaymentStatus(models.TextChoices):
        UNPAID = "unpaid", "未払い"
        PAID = "paid", "支払い済み"
        REFUNDED = "refunded", "返金済み"

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

    # --- 先行受付・メモ ---
    pre_sale_type = models.CharField("先行種別", max_length=50, blank=True)
    memo = models.TextField("メモ", blank=True)

    # --- タイムスタンプ ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "予約"
        verbose_name_plural = "予約"

    def __str__(self):
        return f"{self.guest_name} / {self.performance} ({self.get_reservation_type_display()})"
