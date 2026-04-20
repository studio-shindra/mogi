"""先行受付 CSV をインポートして Reservation を作成する。

CSV フォーマット（ヘッダー必須）:
    guest_name,guest_email,guest_phone,pre_sale_type,seat_tier_code,quantity,memo

Usage:
    python manage.py import_presale <performance_id> <csv_path>
    python manage.py import_presale <performance_id> <csv_path> --dry-run
    python manage.py import_presale <performance_id> <csv_path> --type invite

例:
    python manage.py import_presale 1 data/presale.csv
    python manage.py import_presale 1 data/presale.csv --dry-run
    python manage.py import_presale 1 data/presale.csv --type invite --tier rear
"""

import csv

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from events.models import Performance, SeatTier
from reservations.models import Reservation


REQUIRED_COLUMNS = {"guest_name"}
OPTIONAL_COLUMNS = {
    "guest_email",
    "guest_phone",
    "pre_sale_type",
    "seat_tier_code",
    "quantity",
    "memo",
}
ALL_COLUMNS = REQUIRED_COLUMNS | OPTIONAL_COLUMNS


class Command(BaseCommand):
    help = "先行受付 CSV をインポートして Reservation を作成"

    def add_arguments(self, parser):
        parser.add_argument("performance_id", type=int, help="対象 Performance の ID")
        parser.add_argument("csv_path", type=str, help="CSV ファイルパス")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="実際には保存せず、パース結果だけ表示",
        )
        parser.add_argument(
            "--type",
            choices=["card", "cash", "invite"],
            default="cash",
            help="予約種別（デフォルト: cash）",
        )
        parser.add_argument(
            "--channel",
            choices=["advance", "general", "staff", "invite", "hold", "walk_in"],
            default="advance",
            help="販売区分（デフォルト: advance）",
        )
        parser.add_argument(
            "--tier",
            type=str,
            default="",
            help="席種コード（CSV に seat_tier_code がない場合のデフォルト値）",
        )

    def handle(self, *args, **options):
        performance_id = options["performance_id"]
        csv_path = options["csv_path"]
        dry_run = options["dry_run"]
        default_type = options["type"]
        default_channel = options["channel"]
        default_tier = options["tier"]

        # Performance 取得
        try:
            performance = Performance.objects.select_related("event").get(
                pk=performance_id,
            )
        except Performance.DoesNotExist:
            raise CommandError(f"Performance id={performance_id} が見つかりません")

        self.stdout.write(f"対象公演: {performance}")

        # 席種マップ（code → SeatTier）
        tier_map = {
            st.code: st for st in performance.seat_tiers.all()
        }
        if not tier_map:
            raise CommandError(
                f"この公演に SeatTier が登録されていません。"
                f"先に admin で席種を作成してください。"
            )

        # CSV 読み込み
        try:
            with open(csv_path, encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except FileNotFoundError:
            raise CommandError(f"ファイルが見つかりません: {csv_path}")

        if not rows:
            raise CommandError("CSV が空です")

        # ヘッダー検証
        headers = set(rows[0].keys())
        missing = REQUIRED_COLUMNS - headers
        if missing:
            raise CommandError(f"必須カラムがありません: {missing}")

        unknown = headers - ALL_COLUMNS
        if unknown:
            self.stdout.write(self.style.WARNING(
                f"未知のカラムは無視します: {unknown}"
            ))

        # パース
        reservations_to_create = []
        errors = []

        for i, row in enumerate(rows, start=2):  # 2行目からデータ
            guest_name = row.get("guest_name", "").strip()
            if not guest_name:
                errors.append(f"行{i}: guest_name が空です")
                continue

            guest_email = row.get("guest_email", "").strip()
            guest_phone = row.get("guest_phone", "").strip()
            pre_sale_type = row.get("pre_sale_type", "").strip()
            memo = row.get("memo", "").strip()
            quantity = row.get("quantity", "1").strip() or "1"

            try:
                quantity = int(quantity)
                if quantity < 1 or quantity > 10:
                    raise ValueError
            except ValueError:
                errors.append(f"行{i}: quantity が不正です: {row.get('quantity')}")
                continue

            # 席種決定
            tier_code = row.get("seat_tier_code", "").strip() or default_tier
            if not tier_code:
                errors.append(
                    f"行{i}: seat_tier_code が未指定で --tier もありません"
                )
                continue

            seat_tier = tier_map.get(tier_code)
            if not seat_tier:
                errors.append(
                    f"行{i}: 席種 '{tier_code}' がこの公演に存在しません "
                    f"(有効: {list(tier_map.keys())})"
                )
                continue

            # 予約種別
            reservation_type = default_type

            # invite は confirmed/paid で作成、それ以外は confirmed/unpaid
            if reservation_type == "invite":
                status = Reservation.Status.CONFIRMED
                payment_status = Reservation.PaymentStatus.PAID
            else:
                status = Reservation.Status.CONFIRMED
                payment_status = Reservation.PaymentStatus.UNPAID

            reservations_to_create.append(
                Reservation(
                    performance=performance,
                    seat_tier=seat_tier,
                    quantity=quantity,
                    guest_name=guest_name,
                    guest_email=guest_email,
                    guest_phone=guest_phone,
                    reservation_type=reservation_type,
                    sales_channel=default_channel,
                    status=status,
                    payment_status=payment_status,
                    pre_sale_type=pre_sale_type,
                    memo=memo,
                )
            )

        # エラー報告
        if errors:
            for e in errors:
                self.stdout.write(self.style.ERROR(e))
            if not reservations_to_create:
                raise CommandError("有効な行がありません")
            self.stdout.write(self.style.WARNING(
                f"エラー {len(errors)} 件をスキップし、"
                f"{len(reservations_to_create)} 件を処理します"
            ))

        # dry-run
        if dry_run:
            self.stdout.write(self.style.WARNING("\n=== DRY RUN ==="))
            for r in reservations_to_create:
                self.stdout.write(
                    f"  {r.guest_name} | {r.guest_email} | "
                    f"{r.seat_tier.name} x{r.quantity} | "
                    f"{r.reservation_type} | {r.pre_sale_type}"
                )
            self.stdout.write(self.style.WARNING(
                f"\n合計 {len(reservations_to_create)} 件（未保存）"
            ))
            return

        # 保存
        with transaction.atomic():
            created = Reservation.objects.bulk_create(reservations_to_create)

        self.stdout.write(self.style.SUCCESS(
            f"完了: {len(created)} 件の予約を作成しました"
        ))
