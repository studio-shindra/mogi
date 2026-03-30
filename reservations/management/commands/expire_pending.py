"""作成から一定時間経過した pending 予約を cancelled にする。

Stripe 未決済のまま放置された予約の在庫を解放する。

Usage:
    python manage.py expire_pending
    python manage.py expire_pending --minutes 60
    python manage.py expire_pending --dry-run
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from reservations.models import Reservation


class Command(BaseCommand):
    help = "期限切れの pending 予約を cancelled に更新"

    def add_arguments(self, parser):
        parser.add_argument(
            "--minutes",
            type=int,
            default=30,
            help="pending のまま放置する上限（分）。デフォルト: 30",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="実際には更新せず、対象件数だけ表示",
        )

    def handle(self, *args, **options):
        minutes = options["minutes"]
        dry_run = options["dry_run"]
        cutoff = timezone.now() - timedelta(minutes=minutes)

        expired_qs = Reservation.objects.filter(
            status=Reservation.Status.PENDING,
            created_at__lt=cutoff,
        )

        count = expired_qs.count()

        if count == 0:
            self.stdout.write("期限切れの pending 予約はありません")
            return

        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"DRY RUN: {count} 件の pending 予約が期限切れ対象です"
            ))
            for r in expired_qs[:20]:
                self.stdout.write(
                    f"  id={r.pk} {r.guest_name} "
                    f"created={r.created_at} type={r.reservation_type}"
                )
            return

        updated = expired_qs.update(
            status=Reservation.Status.CANCELLED,
        )

        self.stdout.write(self.style.SUCCESS(
            f"完了: {updated} 件の pending 予約を cancelled に更新しました"
        ))
