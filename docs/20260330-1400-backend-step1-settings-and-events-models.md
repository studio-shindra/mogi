# 作業報告書: Mogi バックエンド Step 1+2 — Settings 改修 + events モデル定義

- 日時: 2026-03-30 14:00
- 作業者: Claude (Opus 4.6)
- プロジェクト: Mogi（演劇向け最小票券管理システム）

---

## 1. 作業の目的

Django プロジェクトの初期骨格構築。
`django-admin startproject config .` で生成されたデフォルト状態から、
MVP に必要な設定と中核モデル（events app）を整備し、
`makemigrations` → `migrate` → `manage.py check` まで通す。

---

## 2. 前提条件

| 項目 | 内容 |
|------|------|
| Django 配置 | プロジェクトルート直下（`backend/` は作らない） |
| Django バージョン | 4.2.29 |
| Python バージョン | 3.9（venv） |
| DB | PostgreSQL 16（compose.yml で port 5433 にマッピング済み） |
| env 管理 | `python-decouple`（`config()` 関数）に統一。django-environ は使わない |
| フロント | `frontend/` に Vue（今回は対象外） |
| デプロイ先 | Heroku 想定 |

---

## 3. 変更ファイル一覧

| ファイル | 操作 | 概要 |
|---------|------|------|
| `requirements.txt` | 新規作成 | 依存パッケージ定義 |
| `config/settings.py` | 全面書き換え | デフォルト設定 → 本番対応の設定に改修 |
| `events/__init__.py` | 自動生成 | `startapp` で生成（空ファイル） |
| `events/apps.py` | 自動生成 | `startapp` で生成（デフォルトのまま） |
| `events/models.py` | 書き換え | Event / Performance / SeatTier の3モデル定義 |
| `events/admin.py` | 書き換え | 3モデルの admin 登録 + インライン設定 |
| `events/migrations/0001_initial.py` | 自動生成 | `makemigrations` で生成 |
| `events/tests.py` | 自動生成 | `startapp` で生成（空、未変更） |
| `events/views.py` | 自動生成 | `startapp` で生成（空、未変更） |

---

## 4. 各ファイルの詳細

### 4.1 requirements.txt（新規作成）

```
Django>=4.2,<5.0
djangorestframework>=3.14,<4.0
django-cors-headers>=4.0,<5.0
python-decouple>=3.8,<4.0
whitenoise>=6.5,<7.0
gunicorn>=21.2,<23.0
psycopg2-binary>=2.9,<3.0
stripe>=7.0,<8.0
```

**意図:**
- DRF: API 構築用。この時点では settings に登録のみ、エンドポイントはまだない
- python-decouple: `.env` / 環境変数からの設定読み込み
- django-cors-headers: Vue フロント（localhost:5173）からの API アクセス許可
- whitenoise: Heroku での静的ファイル配信
- gunicorn: Heroku の WSGI サーバ
- psycopg2-binary: PostgreSQL ドライバ（本番では psycopg2 に差し替え推奨）
- stripe: Stripe Checkout 連携用（この時点では未使用、設定枠だけ確保）

### 4.2 config/settings.py（全面書き換え）

変更点を項目別に整理する。

#### env 管理
- `from decouple import Csv, config` を使用
- SECRET_KEY, DEBUG, ALLOWED_HOSTS, DB 接続情報, CORS, Stripe, Email すべて `config()` 経由
- デフォルト値は開発用の値を設定（本番では `.env` または環境変数で上書き）

#### INSTALLED_APPS
```python
"rest_framework",
"corsheaders",
"events",
```

#### MIDDLEWARE
追加したもの:
- `whitenoise.middleware.WhiteNoiseMiddleware` — SecurityMiddleware 直後
- `corsheaders.middleware.CorsMiddleware` — SessionMiddleware 前

#### DATABASE
```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME", default="mogi"),
        "USER": config("DB_USER", default="mogi"),
        "PASSWORD": config("DB_PASSWORD", default="mogi"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5433"),
    }
}
```
- デフォルト値は compose.yml の PostgreSQL コンテナに合わせている
- SQLite からの切り替え（db.sqlite3 は残存しているが未使用になった）

#### i18n / tz
- `LANGUAGE_CODE = "ja"`
- `TIME_ZONE = "Asia/Tokyo"`
- `USE_TZ = True`（UTC 保存、表示時に Asia/Tokyo 変換）

#### 静的ファイル
```python
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
```

#### DRF
```python
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%S%z",
}
```
- デフォルト認証必須。公開 API（予約確認トークン等）は個別に AllowAny を指定する想定

#### CORS
```python
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:5173",
    cast=Csv(),
)
```

#### Stripe（設定枠のみ）
```python
STRIPE_SECRET_KEY = config("STRIPE_SECRET_KEY", default="")
STRIPE_PUBLISHABLE_KEY = config("STRIPE_PUBLISHABLE_KEY", default="")
STRIPE_WEBHOOK_SECRET = config("STRIPE_WEBHOOK_SECRET", default="")
```
- payments app で `from django.conf import settings` 経由で参照する想定
- 将来テナント化する場合は Event/Organizer モデルに移す余地あり

#### Email
```python
EMAIL_BACKEND = config(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@example.com")
```
- 開発時はコンソール出力、本番は SMTP/SES に切り替え

### 4.3 events/models.py（3モデル定義）

#### Event（作品）
| フィールド | 型 | 備考 |
|-----------|-----|------|
| title | CharField(200) | 作品名 |
| slug | SlugField(unique) | URL用スラッグ |
| description | TextField(blank) | 説明 |
| organizer_name | CharField(200, blank) | 主催者名。将来 tenant FK 化の余地 |
| organizer_email | EmailField(blank) | 主催者メール |
| created_at | DateTimeField(auto_now_add) | |
| updated_at | DateTimeField(auto_now) | |

- ordering: `-created_at`
- `__str__`: title

#### Performance（公演回）
| フィールド | 型 | 備考 |
|-----------|-----|------|
| event | FK(Event, CASCADE) | related_name="performances" |
| label | CharField(200) | "3/30 14:00 マチネ" 等 |
| starts_at | DateTimeField | 開演時刻 |
| open_at | DateTimeField | 開場時刻 |
| created_at | DateTimeField(auto_now_add) | |
| updated_at | DateTimeField(auto_now) | |

- ordering: `starts_at`
- `__str__`: `{event.title} / {label}`

#### SeatTier（席種）
| フィールド | 型 | 備考 |
|-----------|-----|------|
| performance | FK(Performance, CASCADE) | related_name="seat_tiers" |
| code | CharField(20, choices) | TextChoices: front_row/front/center/rear |
| name | CharField(50) | 表示名（"最前席" 等）。code と分離 |
| capacity | PositiveIntegerField | 定員 |
| price_card | PositiveIntegerField | カード決済価格（円） |
| price_cash | PositiveIntegerField | 現金価格（円） |
| sort_order | PositiveSmallIntegerField(default=0) | 表示順 |

- ordering: `sort_order`
- constraint: `UniqueConstraint(fields=["performance", "code"])` — 同一公演で同じ席種コードは1つだけ
- TierCode の TextChoices に表示名も定義しているが、name フィールドを別途持つことで、同じ code でも公演ごとに表示名を変えられる

**設計判断:**
- SeatTier を Performance 単位に持たせた理由: 公演ごとに席数・価格を変えたいケース（千秋楽増席等）に対応するため
- price は PositiveIntegerField（円単位の整数）。Decimal にしなかった理由: 日本円は小数点以下不要
- 招待(invite)は予約種別で管理し、SeatTier としては rear の在庫を消費する（モデル上の特別扱いなし）

### 4.4 events/admin.py

| クラス | 種別 | 内容 |
|--------|------|------|
| PerformanceInline | TabularInline | Event 編集画面に Performance を表示（extra=1） |
| SeatTierInline | TabularInline | Performance 編集画面に SeatTier を表示（extra=4、4席種分） |
| EventAdmin | ModelAdmin | list_display: title/slug/created_at、slug 自動入力 |
| PerformanceAdmin | ModelAdmin | list_display: event/label/starts_at、event フィルタ |
| SeatTierAdmin | ModelAdmin | list_display: performance/code/name/capacity/price_card/price_cash |

---

## 5. 動作確認結果

| コマンド | 結果 |
|---------|------|
| `python manage.py makemigrations events` | `events/migrations/0001_initial.py` 生成。Event, Performance, SeatTier の3テーブル + constraint |
| `python manage.py migrate` | 全 migration 適用成功（auth, admin, contenttypes, sessions, events） |
| `python manage.py check` | `System check identified no issues (0 silenced)` |

---

## 6. 未着手・残存事項

| 項目 | 状態 | 備考 |
|------|------|------|
| db.sqlite3 | 残存 | PostgreSQL に切り替えたため不要。削除してよい |
| .env ファイル | 未作成 | 現時点はデフォルト値で動作。本番前に作成必要 |
| .gitignore | 未作成（ルート） | frontend/.gitignore はあるがルートにはない |
| Procfile | 未作成 | `web: gunicorn config.wsgi` になる予定 |
| runtime.txt | 未作成 | Heroku 用 Python バージョン指定 |
| events の API (serializer/views/urls) | 未着手 | 次ステップ (Step 3) |
| reservations app | 未着手 | Step 4 |
| payments app | 未着手 | Step 6 |
| notifications app | 未着手 | Step 9 |

---

## 7. 次ステップの候補

**Step 3:** events の serializer + views + urls（API 公開）
- `events/serializers.py`, `events/views.py`, `events/urls.py`, `config/urls.py`

**Step 4:** reservations app のモデル定義 + admin
- Reservation モデル（performance, seat_tier, quantity, token, guest_*, reservation_type, status, payment_status, checked_in 等）

---

## 8. 現在のディレクトリ構成

```
Mogi/
├── manage.py
├── compose.yml
├── requirements.txt              ← 新規
├── db.sqlite3                    ← 残存（不要）
├── config/
│   ├── __init__.py
│   ├── settings.py               ← 全面書き換え
│   ├── urls.py                   ← 未変更
│   ├── wsgi.py                   ← 未変更
│   └── asgi.py                   ← 未変更
├── events/                       ← 新規 app
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                 ← Event, Performance, SeatTier
│   ├── admin.py                  ← 3モデル登録 + インライン
│   ├── views.py                  （空）
│   ├── tests.py                  （空）
│   └── migrations/
│       ├── __init__.py
│       └── 0001_initial.py       ← 自動生成
├── frontend/                     （対象外）
└── venv/                         （対象外）
```
