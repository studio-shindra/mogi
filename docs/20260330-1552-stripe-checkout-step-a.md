# 作業報告書: Stripe Step A — Checkout Session 作成 + フロント redirect

- 日時: 2026-03-30 15:52
- 作業者: Claude (Opus 4.6)
- プロジェクト: Mogi（演劇向け最小票券管理システム）

---

## 1. 目的

Stripe Checkout Session の作成 API を実装し、フロントの card 予約フローで Stripe 決済画面にリダイレクトできるようにする。webhook はまだやらない。

---

## 2. 変更ファイル一覧

| ファイル | 操作 | 概要 |
|---------|------|------|
| `payments/services.py` | 新規 | create_checkout_session（Stripe API 呼び出し） |
| `payments/views.py` | 書き換え | checkout view（POST /api/reservations/:id/checkout/） |
| `payments/urls.py` | 新規 | checkout エンドポイント |
| `config/urls.py` | 編集 | payments.urls を include |
| `config/settings.py` | 編集 | payments を INSTALLED_APPS に追加、CSRF_TRUSTED_ORIGINS 追加、SITE_URL 追加 |
| `frontend/src/api/reservations.js` | 編集 | startCheckout 関数追加 |
| `frontend/src/views/ReserveView.vue` | 編集 | card 時に startCheckout → window.location.href でリダイレクト |

---

## 3. 各ファイルの詳細

### 3.1 payments/services.py

```python
def create_checkout_session(reservation):
```

- Stripe Checkout Session を作成
- `mode="payment"`（一回決済）
- `line_items`: 席種名 × quantity、price_card の金額
- `success_url`: `{SITE_URL}/reservation/{token}?checkout=success`
- `cancel_url`: `{SITE_URL}/reservation/{token}?checkout=cancel`
- `client_reference_id`: reservation.pk
- `metadata`: reservation_id, reservation_token（webhook で使用予定）
- `customer_email`: guest_email（Stripe 画面にプリフィル）
- session.id を reservation.stripe_checkout_session_id に保存
- session.url を返す

**設計判断:**
- success/cancel URL は予約確認ページに戻す。checkout=success/cancel クエリで状態が分かる
- 将来テナント化: `stripe_account` パラメータを足すだけで Connect 対応可能
- API Key は settings.STRIPE_SECRET_KEY から取得（単一アカウント前提）

### 3.2 payments/views.py — checkout

```
POST /api/reservations/<id>/checkout/
→ 200 { "checkout_url": "https://checkout.stripe.com/..." }
→ 400 "この予約は Stripe 対象ではありません"
→ 400 "この予約はすでに処理済みです"
→ 502 "Stripe エラー: ..."
```

バリデーション:
1. reservation_type == "card" のみ
2. status == "pending" のみ（confirmed 済みは不可）
3. Stripe API エラーは 502 で返す

認証: AllowAny（予約確認ページから直接呼べるように）

### 3.3 config/settings.py（差分）

追加:
```python
# CSRF
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="...", cast=Csv())

# Stripe
SITE_URL = config("SITE_URL", default="http://localhost:5173")
```

- CSRF_TRUSTED_ORIGINS: フロント → Django の POST リクエストで必要
- SITE_URL: Stripe の success/cancel URL 生成用

### 3.4 frontend の変更

#### api/reservations.js
```javascript
export async function startCheckout(reservationId) {
  const { data } = await client.post(`/reservations/${reservationId}/checkout/`)
  return data
}
```

#### ReserveView.vue — handleSubmit()
```javascript
if (form.reservationType.value === 'card') {
  const { checkout_url } = await startCheckout(result.id)
  window.location.href = checkout_url  // Stripe にリダイレクト
} else {
  router.push({ name: 'reservation-confirm', params: { token: result.token } })
}
```

---

## 4. card 予約の完全フロー（現状）

```
1. ReserveView Step 1-3 で予約情報入力
2. handleSubmit()
   → POST /api/reservations/  (status=pending, payment_status=unpaid)
   → POST /api/reservations/:id/checkout/  (Stripe Session 作成)
   → window.location.href = checkout_url  (Stripe 決済画面)
3. Stripe 決済完了
   → success_url: /reservation/:token?checkout=success
   → 予約確認ページに戻る
4. ※ この時点では status=pending のまま（webhook 未実装）
```

**webhook 実装後:**
- Stripe が checkout.session.completed を POST
- status → confirmed, payment_status → paid に更新
- 予約確認ページで「確定」「支払済」が表示される

---

## 5. 実行コマンドと動作確認結果

| コマンド | 結果 |
|---------|------|
| `pip install stripe` | stripe 15.0.0 インストール成功 |
| `python manage.py check` | `System check identified no issues (0 silenced)` |
| `npx vite build` | ビルド成功（282ms） |
| URL パターン一覧 | `api/reservations/<int:pk>/checkout/ [reservation-checkout]` 登録確認 |

---

## 6. 動作確認に必要な設定

Stripe Checkout を実際にテストするには `.env` に以下を設定:

```
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
SITE_URL=http://localhost:5173
```

テストモードの API キーで動作確認可能。

---

## 7. 未着手・残存事項

| 項目 | 備考 |
|------|------|
| Stripe webhook | checkout.session.completed → status/payment_status 更新。次ターン |
| pending の寿命管理 | Stripe 未決済のまま放置された pending 予約の在庫解放。webhook 後に検討 |
| ReservationConfirmView の checkout=success 表示 | クエリパラメータでメッセージを出す（任意） |
| エラー時の UX | Stripe エラー時にフロントでメッセージ表示（submitError で対応済み） |

---

## 8. 次ステップ

**Stripe Step B:** webhook
- `payments/views.py` に webhook view 追加
- `payments/urls.py` に webhook URL 追加
- checkout.session.completed で reservation の status → confirmed, payment_status → paid
- CSRF exempt 設定
- Stripe 署名検証

---

## 9. 現在のディレクトリ構成（差分のみ）

```
Mogi/
├── config/
│   ├── settings.py               ← payments追加, CSRF, SITE_URL
│   └── urls.py                   ← payments.urls include
├── payments/                     ← 新規 app
│   ├── __init__.py
│   ├── apps.py
│   ├── services.py               ← create_checkout_session
│   ├── views.py                  ← checkout view
│   ├── urls.py                   ← checkout endpoint
│   ├── models.py                 （空）
│   └── ...
├── frontend/src/
│   ├── api/
│   │   └── reservations.js       ← startCheckout 追加
│   └── views/
│       └── ReserveView.vue       ← card → Stripe redirect
└── docs/
    └── 20260330-1552-stripe-checkout-step-a.md  ← 本報告書
```
