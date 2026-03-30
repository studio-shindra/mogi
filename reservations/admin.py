from django.contrib import admin

from .models import Reservation


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
