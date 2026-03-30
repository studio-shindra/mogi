# 作業報告書: バックエンド — reservations API 一式 + SeatTier remaining

- 日時: 2026-03-30 15:22
- 作業者: Claude (Opus 4.6)
- プロジェクト: Mogi（演劇向け最小票券管理システム）

---

## 1. 目的

reservations の全 API エンドポイント（7本）を実装し、
events の SeatTierSerializer に remaining を追加する。
Stripe は含めない。

---

## 2. 変更ファイル一覧

| ファイル | 操作 | 概要 |
|---------|------|------|
| `reservations/serializers.py` | 新規 | 5つの serializer |
| `reservations/views.py` | 書き換え | 7つの API view |
| `reservations/urls.py` | 新規 | 7エンドポイント定義 |
| `config/urls.py` | 編集 | reservations.urls を include 追加 |
| `events/serializers.py` | 編集 | SeatTierSerializer に remaining 追加 |
| `events/views.py` | 書き換え | annotate で _confirmed_qty を付与 |

---

## 3. API エンドポイント一覧

### Public（認証不要）

| メソッド | URL | view | 説明 |
|---------|-----|------|------|
| POST | `/api/reservations/` | reservation_create | 予約作成 |
| GET | `/api/reservations/<token>/` | reservation_by_token | 予約確認（token） |
| POST | `/api/reservations/<token>/checkin/` | reservation_checkin | セルフチェックイン |

### Staff（認証必須）

| メソッド | URL | view | 説明 |
|---------|-----|------|------|
| GET | `/api/staff/reservations/` | staff_reservation_list | 予約検索 |
| POST | `/api/staff/reservations/walk-in/` | staff_walk_in | 当日券作成 |
| POST | `/api/staff/reservations/<id>/mark-paid/` | staff_mark_paid | 現金受領 |
| POST | `/api/staff/reservations/<id>/check-in/` | staff_check_in | 入場処理 |

---

## 4. 各ファイルの詳細

### 4.1 reservations/serializers.py

| クラス | 用途 |
|--------|------|
| ReservationPerformanceSerializer | 予約確認用の公演情報（id, label, starts_at, event_title, venue_name） |
| ReservationSeatTierSerializer | 予約確認用の席種情報（id, name, code） |
| ReservationCreateSerializer | 予約作成の入力バリデーション + create() |
| ReservationDetailSerializer | 予約確認のレスポンス（can_self_checkin, checkin_opens_at 含む） |
| StaffReservationSerializer | 受付用一覧のレスポンス（memo 含む） |
| WalkInCreateSerializer | 当日券作成の入力バリデーション + create() |

#### ReservationCreateSerializer のバリデーション

| チェック | エラーメッセージ |
|---------|----------------|
| Performance 存在 | 「公演が見つかりません」 |
| SeatTier 存在 | 「席種が見つかりません」 |
| seat_tier.performance == performance | 「この席種は指定した公演に属していません」 |
| invite は rear のみ | 「招待は後方席のみ指定できます」 |
| card はメール必須 | 「カード決済の場合はメールアドレスが必要です」 |
| 在庫チェック（capacity - confirmed qty >= quantity） | 「残席が不足しています。{席種名}: 残り{N}枚」 |

在庫チェックの計算: `status in [pending, confirmed]` の quantity 合計を使用。
pending も在庫消費に含める理由: Stripe 決済中の予約が在庫を確保する必要があるため。

#### create() の初期状態

| reservation_type | status | payment_status |
|-----------------|--------|---------------|
| card | pending | unpaid |
| cash | confirmed | unpaid |
| invite | confirmed | paid |

#### ReservationDetailSerializer の算出フィールド

- `can_self_checkin`: (!checked_in) AND (type != cash) AND (confirmed + paid) AND (now >= starts_at - 1h)
- `checkin_opens_at`: starts_at - 1h

### 4.2 reservations/views.py

#### reservation_create (POST)

- AllowAny
- ReservationCreateSerializer でバリデーション + 作成
- レスポンス: ReservationDetailSerializer (201)

#### reservation_by_token (GET)

- AllowAny
- token で Reservation を取得（select_related: performance.event, seat_tier）
- 404: 「予約が見つかりません」

#### reservation_checkin (POST)

- AllowAny
- バリデーション順:
  1. token で取得（404）
  2. checked_in 済み（400）
  3. cash は不可（400）
  4. confirmed + paid チェック（400）
  5. 開演1h前チェック（400: 「チェックイン可能時間前です（HH:MM から）」）
- 成功: checked_in=True, checked_in_at=now を保存

#### staff_reservation_list (GET)

- IsAuthenticated
- クエリパラメータ: `performance`（公演ID）, `search`（テキスト）
- search: guest_name, guest_email, guest_phone, token の icontains OR
- 上限 200 件
- レスポンス: `{ count, results }`

#### staff_mark_paid (POST)

- IsAuthenticated
- payment_status が paid なら 400
- payment_status → paid に更新

#### staff_check_in (POST)

- IsAuthenticated
- checked_in なら 400
- checked_in=True, checked_in_at=now に更新
- **セルフチェックインとの違い**: reservation_type 制限なし、時間制限なし

#### staff_walk_in (POST)

- IsAuthenticated
- WalkInCreateSerializer でバリデーション + 作成
- 自動: type=cash, status=confirmed, payment_status=paid

### 4.3 events/serializers.py（差分）

SeatTierSerializer に `remaining` フィールド追加:
```python
remaining = serializers.SerializerMethodField()

def get_remaining(self, obj):
    confirmed_qty = getattr(obj, "_confirmed_qty", None)
    if confirmed_qty is not None:
        return obj.capacity - confirmed_qty
    # フォールバック
    ...
```

- annotate で `_confirmed_qty` が付いていればそれを使う（N+1 防止）
- 付いていない場合はフォールバックでクエリ発行

### 4.4 events/views.py（差分）

EventViewSet と PerformanceViewSet の queryset を annotate 対応に変更:
```python
SeatTier.objects.annotate(
    _confirmed_qty=Coalesce(
        Sum("reservations__quantity",
            filter=Q(reservations__status__in=["pending", "confirmed"])),
        Value(0),
    ),
)
```

- Event の retrieve (詳細) と Performance の list/retrieve で annotate を実行
- Event の list (一覧) では seat_tiers を返さないので annotate なし

---

## 5. 実行コマンドと動作確認結果

| コマンド | 結果 |
|---------|------|
| `python manage.py check` | `System check identified no issues (0 silenced)` |
| URL パターン一覧 | 全7エンドポイント + 既存4エンドポイント 正常登録 |
| 存在しない公演で予約作成 | 400 `{"performance_id": ["公演が見つかりません"]}` |
| 存在しない token で確認 | 404 `{"detail": "予約が見つかりません"}` |

migration は不要（モデル変更なし）。

---

## 6. API エンドポイント × フロント画面の対応

| API | フロント画面 | mock→real 切替対象 |
|-----|------------|-------------------|
| POST /api/reservations/ | ReserveView (Step 3 確定) | api/reservations.js |
| GET /api/reservations/:token/ | ReservationConfirmView | api/reservations.js |
| POST /api/reservations/:token/checkin/ | CheckinView | api/reservations.js |
| GET /api/staff/reservations/ | StaffDashboardView | composables/useStaffActions.js |
| POST .../mark-paid/ | StaffDashboardView | composables/useStaffActions.js |
| POST .../check-in/ | StaffDashboardView | composables/useStaffActions.js |
| POST .../walk-in/ | StaffDashboardView | composables/useStaffActions.js |
| GET /api/events/:slug/ (remaining) | EventDetailView | api/events.js |

---

## 7. 未着手・残存事項

| 項目 | 備考 |
|------|------|
| Stripe Checkout API | POST /api/reservations/:id/checkout/ は次ターン |
| SeatTier データ投入 | admin から投入（価格・定員が確定次第） |
| フロント mock→real 切替 | api/client.js + api/*.js の実装 |
| /staff 認証ガード（フロント） | router.beforeEach |
| superuser 作成 | `createsuperuser` でスタッフ用アカウント作成 |
| CSRF 設定 | SPA 向けに CSRF_TRUSTED_ORIGINS or SessionAuthentication の設定が必要 |

---

## 8. 次ステップ

**選択肢A（推奨）:** Stripe Checkout API を刻んで実装
- `payments/services.py`, `payments/views.py`, `payments/urls.py`
- POST /api/reservations/:id/checkout/
- Stripe webhook

**選択肢B:** フロントの mock→real 切替を先にやる
- api/client.js, api/events.js, api/reservations.js
- Stripe 以外の全 API を先に繋ぐ

---

## 9. 現在のディレクトリ構成（差分のみ）

```
Mogi/
├── config/
│   └── urls.py                   ← reservations.urls 追加
├── events/
│   ├── serializers.py            ← remaining 追加
│   └── views.py                  ← annotate 対応
├── reservations/
│   ├── serializers.py            ← 新規: 5つの serializer
│   ├── views.py                  ← 書き換え: 7つの view
│   └── urls.py                   ← 新規: 7エンドポイント
└── docs/
    └── 20260330-1522-backend-reservations-api.md  ← 本報告書
```
