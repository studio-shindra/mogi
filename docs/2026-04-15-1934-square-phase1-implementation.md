# Square 決済導入 Phase 1 実装報告

- 日時: 2026-04-15 19:34
- 担当: Claude (Opus 4.6)
- スコープ: Stripe → Square 切替 Phase 1(Payment Link 発行と遷移確認のみ)

---

## 背景

Stripe 審査が通らなかったため、Square へ決済基盤を切替える。
事故防止のため以下の方針で進行:

- Phase 1 は「Square Payment Link の `checkout_url` が発行され、Sandbox 決済画面に遷移できる」までに限定
- DB 変更ゼロ、Stripe コードは残置、フロント変更なし
- 変更ファイルは 3 ファイル以内
- Webhook・予約確定・メール送信・Stripe 削除・DB リネームは Phase 2 以降に分離
- Square API 仕様は記憶ベースではなく公式ドキュメント一次ソース確認

---

## 一次確認した Square 仕様(出典付き)

- **PyPI パッケージ**: `squareup`(現行 v44 系)
  - 出典: <https://developer.squareup.com/docs/sdks/python>
- **import / クライアント初期化**:
  - `from square import Square`
  - `from square.environment import SquareEnvironment`
  - `Square(token=..., environment=SquareEnvironment.SANDBOX)`
  - 出典: <https://developer.squareup.com/docs/sdks/python/quick-start>
- **Payment Link 作成メソッド**: `client.checkout.payment_links.create(...)`
  - 出典: <https://github.com/square/square-python-sdk/blob/master/reference.md>(L20719 付近)
- **リクエスト構造**:
  - `idempotency_key` (str)
  - `quick_pay = { name, price_money: { amount, currency }, location_id }`
  - `checkout_options = { redirect_url, ... }`
  - 出典: <https://developer.squareup.com/reference/square/checkout-api/create-payment-link>
- **CheckoutOptions.redirect_url**: 決済完了後の遷移先 URL(最大 2048 文字)。Stripe のような success/cancel の二系統はなく単一 URL。
  - 出典: <https://developer.squareup.com/reference/square/objects/CheckoutOptions>
- **JPY**: `price_money.amount` は最小通貨単位の整数(円)、`currency: "JPY"`
- **レスポンス**: `payment_link.url` / `payment_link.id` / `payment_link.order_id`

---

## 変更ファイル(3 ファイル)

### 1. `requirements.txt`

```diff
 stripe>=7.0,<8.0
+squareup>=44.0,<45.0
```

`stripe` は残置(Phase 3 で削除予定)。

### 2. `config/settings.py`

Stripe ブロックの直後に Square ブロックを追加。

```diff
 # --- Stripe ----------------------------------------------------------
 STRIPE_SECRET_KEY = config("STRIPE_SECRET_KEY", default="")
 STRIPE_PUBLISHABLE_KEY = config("STRIPE_PUBLISHABLE_KEY", default="")
 STRIPE_WEBHOOK_SECRET = config("STRIPE_WEBHOOK_SECRET", default="")
 SITE_URL = config("SITE_URL", default="https://mogi-app.com")
+
+# --- Square ----------------------------------------------------------
+SQUARE_ACCESS_TOKEN = config("SQUARE_ACCESS_TOKEN", default="")
+SQUARE_ENVIRONMENT = config("SQUARE_ENVIRONMENT", default="sandbox")
+SQUARE_LOCATION_ID = config("SQUARE_LOCATION_ID", default="")
```

### 3. `payments/services.py`

`create_checkout_session(reservation)` を Square Payment Link 発行版に全面置換。
**関数名・シグネチャ・戻り値(`checkout_url` 文字列)は維持** → `reservations/views.py` および フロントは無変更で動作する。

Phase 1 では `reservation` への ID 保存は行わない(DB 変更ゼロを担保)。Webhook がまだ無いため、現時点で payment_link_id を保持する必要がない。

```python
import uuid

from django.conf import settings
from square import Square
from square.environment import SquareEnvironment


def _client():
    env = (
        SquareEnvironment.PRODUCTION
        if settings.SQUARE_ENVIRONMENT == "production"
        else SquareEnvironment.SANDBOX
    )
    return Square(token=settings.SQUARE_ACCESS_TOKEN, environment=env)


def create_checkout_session(reservation):
    """Square Payment Link を作成し、URL を返す。"""
    unit_price = reservation.seat_tier.price_card
    total_amount = unit_price * reservation.quantity

    name = (
        f"{reservation.performance.event.title} "
        f"/ {reservation.performance.label} "
        f"/ {reservation.seat_tier.name} x{reservation.quantity}"
    )

    redirect_url = (
        f"{settings.SITE_URL}/reservation/{reservation.token}"
        "?checkout=success"
    )

    response = _client().checkout.payment_links.create(
        idempotency_key=str(uuid.uuid4()),
        quick_pay={
            "name": name,
            "price_money": {"amount": total_amount, "currency": "JPY"},
            "location_id": settings.SQUARE_LOCATION_ID,
        },
        checkout_options={"redirect_url": redirect_url},
    )

    return response.payment_link.url
```

---

## 触らなかった範囲(意図的)

- `reservations/models.py` — `stripe_checkout_session_id` カラムは温存
- `reservations/views.py` — `reservation_checkout` は無変更(契約維持)
- `payments/views.py` / `payments/urls.py` — Stripe Webhook は Phase 2 まで残置
- `frontend/` 全般 — `checkout_url` を返す契約が変わらないため無変更
- `.env.production` — 本番値投入は Phase 1 検証完了後

---

## 検証

### 自動チェック

- `pip show squareup` → `Version: 44.0.1.20260122` 確認
- `python -c "from square import Square; from square.environment import SquareEnvironment"` → import OK
- Django shell から `settings.SQUARE_ENVIRONMENT == 'sandbox'` 確認

### 残課題(ユーザー作業待ち)

- ローカル `.env` に `SQUARE_ACCESS_TOKEN` と `SQUARE_LOCATION_ID` の **行が無い**(grep 0 件)状態
- そのため runserver → 決済ボタン押下時に 401(Unauthorized)または 400(LocationId 空)で落ちる見込み
- Sandbox 用の Access token / Location ID を Square Developer Dashboard から取得し、ローカル `.env` に追記する必要あり

```
SQUARE_ACCESS_TOKEN=EAAA...
SQUARE_LOCATION_ID=L...
SQUARE_ENVIRONMENT=sandbox
```

取得元: <https://developer.squareup.com/apps> → アプリ → タブを Sandbox に切替 → Credentials / Locations

---

## 次のステップ

### Phase 1 完了判定(ユーザー手動確認)

1. `.env` に Sandbox 値を追記
2. `python manage.py runserver`
3. 既存フローで card 予約を作成
4. 予約確認画面の決済ボタン押下
5. Square Sandbox 決済画面へ遷移すれば Phase 1 完了

詰まったら以下 3 点を共有:
- どの API で落ちたか
- バックエンドのスタックトレース
- Square から返ったレスポンス本文

### Phase 2(Webhook 連携)着手前にやること

実装に入る前に Square 公式ドキュメントを WebFetch で再確認し、以下を文字列レベルで確定:

- 購読すべき Webhook イベント名(`payment.updated` / `COMPLETED` 系は **未検証**、思い込みで実装しない)
- 署名検証ヘッダ名と HMAC ペイロード構造
- 予約トークン運搬手段(Payment Link → Order の `reference_id` ルートを採用するのが最有力だが、Quick Pay モードでの可否を要確認)

### Phase 3(クリーンアップ)

- `stripe` パッケージ / `STRIPE_*` 環境変数 / `payments/views.py` の Stripe webhook 削除
- `reservations/models.py` の `stripe_checkout_session_id` を `square_payment_link_id` などへリネーム(マイグレーション 1 本)
- フロント文言の調整
