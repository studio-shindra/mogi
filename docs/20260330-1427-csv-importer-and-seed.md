# 作業報告書: Event フィールド追加 + CSV インポーター + 初期データ投入

- 日時: 2026-03-30 14:27
- 作業者: Claude (Opus 4.6)
- プロジェクト: Mogi（演劇向け最小票券管理システム）

---

## 1. 目的

1. Event モデルに会場・出演者フィールドを追加
2. 先行受付 CSV インポーター（management command）を構築
3. パラダイスエフェクトの初期データを投入

---

## 2. 変更ファイル一覧

| ファイル | 操作 | 概要 |
|---------|------|------|
| `events/models.py` | 編集 | Event に venue_name, venue_address, cast を追加 |
| `events/admin.py` | 編集 | fieldsets に新フィールド追加、list_display に venue_name 追加 |
| `events/serializers.py` | 編集 | EventSerializer に新フィールド追加 |
| `events/migrations/0002_event_cast_event_venue_address_event_venue_name.py` | 自動生成 | 上記3フィールドの migration |
| `events/management/__init__.py` | 新規 | パッケージ初期化 |
| `events/management/commands/__init__.py` | 新規 | パッケージ初期化 |
| `events/management/commands/seed_paradise_effect.py` | 新規 | 初期データ投入コマンド |
| `reservations/management/__init__.py` | 新規 | パッケージ初期化 |
| `reservations/management/commands/__init__.py` | 新規 | パッケージ初期化 |
| `reservations/management/commands/import_presale.py` | 新規 | CSV インポーター |
| `data/presale_sample.csv` | 新規 | サンプル CSV |

---

## 3. 各ファイルの詳細

### 3.1 Event モデル追加フィールド（events/models.py）

| フィールド | 型 | 備考 |
|-----------|-----|------|
| venue_name | CharField(200, blank=True) | 会場名 |
| venue_address | CharField(500, blank=True) | 会場住所 |
| cast | TextField(blank=True) | 出演者。複数人は改行区切り |

- すべて blank=True（任意項目）。既存データへの影響なし
- 会場情報は Event 単位（全公演同一会場の前提）。将来ツアー公演対応時は Performance に移す or Venue モデルを切る

### 3.2 events/admin.py（差分）

- list_display に `venue_name` 追加
- fieldsets を追加:
  - (None): title, slug, description, cast
  - 会場: venue_name, venue_address
  - 主催者: organizer_name, organizer_email

### 3.3 events/serializers.py（差分）

EventSerializer の fields に `venue_name`, `venue_address`, `cast` を追加。
EventListSerializer は変更なし（一覧には含めない）。

### 3.4 seed_paradise_effect コマンド

```
python manage.py seed_paradise_effect           # 初回投入
python manage.py seed_paradise_effect --delete   # 消して再投入
```

投入内容:
- Event 1件（パラダイスエフェクト〖第一回単独公演〗）
- Performance 5件（5/21〜5/24）
- open_at は starts_at - 30min の仮値

冪等性:
- slug で既存チェック。既存があれば WARNING を出して終了
- `--delete` で強制再投入

### 3.5 import_presale CSV インポーター

```
python manage.py import_presale <performance_id> <csv_path> [options]
```

#### 引数

| 引数 | 必須 | 説明 |
|------|------|------|
| performance_id | 必須 | 対象公演の ID |
| csv_path | 必須 | CSV ファイルパス |
| --dry-run | 任意 | パース結果だけ表示、保存しない |
| --type | 任意 | 予約種別（card/cash/invite、デフォルト: card） |
| --tier | 任意 | CSV に seat_tier_code がない場合のデフォルト席種 |

#### CSV フォーマット

ヘッダー必須。エンコーディングは UTF-8（BOM 付き対応）。

| カラム | 必須 | 説明 |
|--------|------|------|
| guest_name | 必須 | 氏名 |
| guest_email | 任意 | メール |
| guest_phone | 任意 | 電話番号 |
| pre_sale_type | 任意 | 先行種別（"第一次先行" 等） |
| seat_tier_code | 任意 | 席種コード（front_row/front/center/rear）。なければ --tier で指定 |
| quantity | 任意 | 枚数（デフォルト: 1、上限: 10） |
| memo | 任意 | メモ |

#### 動作仕様

- SeatTier が未登録の公演ではエラー終了（席種を先に admin で作る運用）
- invite の場合: status=confirmed, payment_status=paid で作成
- card/cash の場合: status=confirmed, payment_status=unpaid で作成
- guest_name 空行はスキップ（エラー報告あり）
- quantity 範囲外（1〜10 以外）はスキップ
- 未知のカラムは WARNING 表示して無視
- `transaction.atomic()` で全件一括保存（途中エラー時はロールバック）
- `bulk_create` で一括 INSERT

#### 使い方の例

```bash
# 公演ID=1 に対して先行受付をインポート（カード決済、席種はCSVで指定）
python manage.py import_presale 1 data/presale.csv

# dry-run で確認
python manage.py import_presale 1 data/presale.csv --dry-run

# 招待として一括投入（席種は rear 固定）
python manage.py import_presale 1 data/invite_list.csv --type invite --tier rear
```

### 3.6 サンプル CSV（data/presale_sample.csv）

```csv
guest_name,guest_email,guest_phone,pre_sale_type,seat_tier_code,quantity,memo
山田太郎,yamada@example.com,090-1234-5678,第一次先行,front,2,
佐藤花子,sato@example.com,,第一次先行,center,1,友人紹介
鈴木一郎,,,第一次先行,rear,1,招待扱い
```

---

## 4. 実行コマンドと動作確認結果

| コマンド | 結果 |
|---------|------|
| `python manage.py makemigrations events` | `0002_event_cast_event_venue_address_event_venue_name.py` 生成 |
| `python manage.py migrate` | 適用成功 |
| `python manage.py check` | `System check identified no issues (0 silenced)` |
| `python manage.py seed_paradise_effect` | Event 1件 + Performance 5件 作成成功 |
| ORM でデータ確認 | 全フィールド正常（starts_at/open_at の JST→UTC 変換も正常） |
| `python manage.py import_presale 1 data/presale_sample.csv --dry-run --tier center` | SeatTier 未登録エラー（正しい動作） |
| `python manage.py import_presale --help` | ヘルプ表示正常 |

---

## 5. 投入済みデータ

### Event

| フィールド | 値 |
|-----------|-----|
| title | パラダイスエフェクト〖第一回単独公演〗 |
| slug | paradise-effect |
| description | コヤナギシンが語り紡ぐ〜オムニバス短編集。 |
| organizer_name | STUDIO SHINDRA |
| venue_name | 新生館スタジオ |
| venue_address | 東京都板橋区中板橋19-6 ダイアパレス中板橋B1 |
| cast | コヤナギシン |

### Performance（5件）

| label | starts_at (JST) | open_at (JST, 仮) |
|-------|-----------------|-------------------|
| 5/21(金) 18:00 ソワレ | 2026-05-21 18:00 | 2026-05-21 17:30 |
| 5/22(土) 13:00 マチネ | 2026-05-22 13:00 | 2026-05-22 12:30 |
| 5/22(土) 18:00 ソワレ | 2026-05-22 18:00 | 2026-05-22 17:30 |
| 5/23(日) 13:00 マチネ | 2026-05-23 13:00 | 2026-05-23 12:30 |
| 5/24(日) 18:00 ソワレ | 2026-05-24 18:00 | 2026-05-24 17:30 |

---

## 6. CSV インポーターの運用フロー

```
1. admin で SeatTier を登録（公演ごとに席種・定員・価格を設定）
2. CSV を用意（guest_name は必須、他は任意）
3. dry-run で確認
   python manage.py import_presale <perf_id> data/presale.csv --dry-run
4. 本実行
   python manage.py import_presale <perf_id> data/presale.csv
5. 招待は --type invite --tier rear で別途投入
   python manage.py import_presale <perf_id> data/invite.csv --type invite --tier rear
```

---

## 7. 未着手・残存事項

| 項目 | 状態 | 備考 |
|------|------|------|
| SeatTier データ | 未投入 | 席種・価格・定員が未確定。確定後 admin で入力 |
| .env / .gitignore | 未作成 | |
| Procfile / runtime.txt | 未作成 | |
| reservations API | 未着手 | Step 4b |
| payments app (Stripe) | 未着手 | Step 5 |
| notifications app | 未着手 | |
| 在庫チェックロジック | 未着手 | CSV インポーター側にはまだ在庫チェックなし。API 側で実装予定 |

---

## 8. 次ステップ

**Step 4b:** reservations の API（serializer / views / urls）

- 予約作成 API（在庫チェック含む）
- トークン式確認ページ API
- チェックイン API
- 受付操作 API

---

## 9. 現在のディレクトリ構成

```
Mogi/
├── manage.py
├── compose.yml
├── requirements.txt
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py / asgi.py
│   └── __init__.py
├── events/
│   ├── models.py                 ← venue_name, venue_address, cast 追加
│   ├── admin.py                  ← fieldsets 追加
│   ├── serializers.py            ← 新フィールド追加
│   ├── views.py
│   ├── urls.py
│   ├── apps.py
│   ├── management/
│   │   └── commands/
│   │       └── seed_paradise_effect.py   ← 新規
│   └── migrations/
│       ├── 0001_initial.py
│       └── 0002_event_cast_event_venue_address_event_venue_name.py  ← 新規
├── reservations/
│   ├── models.py
│   ├── admin.py
│   ├── management/
│   │   └── commands/
│   │       └── import_presale.py         ← 新規
│   └── migrations/
│       ├── 0001_initial.py
│       └── 0002_alter_reservation_guest_email_and_more.py
├── data/
│   └── presale_sample.csv                ← 新規
├── docs/
│   ├── 20260330-1400-backend-step1-settings-and-events-models.md
│   ├── 20260330-1407-reservations-model.md
│   ├── 20260330-1419-reservations-fix-and-events-api.md
│   ├── 20260330-1422-initial-data-plan.md
│   └── 20260330-1427-csv-importer-and-seed.md   ← 本報告書
├── frontend/
└── venv/
```
