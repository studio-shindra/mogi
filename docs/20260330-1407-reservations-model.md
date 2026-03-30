# 作業報告書: Mogi バックエンド Step 3 — reservations モデル定義

- 日時: 2026-03-30 14:07
- 作業者: Claude (Opus 4.6)
- プロジェクト: Mogi（演劇向け最小票券管理システム）

---

## 1. 作業の目的

予約の中核モデル（Reservation）を定義し、admin 登録まで完了させる。
events API より先にモデルを固めることで、全体設計のブレを防ぐ。

---

## 2. 前回レビューからの反映事項

| 指摘 | 対応 |
|------|------|
| db.sqlite3 が残存 | 削除済み |
| 報告書は docs/ 配下に出す | docs/ ディレクトリ作成、前回報告書も移動済み |
| Reservation に quantity を追加 | `quantity: PositiveSmallIntegerField(default=1)` で追加 |
| ReservationItem は作らない（1予約1席種） | Reservation に seat_tier + quantity を直接持たせた |
| 実装順序: reservations モデルを events API より先に | 本ステップで対応 |

---

## 3. 変更ファイル一覧

| ファイル | 操作 | 概要 |
|---------|------|------|
| `config/settings.py` | 編集（1行追加） | INSTALLED_APPS に `"reservations"` 追加 |
| `reservations/__init__.py` | 自動生成 | startapp で生成（空） |
| `reservations/apps.py` | 自動生成 | startapp で生成（デフォルト） |
| `reservations/models.py` | 書き換え | Reservation モデル定義 |
| `reservations/admin.py` | 書き換え | ReservationAdmin 登録 |
| `reservations/migrations/0001_initial.py` | 自動生成 | makemigrations で生成 |
| `reservations/tests.py` | 自動生成 | startapp で生成（空、未変更） |
| `reservations/views.py` | 自動生成 | startapp で生成（空、未変更） |
| `db.sqlite3` | 削除 | PostgreSQL 移行済みのため不要 |
| `docs/` | 新規ディレクトリ | 報告書の格納先 |

---

## 4. 各ファイルの詳細

### 4.1 config/settings.py（差分のみ）

INSTALLED_APPS に `"reservations"` を1行追加。他は変更なし。

### 4.2 reservations/models.py — Reservation モデル

#### TextChoices 定義

| Choices クラス | 値 | 表示名 |
|---------------|-----|--------|
| ReservationType.CARD | `"card"` | カード決済 |
| ReservationType.CASH | `"cash"` | 現金 |
| ReservationType.INVITE | `"invite"` | 招待 |
| Status.PENDING | `"pending"` | 仮予約 |
| Status.CONFIRMED | `"confirmed"` | 確定 |
| Status.CANCELLED | `"cancelled"` | キャンセル |
| PaymentStatus.UNPAID | `"unpaid"` | 未払い |
| PaymentStatus.PAID | `"paid"` | 支払い済み |
| PaymentStatus.REFUNDED | `"refunded"` | 返金済み |

#### フィールド定義

| フィールド | 型 | 備考 |
|-----------|-----|------|
| performance | FK(events.Performance, CASCADE) | related_name="reservations" |
| seat_tier | FK(events.SeatTier, PROTECT) | related_name="reservations"。PROTECT にした理由: 予約が残っている席種の誤削除を防ぐ |
| quantity | PositiveSmallIntegerField(default=1) | 枚数。1予約1席種の前提 |
| token | CharField(64, unique, default=uuid4) | 予約確認URL用ランダムトークン。editable=False |
| guest_name | CharField(200) | 氏名 |
| guest_email | EmailField | メール |
| guest_phone | CharField(30, blank) | 電話番号 |
| reservation_type | CharField(10, choices) | card / cash / invite |
| status | CharField(10, choices, default=pending) | pending / confirmed / cancelled |
| payment_status | CharField(10, choices, default=unpaid) | unpaid / paid / refunded |
| checked_in | BooleanField(default=False) | 入場済みフラグ |
| checked_in_at | DateTimeField(null, blank) | 入場日時 |
| stripe_checkout_session_id | CharField(255, blank) | Stripe Session ID |
| pre_sale_type | CharField(50, blank) | 先行受付種別（CSVインポート用） |
| memo | TextField(blank) | メモ |
| created_at | DateTimeField(auto_now_add) | |
| updated_at | DateTimeField(auto_now) | |

#### 設計判断

- **seat_tier の on_delete=PROTECT**: CASCADE だと席種を消した瞬間に予約が消える。PROTECT で安全側に倒した
- **token のデフォルト値に uuid.uuid4 を使用**: UUIDv4 の hex 表現（ハイフン付き36文字）。URL 公開用なので推測困難であること優先
- **quantity を PositiveSmallIntegerField にした理由**: 1予約あたりの枚数は数枚が上限。SmallInt で十分
- **performance と seat_tier を両方 FK で持つ理由**: seat_tier から performance は逆引きできるが、クエリの利便性（公演単位の予約一覧取得）のため performance も直接持つ
- **ReservationItem を作らなかった理由**: MVP では1予約1席種。複数席種を1予約でまとめる要件がないため不要

#### 状態遷移の想定（モデル上の制約は入れていない、ビジネスロジック層で制御）

```
card:   pending/unpaid → (Stripe webhook) → confirmed/paid
cash:   confirmed/unpaid → (受付操作) → confirmed/paid
invite: confirmed/paid （作成時に即確定）
当日券:  confirmed/unpaid → (現金受領) → confirmed/paid
キャンセル: → cancelled（どの種別からも遷移可能）
```

### 4.3 reservations/admin.py

```python
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = (
        "guest_name", "performance", "seat_tier", "quantity",
        "reservation_type", "status", "payment_status",
        "checked_in", "created_at",
    )
    list_filter = (
        "performance__event", "performance",
        "reservation_type", "status", "payment_status", "checked_in",
    )
    search_fields = ("guest_name", "guest_email", "guest_phone", "token")
    readonly_fields = ("token", "created_at", "updated_at")
```

- token / created_at / updated_at は readonly（admin からの改ざん防止）
- performance__event でフィルタ可能にし、作品 → 公演 の絞り込みに対応
- search_fields に token を含めることで、予約確認URLからの逆引きが可能

---

## 5. 実行コマンドと動作確認結果

| コマンド | 結果 |
|---------|------|
| `python manage.py startapp reservations` | 成功。reservations/ 以下にファイル生成 |
| `python manage.py makemigrations reservations` | `reservations/migrations/0001_initial.py` 生成 |
| `python manage.py migrate` | `Applying reservations.0001_initial... OK` |
| `python manage.py check` | `System check identified no issues (0 silenced)` |

---

## 6. 未着手・残存事項

| 項目 | 状態 | 備考 |
|------|------|------|
| .env ファイル | 未作成 | デフォルト値で動作中 |
| .gitignore（ルート） | 未作成 | |
| Procfile / runtime.txt | 未作成 | Heroku デプロイ時に作成 |
| events の API (serializer/views/urls) | 未着手 | Step 4 |
| reservations の API (serializer/views/urls) | 未着手 | Step 4 |
| payments app | 未着手 | Step 5 |
| notifications app | 未着手 | Step 後半 |
| 在庫チェックロジック | 未着手 | reservations の view 層で実装予定 |
| CSVインポート | 未着手 | reservations/management/commands/ |

---

## 7. 次ステップ

**Step 4:** events + reservations の serializer / views / urls を実装し、API エンドポイントを公開する。

対象ファイル:
- `events/serializers.py`, `events/views.py`, `events/urls.py`
- `reservations/serializers.py`, `reservations/views.py`, `reservations/urls.py`
- `config/urls.py`（include 追加）

---

## 8. 現在のディレクトリ構成

```
Mogi/
├── manage.py
├── compose.yml
├── requirements.txt
├── config/
│   ├── __init__.py
│   ├── settings.py               ← reservations 追加
│   ├── urls.py                   ← 未変更
│   ├── wsgi.py
│   └── asgi.py
├── events/
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                 ← Event, Performance, SeatTier
│   ├── admin.py                  ← 3モデル登録
│   ├── views.py                  （空）
│   ├── tests.py                  （空）
│   └── migrations/
│       ├── __init__.py
│       └── 0001_initial.py
├── reservations/                 ← 新規 app
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                 ← Reservation
│   ├── admin.py                  ← ReservationAdmin
│   ├── views.py                  （空）
│   ├── tests.py                  （空）
│   └── migrations/
│       ├── __init__.py
│       └── 0001_initial.py
├── docs/
│   ├── 20260330-1400-backend-step1-settings-and-events-models.md
│   └── 20260330-1407-reservations-model.md   ← 本報告書
├── frontend/                     （対象外）
└── venv/                         （対象外）
```
