import logging

from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.db.models import Sum
from django.utils import timezone
from django.utils.html import format_html

from .emails import send_reservation_email
from .models import AccessLink, Reservation

logger = logging.getLogger(__name__)


class ReservationAdminForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # seat_tier は確定席専用。応募（status=applied）は None で保存されるため
        # init では必須化しない（clean() で応募以外のみ必須化する）。
        # Phase B1: 販売区分は必須
        if "sales_channel" in self.fields:
            self.fields["sales_channel"].required = True

    def clean(self):
        cleaned = super().clean()
        status = cleaned.get("status")
        seat_tier = cleaned.get("seat_tier")
        # 応募以外は確定席（seat_tier）必須。応募は希望席で持つ。
        if status and status != Reservation.Status.APPLIED and not seat_tier:
            self.add_error("seat_tier", "応募以外は確定席を指定してください")
        return cleaned


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    form = ReservationAdminForm
    list_display = (
        "guest_name_nowrap",
        "performance",
        "seat_tier",
        "first_choice_short",
        "allow_any_seat_display",
        "quantity",
        "sales_channel",
        "reservation_type",
        "status",
        "payment_status",
        "checked_in",
        "is_fanclub_member",
        "created_at",
    )

    @admin.display(description="氏名", ordering="guest_name")
    def guest_name_nowrap(self, obj):
        return format_html(
            '<span style="white-space:nowrap;">{}</span>', obj.guest_name,
        )

    @admin.display(description="第一希望", ordering="first_choice_seat_tier")
    def first_choice_short(self, obj):
        t = obj.first_choice_seat_tier
        return t.name if t else "—"

    @admin.display(description="席不問", boolean=True)
    def allow_any_seat_display(self, obj):
        return obj.allow_any_seat
    list_filter = (
        "performance__event",
        "performance",
        "sales_channel",
        "reservation_type",
        "status",
        "payment_status",
        "checked_in",
        "is_fanclub_member",
        "allow_any_seat",
    )
    search_fields = ("guest_name", "guest_email", "guest_phone", "token")
    readonly_fields = ("token", "created_at", "updated_at")
    actions = ("confirm_applications", "reject_applications")
    fieldsets = (
        ("公演・確定席", {
            "fields": ("performance", "seat_tier", "quantity"),
            "description": "seat_tier は確定席です。応募段階では希望席を下のセクションに入力してください。",
        }),
        ("応募の希望席", {
            "fields": ("first_choice_seat_tier", "second_choice_seat_tier", "allow_any_seat"),
            "description": "応募（status=applied）でのみ使用します。確定時は seat_tier を設定してください。",
        }),
        ("ゲスト情報", {
            "fields": ("guest_name", "guest_email", "guest_phone"),
        }),
        ("区分・ステータス", {
            "fields": (
                "reservation_type", "sales_channel", "pre_sale_type",
                "status", "payment_status", "is_fanclub_member",
            ),
        }),
        ("チェックイン", {
            "fields": ("checked_in", "checked_in_at"),
            "classes": ("collapse",),
        }),
        ("メモ", {
            "fields": ("memo",),
        }),
        ("システム", {
            "fields": ("token", "stripe_checkout_session_id", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    class Media:
        js = ("reservations/js/filter_seat_tier.js",)

    def confirm_applications(self, request, queryset):
        now = timezone.now()
        stamp = timezone.localtime(now).strftime("%Y-%m-%d %H:%M")
        confirmed_count = 0
        skipped = []
        for reservation in queryset.select_related("seat_tier"):
            if reservation.status != Reservation.Status.APPLIED:
                skipped.append(f"{reservation.pk}:非応募")
                continue
            seat_tier = reservation.seat_tier
            if seat_tier is None:
                skipped.append(f"{reservation.pk}:席種未設定")
                continue
            used = (
                Reservation.objects.filter(
                    seat_tier=seat_tier,
                    status__in=[Reservation.Status.PENDING, Reservation.Status.CONFIRMED],
                ).aggregate(total=Sum("quantity"))["total"]
                or 0
            )
            remaining = seat_tier.capacity - used
            if reservation.quantity > remaining:
                skipped.append(f"{reservation.pk}:残席不足({remaining})")
                continue
            note = f"二次先行当選者 {stamp}"
            reservation.memo = f"{reservation.memo}\n{note}".strip() if reservation.memo else note
            reservation.status = Reservation.Status.CONFIRMED
            reservation.save(update_fields=["status", "memo", "updated_at"])
            confirmed_count += 1
        messages.success(request, f"{confirmed_count} 件を当選処理しました")
        if skipped:
            messages.warning(request, f"スキップ: {', '.join(skipped)}")
    confirm_applications.short_description = "選択した応募を当選処理する"

    def reject_applications(self, request, queryset):
        from .emails import send_application_lost_email
        now = timezone.now()
        stamp = timezone.localtime(now).strftime("%Y-%m-%d %H:%M")
        rejected_count = 0
        for reservation in queryset:
            if reservation.status != Reservation.Status.APPLIED:
                continue
            note = f"二次先行落選者 {stamp}"
            reservation.memo = f"{reservation.memo}\n{note}".strip() if reservation.memo else note
            reservation.status = Reservation.Status.CANCELLED
            reservation.save(update_fields=["status", "memo", "updated_at"])
            if reservation.guest_email:
                try:
                    send_application_lost_email(reservation)
                except Exception:
                    messages.warning(request, f"#{reservation.pk} 落選メール送信失敗")
            rejected_count += 1
        messages.success(request, f"{rejected_count} 件を落選処理しました")
    reject_applications.short_description = "選択した応募を落選処理する"

    def save_model(self, request, obj, form, change):
        # Phase A: draft 自動化を撤去。
        # 決済前提が無くなったため、reservation_type 未指定は cash に補完する。
        if not change and not obj.reservation_type:
            obj.reservation_type = Reservation.ReservationType.CASH
        # Phase B1: sales_channel 未指定は general に補完
        if not change and not obj.sales_channel:
            obj.sales_channel = Reservation.SalesChannel.GENERAL

        super().save_model(request, obj, form, change)

        # 新規作成時のみメール送信（編集時は送らない）
        if not change and obj.guest_email:
            try:
                send_reservation_email(obj)
                messages.success(request, f"{obj.guest_email} へ予約通知メールを送信しました。")
            except Exception:
                logger.exception("予約通知メール送信失敗: reservation=%s", obj.pk)
                messages.warning(request, "予約は保存されましたが、メール送信に失敗しました。")


@admin.register(AccessLink)
class AccessLinkAdmin(admin.ModelAdmin):
    list_display = (
        "label",
        "mode",
        "sales_channel",
        "event",
        "is_active",
        "token_short",
        "created_at",
    )
    list_filter = (
        "event",
        "mode",
        "sales_channel",
        "is_active",
    )
    search_fields = ("label", "token")
    readonly_fields = ("token", "full_url", "created_at", "updated_at")

    @admin.display(description="token")
    def token_short(self, obj):
        return f"{obj.token[:10]}..."

    @admin.display(description="URL（コピー用）")
    def full_url(self, obj):
        if not obj.pk:
            return "（保存後に表示されます）"
        if settings.DEBUG:
            base = "http://localhost:5173"
        else:
            base = settings.FRONTEND_URL.rstrip("/")
        url = f"{base}/r/{obj.token}/"
        return format_html(
            '<input type="text" readonly value="{}" '
            'style="width:100%;max-width:560px;padding:4px 8px;" '
            'onclick="this.select()" />',
            url,
        )
