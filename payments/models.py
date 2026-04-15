from django.db import models


class ProcessedWebhookEvent(models.Model):
    """Square Webhook の event_id を一意に記録し、再送時の重複処理を防ぐ。"""

    event_id = models.CharField("イベントID", max_length=64, unique=True)
    event_type = models.CharField("イベント種別", max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "処理済みWebhookイベント"
        verbose_name_plural = "処理済みWebhookイベント"

    def __str__(self):
        return f"{self.event_type}:{self.event_id}"
