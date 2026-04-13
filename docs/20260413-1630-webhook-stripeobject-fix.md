# Webhook StripeObject アクセス修正

- 日時: 2026-04-13 16:30
- 目的: checkout.session.completed webhook の 500 エラーを修正
- 種別: バグ修正

---

## 目的

`checkout.session.completed` イベント処理時に `session.get("metadata", {})` が `AttributeError` で落ちる問題を修正する。

## 原因

Stripe の `event["data"]["object"]` は Python の `dict` ではなく `StripeObject`。
`StripeObject` は `[]` アクセスや `in` 演算子は使えるが、`.get()` メソッドは持たない場合がある。
`session.get("metadata", {})` が `AttributeError: get` で 500 になっていた。

## 変更ファイル一覧

| ファイル | 変更内容 |
|---------|---------|
| `payments/views.py` | `_handle_checkout_completed()` の metadata 取得方法を修正 |

## 変更内容

### payments/views.py

**Before:**
```python
reservation_token = session.get("metadata", {}).get("reservation_token")
```

**After:**
```python
metadata = session["metadata"] if "metadata" in session and session["metadata"] else {}
reservation_token = metadata.get("reservation_token")
```

`session["metadata"]` は `dict` として返されるため、そこからの `.get()` は安全。

## 動作確認

- [ ] Django 再起動
- [ ] card 決済 → Stripe Checkout → success に戻る
- [ ] webhook で status=confirmed, payment_status=paid になる

## 未着手事項

- webhook 完了時の自動メール送信
- checkout.session.expired イベント処理
- Stripe API version 固定

## 次ステップ

1. Django 再起動して再度 card 決済テスト
2. GET /api/reservations/{token}/ で confirmed / paid を確認
