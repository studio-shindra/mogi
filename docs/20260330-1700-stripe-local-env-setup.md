# Stripe ローカル環境セットアップ

**日時**: 2026-03-30 17:00
**対象**: .env / .gitignore 作成、設定確認

---

## 確認結果

| チェック項目 | 状態 | 備考 |
|---|---|---|
| `settings.py` で env 読み取り | OK | `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`, `SITE_URL`, `CSRF_TRUSTED_ORIGINS` すべて `python-decouple` で読み込み済み |
| `payments/views.py` webhook 署名検証 | OK | `stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)` で正しく検証 |
| `payments/services.py` API key 設定 | OK | `stripe.api_key = settings.STRIPE_SECRET_KEY` |
| `.env` ファイル | **新規作成** | テストキー貼り付け用テンプレート |
| `.gitignore` | **新規作成** | `.env` を含む標準除外パターン |

## 変更内容

### 1. `.env` 作成

プレースホルダー付きのテンプレートを配置。ユーザーが Stripe Dashboard と `stripe listen` の出力から値を貼り付けるだけで動作する。

### 2. `.gitignore` 作成

`.env` が誤ってコミットされないよう `.gitignore` を新規作成。

## コード変更: なし

`settings.py`, `payments/views.py`, `payments/services.py` はすべて正しく実装済み。変更不要。

## ローカル確認手順

```bash
# 1. .env にキーを貼る（3箇所）
#    - STRIPE_SECRET_KEY=sk_test_...
#    - STRIPE_PUBLISHABLE_KEY=pk_test_...
#    - STRIPE_WEBHOOK_SECRET=whsec_...

# 2. Django 起動
python manage.py runserver

# 3. 別ターミナルで Stripe CLI webhook 転送
stripe listen --forward-to localhost:8000/api/stripe/webhook/

# 4. テストイベント送信（任意）
stripe trigger checkout.session.completed
```

## 補足

- Stripe CLI 未インストールの場合: `brew install stripe/stripe-cli/stripe`
- `whsec_...` は `stripe listen` 起動時の最初の出力行に表示される
- テストモードのキーは `sk_test_` / `pk_test_` で始まる
