"""既存 Reservation に sales_channel を寄せるバックフィル。

方針:
    - reservation_type = "invite"       → sales_channel = "invite"
    - それ以外で pre_sale_type 非空      → sales_channel = "advance"
    - それ以外は既定 (general) のまま

Usage:
    python3 manage.py backfill_sales_channel --dry-run
    python3 manage.py backfill_sales_channel

冪等。再実行しても既に寄せ済みのものは変更されない。
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from reservations.models import Reservation


class Command(BaseCommand):
    help = "既存 Reservation の sales_channel を推定値で埋める"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="実際には更新せず、件数だけ表示",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        invite_qs = Reservation.objects.filter(
            reservation_type=Reservation.ReservationType.INVITE,
        ).exclude(sales_channel=Reservation.SalesChannel.INVITE)

        advance_qs = Reservation.objects.exclude(
            reservation_type=Reservation.ReservationType.INVITE,
        ).exclude(pre_sale_type="").exclude(
            sales_channel=Reservation.SalesChannel.ADVANCE,
        )

        invite_count = invite_qs.count()
        advance_count = advance_qs.count()

        self.stdout.write(f"invite 候補: {invite_count} 件")
        self.stdout.write(f"advance 候補: {advance_count} 件")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN: 更新は行いません"))
            for r in invite_qs[:10]:
                self.stdout.write(
                    f"  [invite] id={r.pk} {r.guest_name} "
                    f"type={r.reservation_type} pre_sale={r.pre_sale_type!r}"
                )
            for r in advance_qs[:10]:
                self.stdout.write(
                    f"  [advance] id={r.pk} {r.guest_name} "
                    f"type={r.reservation_type} pre_sale={r.pre_sale_type!r}"
                )
            return

        with transaction.atomic():
            invite_updated = invite_qs.update(
                sales_channel=Reservation.SalesChannel.INVITE,
            )
            advance_updated = advance_qs.update(
                sales_channel=Reservation.SalesChannel.ADVANCE,
            )

        self.stdout.write(self.style.SUCCESS(
            f"完了: invite={invite_updated}, advance={advance_updated}"
        ))
