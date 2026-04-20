import logging

from django import forms
from django.contrib import admin, messages
from django.db.models import Sum
from django.utils import timezone

from .emails import send_reservation_email
from .models import AccessLink, Reservation

logger = logging.getLogger(__name__)


class ReservationAdminForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Phase A: 席種未指定の予約は在庫事故の原因になるため必須化
        if "seat_tier" in self.fields:
            self.fields["seat_tier"].required = True
        # Phase B1: 販売区分は必須
        if "sales_channel" in self.fields:
            self.fields["sales_channel"].required = True


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    form = ReservationAdminForm
    list_display = (
        "guest_name",
        "performance",
        "seat_tier",
        "quantity",
        "sales_channel",
        "reservation_type",
        "status",
        "payment_status",
        "checked_in",
        "is_fanclub_member",
        "created_at",
    )
    list_filter = (
        "performance__event",
        "performance",
        "sales_channel",
        "reservation_type",
        "status",
        "payment_status",
        "checked_in",
        "is_fanclub_member",
    )
    search_fields = ("guest_name", "guest_email", "guest_phone", "token")
    readonly_fields = ("token", "created_at", "updated_at")
    actions = ("confirm_applications", "reject_applications")

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
            note = f"[system] application confirmed {stamp}"
            reservation.memo = f"{reservation.memo}\n{note}".strip() if reservation.memo else note
            reservation.status = Reservation.Status.CONFIRMED
            reservation.save(update_fields=["status", "memo", "updated_at"])
            confirmed_count += 1
        messages.success(request, f"{confirmed_count} 件を当選処理しました")
        if skipped:
            messages.warning(request, f"スキップ: {', '.join(skipped)}")
    confirm_applications.short_description = "選択した応募を当選処理する"

    def reject_applications(self, request, queryset):
        now = timezone.now()
        stamp = timezone.localtime(now).strftime("%Y-%m-%d %H:%M")
        rejected_count = 0
        for reservation in queryset:
            if reservation.status != Reservation.Status.APPLIED:
                continue
            note = f"[system] application rejected {stamp}"
            reservation.memo = f"{reservation.memo}\n{note}".strip() if reservation.memo else note
            reservation.status = Reservation.Status.CANCELLED
            reservation.save(update_fields=["status", "memo", "updated_at"])
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
        "performance",
        "is_active",
        "token_short",
        "created_at",
    )
    list_filter = (
        "performance__event",
        "performance",
        "mode",
        "sales_channel",
        "is_active",
    )
    search_fields = ("label", "token")
    readonly_fields = ("token", "created_at", "updated_at")

    @admin.display(description="token")
    def token_short(self, obj):
        return f"{obj.token[:10]}..."
