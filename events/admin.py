from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import Event, Performance, SeatTier


class SeatTierResource(resources.ModelResource):
    class Meta:
        model = SeatTier
        fields = (
            "id",
            "performance",
            "code",
            "name",
            "capacity",
            "price_card",
            "price_cash",
            "sort_order",
        )
        import_id_fields = ("id",)


class PerformanceInline(admin.TabularInline):
    model = Performance
    extra = 1
    fields = ("label", "starts_at", "open_at")


class SeatTierInline(admin.TabularInline):
    model = SeatTier
    extra = 4
    fields = ("code", "name", "capacity", "price_card", "price_cash", "sort_order")


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "slug", "venue_name", "public_entry_enabled", "created_at")
    list_filter = ("public_entry_enabled",)
    prepopulated_fields = {"slug": ("title",)}
    inlines = [PerformanceInline]
    fieldsets = (
        (None, {"fields": ("title", "slug", "description", "cast", "flyer_image_url")}),
        ("公開設定", {"fields": ("public_entry_enabled",)}),
        ("会場", {"fields": ("venue_name", "venue_address")}),
        ("主催者", {"fields": ("organizer_name", "organizer_email")}),
    )


@admin.register(Performance)
class PerformanceAdmin(admin.ModelAdmin):
    list_display = ("event", "label", "starts_at")
    list_filter = ("event",)
    inlines = [SeatTierInline]


@admin.register(SeatTier)
class SeatTierAdmin(ImportExportModelAdmin):
    resource_classes = [SeatTierResource]
    list_display = ("performance", "code", "name", "capacity", "price_card", "price_cash")
    list_filter = ("performance__event", "code")
