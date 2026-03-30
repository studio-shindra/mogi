# 作業報告書: フロントエンド mock→real 切替（Stripe 以外）

- 日時: 2026-03-30 15:32
- 作業者: Claude (Opus 4.6)
- プロジェクト: Mogi（演劇向け最小票券管理システム）

---

## 1. 目的

フロントエンドの全画面を mock データから real API に切り替える（Stripe 以外）。
`VITE_USE_MOCK=true` で mock にフォールバック可能な設計を維持する。

---

## 2. 変更ファイル一覧

| ファイル | 操作 | 概要 |
|---------|------|------|
| `frontend/vite.config.js` | 編集 | server.proxy 追加（/api → localhost:8000） |
| `frontend/src/api/client.js` | 新規 | axios インスタンス + CSRF トークン自動送信 |
| `frontend/src/api/events.js` | 新規 | fetchEvents, fetchEventDetail（mock/real 切替） |
| `frontend/src/api/reservations.js` | 新規 | 予約・チェックイン・受付操作の API 呼び出し（mock/real 切替） |
| `frontend/src/views/EventDetailView.vue` | 編集 | mock → api/events.js + エラーハンドリング |
| `frontend/src/views/ReserveView.vue` | 編集 | mock → api/events.js + api/reservations.js + 予約確認ページ遷移 |
| `frontend/src/views/ReservationConfirmView.vue` | 編集 | mock → api/reservations.js + 404 ハンドリング |
| `frontend/src/views/CheckinView.vue` | 編集 | mock → api/reservations.js + API エラー表示 |
| `frontend/src/composables/useStaffActions.js` | 書き換え | mock → api/reservations.js |

---

## 3. 各ファイルの詳細

### 3.1 vite.config.js

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
},
```

- 開発時に Vite dev server から Django に `/api` リクエストをプロキシ
- 本番では Heroku が同一ドメインで Django を配信するので proxy 不要

### 3.2 api/client.js

- `baseURL: '/api'`
- `withCredentials: true`（Django session cookie を送る）
- request interceptor で `csrftoken` cookie を `X-CSRFToken` ヘッダーに自動設定

### 3.3 api/events.js

| 関数 | mock 時 | real 時 |
|------|---------|---------|
| fetchEvents() | mockEvents を返す | GET /api/events/ |
| fetchEventDetail(slug) | mockEventDetail を返す | GET /api/events/:slug/ |

`VITE_USE_MOCK` 環境変数で切替。

### 3.4 api/reservations.js

| 関数 | mock 時 | real 時 |
|------|---------|---------|
| createReservation(payload) | console.log | POST /api/reservations/ |
| fetchReservation(token) | findMockReservation | GET /api/reservations/:token/ |
| checkin(token) | 即成功を返す | POST /api/reservations/:token/checkin/ |
| staffSearchReservations(perfId, search) | searchMockReservations | GET /api/staff/reservations/ |
| staffMarkPaid(id) | 即成功を返す | POST /api/staff/reservations/:id/mark-paid/ |
| staffCheckIn(id) | 即成功を返す | POST /api/staff/reservations/:id/check-in/ |
| staffWalkIn(payload) | console.log | POST /api/staff/reservations/walk-in/ |

### 3.5 view の変更まとめ

| view | 変更点 |
|------|--------|
| EventDetailView | fetchEventDetail(slug) を try/catch で呼び出し。エラー時 alert 表示 |
| ReserveView | fetchEventDetail で公演取得。handleSubmit で createReservation → 予約確認ページに router.push。submitError 表示追加 |
| ReservationConfirmView | fetchReservation(token) を try/catch で呼び出し。404 時 notFound フラグ |
| CheckinView | fetchReservation + checkin を try/catch。エラーは API の detail メッセージを表示 |

### 3.6 ReserveView の予約送信フロー（Stripe 暫定）

```
handleSubmit()
  → createReservation(payload)  // POST /api/reservations/
  → if card:
      // TODO: POST /api/reservations/:id/checkout/ → Stripe redirect
      // 暫定: 予約確認ページに遷移（pending/unpaid 状態で表示される）
      router.push({ name: 'reservation-confirm', params: { token } })
  → if cash:
      router.push({ name: 'reservation-confirm', params: { token } })
```

card の場合、Stripe 実装後は checkout API → redirect に変わる。

### 3.7 composables/useStaffActions.js

全関数を api/reservations.js の関数呼び出しに差し替え:
- `search()` → `staffSearchReservations()`
- `markPaid()` → `staffMarkPaid()`
- `checkIn()` → `staffCheckIn()`
- `createWalkIn()` → `staffWalkIn()`

エラーハンドリング: search は catch で空配列、他は呼び出し元に throw。

---

## 4. mock/real 切替方式

```bash
# mock モード（API 不要で動く）
VITE_USE_MOCK=true npm run dev

# real モード（Django runserver が必要）
npm run dev
```

- `VITE_USE_MOCK` を設定しなければ real（デフォルト）
- mock ファイルは削除せず残す（開発・テスト用）
- 本番ビルドでは mock コードは tree-shake で除外される（USE_MOCK が false のため）

---

## 5. 実行コマンドと動作確認結果

| コマンド | 結果 |
|---------|------|
| `npx vite build` | ビルド成功（330ms） |

ビルド出力（主要 chunk）:
- `client-*.js`: 36.43 kB（axios）
- `reservations-*.js`: 0.96 kB（API 関数）
- `events-*.js`: 0.15 kB（API 関数） + 3.29 kB（mock データ）
- `ReserveView-*.js`: 12.29 kB
- `StaffDashboardView-*.js`: 8.74 kB

---

## 6. 動作確認に必要な手順（real モード）

```bash
# 1. Django 起動
python manage.py runserver

# 2. フロント起動
cd frontend && npm run dev

# 3. ブラウザで http://localhost:5173/paradise-effect にアクセス
```

注意: SeatTier が未投入の場合、公演一覧のカードに席種情報が表示されません。
admin で SeatTier を登録してから確認してください。

---

## 7. 未着手・残存事項

| 項目 | 備考 |
|------|------|
| Stripe Checkout API | POST /api/reservations/:id/checkout/ → 次ターン |
| ReserveView の card 分岐 | 暫定で予約確認ページに遷移。Stripe 後に checkout redirect に差し替え |
| CSRF 設定（Django側） | CSRF_TRUSTED_ORIGINS にフロントの origin を追加する必要あり |
| /staff 認証ガード（フロント） | router.beforeEach で 401 チェック |
| SeatTier データ投入 | admin から投入。これがないと予約フォームが空 |
| EventListView | まだスタブ。優先度低 |
| superuser 作成 | staff API を使うために必要 |

---

## 8. 次ステップ

**推奨:** Stripe Checkout API
- `payments/services.py` — create_checkout_session
- `payments/views.py` — checkout + webhook
- `payments/urls.py`
- ReserveView の card 分岐を本接続

---

## 9. 現在のディレクトリ構成（差分のみ）

```
frontend/src/
├── api/
│   ├── client.js                ← 新規: axios + CSRF
│   ├── events.js                ← 新規: mock/real 切替
│   └── reservations.js          ← 新規: mock/real 切替
├── composables/
│   └── useStaffActions.js       ← 書き換え: API 接続
├── views/
│   ├── EventDetailView.vue      ← 編集: API + エラー
│   ├── ReserveView.vue          ← 編集: API + 予約送信 + エラー
│   ├── ReservationConfirmView.vue ← 編集: API + 404
│   ├── CheckinView.vue          ← 編集: API + エラー
│   └── StaffDashboardView.vue   ← 変更なし（useStaffActions 経由で切替済み）
└── ...
```
