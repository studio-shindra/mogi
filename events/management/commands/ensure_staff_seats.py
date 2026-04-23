from django.core.management.base import BaseCommand
from django.db import transaction

from events.models import Performance, SeatTier


class Command(BaseCommand):
    help = "各公演に関係者席 SeatTier (is_staff_only=True) を1件ずつ作成する。既存ならスキップ。"

    def add_arguments(self, parser):
        parser.add_argument(
            "--capacity",
            type=int,
            default=7,
            help="関係者席の定員（デフォルト 7）",
        )
        parser.add_argument(
            "--sort-order",
            type=int,
            default=99,
            help="表示順（デフォルト 99、末尾に並ぶ想定）",
        )
        parser.add_argument(
            "--name",
            type=str,
            default="関係者席",
            help="席種表示名（デフォルト '関係者席'）",
        )
        parser.add_argument(
            "--price",
            type=int,
            default=4800,
            help="料金（デフォルト 4800。price_card / price_cash に同額を設定）",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        capacity = options["capacity"]
        sort_order = options["sort_order"]
        name = options["name"]
        price = options["price"]

        created = 0
        skipped = 0
        for perf in Performance.objects.all():
            exists = SeatTier.objects.filter(
                performance=perf,
                code=SeatTier.TierCode.STAFF_SEAT,
            ).exists()
            if exists:
                skipped += 1
                self.stdout.write(f"- skip: {perf} (既に関係者席あり)")
                continue

            SeatTier.objects.create(
                performance=perf,
                code=SeatTier.TierCode.STAFF_SEAT,
                name=name,
                capacity=capacity,
                price_card=price,
                price_cash=price,
                sort_order=sort_order,
                is_staff_only=True,
            )
            created += 1
            self.stdout.write(self.style.SUCCESS(f"+ 作成: {perf}"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"完了: 作成 {created} / スキップ {skipped}"))
