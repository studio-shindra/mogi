from django.core.management.base import BaseCommand
from django.db import transaction

from events.models import Performance, SeatTier


class Command(BaseCommand):
    help = "各公演に招待枠 SeatTier (is_staff_only=True) を1件ずつ作成する。既存ならスキップ。"

    def add_arguments(self, parser):
        parser.add_argument(
            "--capacity",
            type=int,
            default=7,
            help="招待枠の定員（デフォルト 7）",
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
            default="招待",
            help="席種表示名（デフォルト '招待'）",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        capacity = options["capacity"]
        sort_order = options["sort_order"]
        name = options["name"]

        created = 0
        skipped = 0
        for perf in Performance.objects.all():
            exists = SeatTier.objects.filter(
                performance=perf,
                code=SeatTier.TierCode.INVITE,
            ).exists()
            if exists:
                skipped += 1
                self.stdout.write(f"- skip: {perf} (既に招待枠あり)")
                continue

            SeatTier.objects.create(
                performance=perf,
                code=SeatTier.TierCode.INVITE,
                name=name,
                capacity=capacity,
                price_card=0,
                price_cash=0,
                sort_order=sort_order,
                is_staff_only=True,
            )
            created += 1
            self.stdout.write(self.style.SUCCESS(f"+ 作成: {perf}"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"完了: 作成 {created} / スキップ {skipped}"))
