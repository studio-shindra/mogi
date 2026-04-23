from django.db import models


class Event(models.Model):
    title = models.CharField("作品名", max_length=200)
    slug = models.SlugField("スラッグ", unique=True)
    description = models.TextField("説明", blank=True)
    organizer_name = models.CharField("主催者名", max_length=200, blank=True)
    organizer_email = models.EmailField("主催者メール", blank=True)
    email_signature = models.TextField("メール署名", blank=True)
    venue_name = models.CharField("会場名", max_length=200, blank=True)
    venue_address = models.CharField("会場住所", max_length=500, blank=True)
    cast = models.TextField("出演", blank=True)
    flyer_image_url = models.URLField("フライヤー画像URL", max_length=500, blank=True)
    public_entry_enabled = models.BooleanField("本URL公開", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "作品"
        verbose_name_plural = "作品"

    def __str__(self):
        return self.title


class Performance(models.Model):
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="performances",
        verbose_name="作品",
    )
    label = models.CharField("公演名", max_length=200)
    starts_at = models.DateTimeField("開演")
    open_at = models.DateTimeField("開場")
    show_fanclub_question = models.BooleanField("FC会員欄を表示", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["starts_at"]
        verbose_name = "公演"
        verbose_name_plural = "公演"

    def __str__(self):
        return f"{self.event.title} / {self.label}"


class SeatTier(models.Model):
    class TierCode(models.TextChoices):
        ROW_A = "row_a", "A列"
        ROW_B = "row_b", "B列"
        ROW_C = "row_c", "C列"
        ROW_D_BENCH = "row_d_bench", "D列ベンチシート"
        ROW_E_BENCH = "row_e_bench", "E列ベンチシート"
        STAFF_SEAT = "staff_seat", "関係者席"

    performance = models.ForeignKey(
        Performance,
        on_delete=models.CASCADE,
        related_name="seat_tiers",
        verbose_name="公演",
    )
    code = models.CharField(
        "席種コード",
        max_length=20,
        choices=TierCode.choices,
    )
    name = models.CharField("席種表示名", max_length=50)
    capacity = models.PositiveIntegerField("定員")
    price_card = models.PositiveIntegerField("前売り価格")
    price_cash = models.PositiveIntegerField("当日価格")
    sort_order = models.PositiveSmallIntegerField("表示順", default=0)
    is_staff_only = models.BooleanField(
        "スタッフ専用枠",
        default=False,
        help_text="True の席種は公開APIから除外され、スタッフ用画面のみで選択可能",
    )

    class Meta:
        ordering = ["sort_order"]
        verbose_name = "席種"
        verbose_name_plural = "席種"
        constraints = [
            models.UniqueConstraint(
                fields=["performance", "code"],
                name="unique_tier_per_performance",
            ),
        ]

    def __str__(self):
        return self.name
