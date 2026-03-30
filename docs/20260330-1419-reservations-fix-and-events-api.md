# 作業報告書: Mogi バックエンド Step 3修正 + Step 4a — reservations 修正 & events API

- 日時: 2026-03-30 14:19
- 作業者: Claude (Opus 4.6)
- プロジェクト: Mogi（演劇向け最小票券管理システム）

---

## 1. 作業の目的

1. 前回レビューで指摘された reservations モデルの2点を修正
2. events app の API（serializer / views / urls）を実装し、公開エンドポイントを通す

---

## 2. 前回レビューからの反映事項

| 指摘 | 対応 |
|------|------|
| guest_email を必須にしない（招待・当日券でメールなし運用あり） | `blank=True` に変更 |
| token の実装と説明のズレ（uuid4 の hex vs str） | `_generate_token()` ヘルパーで `uuid.uuid4().hex` を使用。max_length=32 に変更。ハイフンなし32文字に統一 |
| events + reservations API を一気にやらず分割する | 本ステップは events API のみ。reservations API は次ステップ |

---

## 3. 変更ファイル一覧

| ファイル | 操作 | 概要 |
|---------|------|------|
| `reservations/models.py` | 編集 | guest_email に blank=True 追加、token を hex 32文字に修正 |
| `reservations/migrations/0002_alter_reservation_guest_email_and_more.py` | 自動生成 | 上記変更の migration |
| `events/serializers.py` | 新規作成 | EventSerializer, EventListSerializer, PerformanceSerializer, SeatTierSerializer |
| `events/views.py` | 書き換え | EventViewSet, PerformanceViewSet |
| `events/urls.py` | 新規作成 | router + ネスト URL |
| `config/urls.py` | 書き換え | `api/` prefix で events.urls を include |

---

## 4. 各ファイルの詳細

### 4.1 reservations/models.py（差分）

#### 変更1: guest_email

```python
# Before
guest_email = models.EmailField("メール")

# After
guest_email = models.EmailField("メール", blank=True)
```

- 招待や当日券でメールなし運用を許容するため
- null=True は付けていない。空文字列 `""` で保存される。EmailField で null を許可すると「NULL と空文字の2種類の空」が生じて扱いにくいため

#### 変更2: token

```python
# Before
token = models.CharField(
    max_length=64,
    unique=True,
    default=uuid.uuid4,   # → str(UUID) でハイフン付き36文字になる
)

# After
def _generate_token():
    return uuid.uuid4().hex  # ハイフンなし32文字

token = models.CharField(
    max_length=32,
    unique=True,
    default=_generate_token,
)
```

- `uuid.uuid4().hex` → `"a1b2c3d4e5f6..."` 形式の32文字
- URL に使うのでハイフンなしの方が扱いやすい
- max_length も 64 → 32 に修正（32文字固定なので余分な枠は不要）

### 4.2 events/serializers.py（新規作成）

| クラス | 用途 | fields |
|--------|------|--------|
| SeatTierSerializer | 席種の詳細 | id, code, name, capacity, price_card, price_cash, sort_order |
| PerformanceSerializer | 公演の詳細。seat_tiers をネスト | id, label, starts_at, open_at, seat_tiers |
| EventSerializer | 作品の詳細。performances をネスト | id, title, slug, description, performances |
| EventListSerializer | 作品の一覧用。ネストなし | id, title, slug |

**設計判断:**
- 一覧（list）と詳細（retrieve）で serializer を分けた理由: 一覧で全公演・全席種をネストするとレスポンスが肥大化する
- すべて read_only のネスト。書き込みは admin 画面から行う前提（MVP）
- organizer_name / organizer_email は公開 API に含めない（管理者情報のため）

### 4.3 events/views.py（書き換え）

#### EventViewSet

```python
class EventViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Event.objects.prefetch_related("performances__seat_tiers")
    permission_classes = [AllowAny]
    lookup_field = "slug"
```

- `ReadOnlyModelViewSet` — list / retrieve のみ
- `permission_classes = [AllowAny]` — 公開 API。settings の DEFAULT_PERMISSION は IsAuthenticated だが、作品情報は認証不要
- `lookup_field = "slug"` — `/api/events/my-event-slug/` でアクセス
- `prefetch_related` で N+1 を防止

#### PerformanceViewSet

```python
class PerformanceViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = PerformanceSerializer

    def get_queryset(self):
        return Performance.objects.filter(
            event__slug=self.kwargs["event_slug"],
        ).prefetch_related("seat_tiers")
```

- URL の `event_slug` で親 Event を絞り込み
- ネストされた URL: `/api/events/<slug>/performances/`

### 4.4 events/urls.py（新規作成）

```python
router = DefaultRouter()
router.register(r"events", views.EventViewSet, basename="event")

urlpatterns = [
    path("", include(router.urls)),
    path("events/<slug:event_slug>/performances/", ...list...),
    path("events/<slug:event_slug>/performances/<int:pk>/", ...detail...),
]
```

- Event は DefaultRouter で自動登録
- Performance はネスト URL のため手動で `as_view()` を使用
- `basename="event"` を明示（queryset が固定なので省略可能だが明示的に）

### 4.5 config/urls.py（書き換え）

```python
urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("events.urls")),
]
```

- 全 API に `api/` prefix を付与
- 将来 reservations.urls も `api/` 配下に追加する

---

## 5. API エンドポイント一覧

| メソッド | URL | 説明 | 認証 |
|---------|-----|------|------|
| GET | `/api/events/` | 作品一覧 | 不要 |
| GET | `/api/events/<slug>/` | 作品詳細（公演・席種ネスト） | 不要 |
| GET | `/api/events/<slug>/performances/` | 公演一覧（席種ネスト） | 不要 |
| GET | `/api/events/<slug>/performances/<id>/` | 公演詳細（席種ネスト） | 不要 |

---

## 6. 実行コマンドと動作確認結果

| コマンド | 結果 |
|---------|------|
| `python manage.py makemigrations` | `reservations/migrations/0002` 生成（guest_email + token 変更） |
| `python manage.py migrate` | `Applying reservations.0002... OK` |
| `python manage.py check` | `System check identified no issues (0 silenced)` |
| URL パターン一覧出力 | `api/^events/$`, `api/^events/(?P<slug>...)/$`, `api/events/<slug>/performances/`, `api/events/<slug>/performances/<int:pk>/` すべて登録確認 |

---

## 7. 未着手・残存事項

| 項目 | 状態 | 備考 |
|------|------|------|
| .env ファイル | 未作成 | デフォルト値で動作中 |
| .gitignore（ルート） | 未作成 | |
| Procfile / runtime.txt | 未作成 | |
| reservations の API | 未着手 | Step 4b（次ステップ） |
| payments app | 未着手 | Step 5 |
| notifications app | 未着手 | |
| 在庫チェックロジック | 未着手 | reservations view で実装予定 |
| CSVインポート | 未着手 | |
| API テスト | 未着手 | テストデータ投入後に動作確認推奨 |

---

## 8. 次ステップ

**Step 4b:** reservations の API（serializer / views / urls）

対象ファイル:
- `reservations/serializers.py` — 予約作成・一覧・詳細用 serializer
- `reservations/views.py` — 予約作成、トークン確認、チェックイン、受付操作
- `reservations/urls.py` — エンドポイント定義
- `config/urls.py` — reservations.urls の include 追加

重要な実装ポイント:
- 在庫チェック（seat_tier の capacity vs confirmed 予約数の quantity 合計）
- reservation_type ごとの初期状態設定
- seat_tier.performance == performance の整合性バリデーション
- invite は rear 席種のみ許可
- quantity の上限バリデーション（1〜10 程度）

---

## 9. 現在のディレクトリ構成

```
Mogi/
├── manage.py
├── compose.yml
├── requirements.txt
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py                   ← api/ include 追加
│   ├── wsgi.py
│   └── asgi.py
├── events/
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                 ← Event, Performance, SeatTier
│   ├── admin.py                  ← 3モデル登録
│   ├── serializers.py            ← 新規: 4つの serializer
│   ├── views.py                  ← 書き換え: 2つの ViewSet
│   ├── urls.py                   ← 新規: router + ネスト URL
│   ├── tests.py                  （空）
│   └── migrations/
│       ├── __init__.py
│       └── 0001_initial.py
├── reservations/
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py                 ← guest_email + token 修正済み
│   ├── admin.py
│   ├── views.py                  （空）
│   ├── tests.py                  （空）
│   └── migrations/
│       ├── __init__.py
│       ├── 0001_initial.py
│       └── 0002_alter_reservation_guest_email_and_more.py  ← 新規
├── docs/
│   ├── 20260330-1400-backend-step1-settings-and-events-models.md
│   ├── 20260330-1407-reservations-model.md
│   └── 20260330-1419-reservations-fix-and-events-api.md   ← 本報告書
├── frontend/                     （対象外）
└── venv/                         （対象外）
```
