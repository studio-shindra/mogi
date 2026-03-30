# 作業報告書: Stripe Step B — checkout token 化 + webhook

- 日時: 2026-03-30 15:59
- 作業者: Claude (Opus 4.6)
- プロジェクト: Mogi（演劇向け最小票券管理システム）

---

## 1. 目的

1. checkout エンドポイントを数値 ID → token ベースに修正（セキュリティ改善）
2. Stripe webhook を実装し、決済完了時に予約を confirmed/paid に更新する

---

## 2. 変更ファイル一覧

| ファイル | 操作 | 概要 |
|---------|------|------|
| `reservations/views.py` | 編集 | reservation_checkout を追加（token ベース） |
| `reservations/urls.py` | 編集 | `<str:token>/checkout/` を追加 |
| `payments/views.py` | 書き換え | checkout 削除、stripe_webhook + _handle_checkout_completed のみ |
| `payments/urls.py` | 書き換え | checkout 削除、webhook のみ |
| `frontend/src/api/reservations.js` | 編集 | startCheckout(id) → startCheckout(token) |
| `frontend/src/views/ReserveView.vue` | 編集 | startCheckout(result.id) → startCheckout(result.token) |

---

## 3. 各ファイルの詳細

### 3.1 checkout の token 化

**変更前:**
```
POST /api/reservations/<int:pk>/checkout/  (payments/views.py)
```

**変更後:**
```
POST /api/reservations/<str:token>/checkout/  (reservations/views.py)
```

- checkout view を payments/ → reservations/ に移動
- 理由: 他の token ベース API（確認, チェックイン）と同じ reservations/urls.py にまとめた方が URL 解決の衝突リスクが低い
- payments/services.py の create_checkout_session() は変更なし（reservations 側から呼ぶだけ）

### 3.2 stripe_webhook

```
POST /api/stripe/webhook/
```

- `@csrf_exempt` — Stripe からの POST には CSRF トークンがないため
- `stripe.Webhook.construct_event()` で署名検証
- `checkout.session.completed` イベントのみ処理
- 他のイベントは 200 で無視（Stripe が再送しないように）

#### _handle_checkout_completed(session)

1. `session.metadata.reservation_token` で予約を特定
2. 冪等チェック: `status == "pending"` の時だけ更新
3. `status → confirmed`, `payment_status → paid`
4. すでに confirmed なら何もしない（二重処理防止）

**設計判断:**
- metadata に reservation_token を入れているので、token で予約を特定できる
- client_reference_id（reservation.pk）も入っているが、token の方が安全
- checked_in とは無関係（チェックインはお客様の操作）

### 3.3 payments/ の責務整理

| ファイル | 責務 |
|---------|------|
| payments/services.py | Stripe API 呼び出し（create_checkout_session） |
| payments/views.py | webhook 受信のみ |
| payments/urls.py | `/api/stripe/webhook/` のみ |
| reservations/views.py | checkout view（token で予約を取得 → services.create_checkout_session を呼ぶ） |

### 3.4 フロント側の変更

```javascript
// Before
startCheckout(result.id)    // 数値 ID

// After
startCheckout(result.token) // token
```

---

## 4. card 予約の完全フロー（webhook 込み）

```
1. ReserveView: 予約情報入力
2. handleSubmit()
   → POST /api/reservations/          → status=pending, payment_status=unpaid
   → POST /api/reservations/:token/checkout/ → Stripe Session 作成
   → window.location.href = checkout_url     → Stripe 決済画面へ

3. Stripe 決済完了
   → success_url: /reservation/:token?checkout=success
   → ユーザーは予約確認ページに戻る

4. Stripe → POST /api/stripe/webhook/
   → checkout.session.completed
   → status=confirmed, payment_status=paid

5. 予約確認ページで「確定」「支払済」が表示される
```

---

## 5. API エンドポイント最終一覧

| メソッド | URL | 認証 | 説明 |
|---------|-----|------|------|
| GET | /api/events/ | 不要 | 作品一覧 |
| GET | /api/events/:slug/ | 不要 | 作品詳細（remaining 付き） |
| GET | /api/events/:slug/performances/ | 不要 | 公演一覧 |
| GET | /api/events/:slug/performances/:id/ | 不要 | 公演詳細 |
| POST | /api/reservations/ | 不要 | 予約作成 |
| GET | /api/reservations/:token/ | 不要 | 予約確認 |
| POST | /api/reservations/:token/checkin/ | 不要 | セルフチェックイン |
| POST | /api/reservations/:token/checkout/ | 不要 | Stripe Checkout 開始 |
| GET | /api/staff/reservations/ | 必須 | 受付検索 |
| POST | /api/staff/reservations/walk-in/ | 必須 | 当日券作成 |
| POST | /api/staff/reservations/:id/mark-paid/ | 必須 | 現金受領 |
| POST | /api/staff/reservations/:id/check-in/ | 必須 | 入場処理 |
| POST | /api/stripe/webhook/ | Stripe署名 | webhook |

合計 13 エンドポイント。

---

## 6. 実行コマンドと動作確認結果

| コマンド | 結果 |
|---------|------|
| `python manage.py check` | `System check identified no issues (0 silenced)` |
| `npx vite build` | ビルド成功（326ms） |
| URL パターン一覧 | 全13エンドポイント正常登録 |

---

## 7. webhook テストに必要な設定

```bash
# .env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Stripe CLI でローカルテスト
stripe listen --forward-to localhost:8000/api/stripe/webhook/
stripe trigger checkout.session.completed
```

---

## 8. 未着手・残存事項

| 項目 | 備考 |
|------|------|
| pending の寿命管理 | Stripe 未決済のまま放置された pending 予約の在庫解放（management command or celery） |
| checkout=success 時のフロント表示 | ReservationConfirmView でクエリパラメータを見て「決済完了」メッセージ（任意） |
| Stripe テスト実行 | .env に API キーを設定して stripe CLI で E2E テスト |
| notifications app | メール送信（リマインド、一括通知） |
| EventListView | スタブのまま |
| Heroku デプロイ設定 | Procfile, runtime.txt, whitenoise collectstatic |
| .gitignore | ルートに未作成 |
| superuser 作成 | staff API 用 |

---

## 9. 次ステップ候補

MVP としての主要機能は実装完了に近い。残りは:

1. **デプロイ準備**（Procfile, .gitignore, .env.example, collectstatic）
2. **notifications app**（メール送信、リマインド）
3. **EventListView**（優先度低）
4. **pending 予約の expire 処理**
5. **E2E テスト**（Stripe テストキーで一連のフロー確認）

---

## 10. 現在のディレクトリ構成（差分のみ）

```
Mogi/
├── reservations/
│   ├── views.py                  ← reservation_checkout 追加（token ベース）
│   └── urls.py                   ← checkout URL 追加
├── payments/
│   ├── services.py               ← 変更なし
│   ├── views.py                  ← stripe_webhook + _handle_checkout_completed のみ
│   └── urls.py                   ← webhook URL のみ
├── frontend/src/
│   ├── api/reservations.js       ← startCheckout(token)
│   └── views/ReserveView.vue     ← startCheckout(result.token)
└── docs/
    └── 20260330-1559-stripe-step-b-webhook.md  ← 本報告書
```
