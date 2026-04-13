import logging

from django.contrib import admin, messages

from .emails import send_reservation_email
from .models import Reservation

logger = logging.getLogger(__name__)


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        "guest_name",
        "performance",
        "seat_tier",
        "quantity",
        "reservation_type",
        "status",
        "payment_status",
        "checked_in",
        "created_at",
    )
    list_filter = (
        "performance__event",
        "performance",
        "reservation_type",
        "status",
        "payment_status",
        "checked_in",
    )
    search_fields = ("guest_name", "guest_email", "guest_phone", "token")
    readonly_fields = ("token", "created_at", "updated_at")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # 新規作成時のみメール送信（編集時は送らない）
        if not change and obj.guest_email:
            try:
                send_reservation_email(obj)
                messages.success(request, f"{obj.guest_email} へ予約通知メールを送信しました。")
            except Exception:
                logger.exception("予約通知メール送信失敗: reservation=%s", obj.pk)
                messages.warning(request, "予約は保存されましたが、メール送信に失敗しました。")
