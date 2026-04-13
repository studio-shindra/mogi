# Stripe 決済まわり計画レビュー

- 日時: 2026-04-13 16:20
- 目的: ローカルでの Stripe 決済確認手順と本番移行チェックリストの整理
- 種別: 計画レビュー（コード変更なし）

---

## 目的

Mogi の Stripe 決済フロー（予約作成 → Checkout → webhook → pending 失効）について、ローカル動作確認に必要な手順と、本番移行時に必要な設定を整理する。

---

## 変更ファイル一覧

なし（計画レビューのみ）

---

## 精査対象ファイル

| ファイル | 役割 |
|---------|------|
| `payments/services.py` | Stripe Checkout Session 作成 |
| `payments/views.py` | Webhook ハンドラ（checkout.session.completed） |
| `payments/urls.py` | `/api/stripe/webhook/` ルーティング |
| `reservations/views.py` | `/api/reservations/<token>/checkout/` endpoint |
| `reservations/urls.py` | checkout endpoint ルーティング |
| `reservations/models.py` | Reservation model（status, payment_status, stripe_checkout_session_id） |
| `reservations/management/commands/expire_pending.py` | pending 失効コマンド |
| `config/settings.py` | STRIPE_*, SITE_URL, CSRF_TRUSTED_ORIGINS |
| `.env` | 環境変数テンプレート |
| `frontend/src/api/reservations.js` | startCheckout() API コール |
| `frontend/src/views/ReserveView.vue` | card 選択時の Checkout リダイレクト |
| `frontend/src/views/ReservationConfirmView.vue` | success/cancel 表示、再決済ボタン |

---

## ローカル確認手順

```bash
# 1. PostgreSQL 起動
docker compose up -d

# 2. .env 編集（Stripe test key を記入）

# 3. Django 起動
python manage.py runserver

# 4. Stripe CLI で webhook 転送（別ターミナル）
stripe listen --forward-to localhost:8000/api/stripe/webhook/
# → 表示される whsec_xxx を .env に貼る

# 5. Django 再起動（.env 反映）

# 6. Frontend 起動（別ターミナル）
cd frontend && npm run dev

# 7. ブラウザで card 予約 → Checkout → success 確認
# 8. DB ステータス確認
python manage.py shell -c "from reservations.models import Reservation; r = Reservation.objects.last(); print(r.status, r.payment_status)"

# 9. Pending 失効テスト
python manage.py expire_pending --minutes 1
```

---

## 必要な環境変数（ローカル）

| 変数 | 値 | 備考 |
|------|---|------|
| STRIPE_SECRET_KEY | sk_test_xxx | Stripe Dashboard |
| STRIPE_PUBLISHABLE_KEY | pk_test_xxx | Stripe Dashboard |
| STRIPE_WEBHOOK_SECRET | whsec_xxx | stripe listen 実行時に表示 |
| SITE_URL | http://localhost:5173 | デフォルト値あり |
| CSRF_TRUSTED_ORIGINS | http://localhost:5173,http://localhost:8000 | デフォルト値あり |

---

## テスト観点

### A. 予約作成
- card 予約で status=pending, payment_status=unpaid になるか

### B. Checkout 開始
- POST /api/reservations/{token}/checkout/ が通るか
- checkout_url が返るか
- Stripe Checkout 画面に遷移するか

### C. Success / Cancel
- 決済完了 → ?checkout=success で確認ページに戻るか
- Cancel → ?checkout=cancel で戻るか

### D. Webhook
- checkout.session.completed で status=confirmed, payment_status=paid になるか
- 二重送信でべき等に動くか

### E. Pending 失効
- expire_pending で古い pending が cancelled になるか
- 在庫が戻るか

---

## 本番移行チェックリスト

### Heroku Config Vars

| 変数 | 内容 |
|------|------|
| STRIPE_SECRET_KEY | sk_live_xxx |
| STRIPE_PUBLISHABLE_KEY | pk_live_xxx |
| STRIPE_WEBHOOK_SECRET | 本番 webhook の signing secret |
| SITE_URL | https://mogi-app.netlify.app |
| CSRF_TRUSTED_ORIGINS | https://mogi-app.netlify.app |
| CORS_ALLOWED_ORIGINS | https://mogi-app.netlify.app |
| DEBUG | False |
| SECRET_KEY | 本番用ランダム値 |

### Stripe Dashboard

| 設定 | 内容 |
|------|------|
| Webhook URL | https://mogi-app-11259607193e.herokuapp.com/api/stripe/webhook/ |
| イベント | checkout.session.completed |
| Signing secret | STRIPE_WEBHOOK_SECRET に設定 |

### Heroku Scheduler

| ジョブ | スケジュール |
|--------|------------|
| python manage.py expire_pending | Every 10 minutes |

---

## 不足実装の有無

**ローカル確認に必要な実装は全て揃っている。コード変更なしで確認に進める。**

### 懸念点（本番前に検討）

1. **webhook 完了時の自動メール送信がない**（中）— 現状は admin 手動送信のみ
2. **checkout.session.expired イベント未処理**（低）— expire_pending でカバーされるがタイミングずれの可能性
3. **Stripe API version 未固定**（低）— 本番では固定推奨
4. **refund 自動処理なし**（情報）— 手動対応で十分なら問題なし

---

## 次ステップ

1. `.env` に Stripe test key を記入してローカル動作確認を実施
2. 確認結果に基づき、必要なら最小修正を実施
3. 本番移行設定を適用
