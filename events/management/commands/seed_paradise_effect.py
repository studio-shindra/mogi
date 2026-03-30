"""パラダイスエフェクトの初期データを投入する。

Usage:
    python manage.py seed_paradise_effect
    python manage.py seed_paradise_effect --delete  # 既存を消して再投入
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from events.models import Event, Performance


SLUG = "paradise-effect"

PERFORMANCES = [
    {"label": "5/21(金) 18:00 ソワレ", "starts_at": "2026-05-21T18:00:00"},
    {"label": "5/22(土) 13:00 マチネ", "starts_at": "2026-05-22T13:00:00"},
    {"label": "5/22(土) 18:00 ソワレ", "starts_at": "2026-05-22T18:00:00"},
    {"label": "5/23(日) 13:00 マチネ", "starts_at": "2026-05-23T13:00:00"},
    {"label": "5/24(日) 18:00 ソワレ", "starts_at": "2026-05-24T18:00:00"},
]


class Command(BaseCommand):
    help = "パラダイスエフェクトの Event + Performance を投入"

    def add_arguments(self, parser):
        parser.add_argument(
            "--delete",
            action="store_true",
            help="既存の同一 slug の Event を削除してから投入",
        )

    def handle(self, *args, **options):
        if options["delete"]:
            deleted, _ = Event.objects.filter(slug=SLUG).delete()
            if deleted:
                self.stdout.write(f"既存データ削除: {deleted} 件")

        if Event.objects.filter(slug=SLUG).exists():
            self.stdout.write(self.style.WARNING(
                f"Event slug='{SLUG}' は既に存在します。--delete で再投入できます。"
            ))
            return

        tz = timezone.get_current_timezone()

        event = Event.objects.create(
            title="パラダイスエフェクト〖第一回単独公演〗",
            slug=SLUG,
            description=(
                "コヤナギシンが語り紡ぐ、楽園へ向かうための小さな羽ばたき。"
                "『ギャンブラーズ』『カギ』『世界にアンチ！』『売れ残り』の"
                "４本からなるオムニバス短編集。"
            ),
            organizer_name="STUDIO SHINDRA",
            venue_name="新生館スタジオ",
            venue_address="東京都板橋区中板橋19-6 ダイアパレス中板橋B1",
            cast="コヤナギシン",
        )
        self.stdout.write(f"Event 作成: {event}")

        for perf_data in PERFORMANCES:
            from datetime import datetime

            starts_at = datetime.fromisoformat(perf_data["starts_at"]).replace(
                tzinfo=tz,
            )
            open_at = starts_at - timedelta(minutes=30)

            perf = Performance.objects.create(
                event=event,
                label=perf_data["label"],
                starts_at=starts_at,
                open_at=open_at,
            )
            self.stdout.write(f"  Performance 作成: {perf}")

        self.stdout.write(self.style.SUCCESS(
            f"完了: Event 1件 + Performance {len(PERFORMANCES)}件"
        ))
