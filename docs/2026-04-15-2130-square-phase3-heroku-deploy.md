# Square 決済導入 Phase 3 — Heroku 反映レポート

日時: 2026-04-15 21:30
対象アプリ: `mogi-app`（Heroku）
成果物: Heroku 上で Square Sandbox 決済を受け入れる準備が整った

---

## 1. 実施内容サマリ

| Step | 内容 | 結果 |
|---|---|---|
| 1 | `.env.production` の git 履歴漏洩確認 | **履歴ゼロ、Stripe live key 漏洩なし** |
| 2 | Phase 1/2a/2b 成功状態をコミット | `28da47f` |
| 3 | `config/settings.py` から ngrok default を除去 | `0ac512a` |
| 4 | `.env` / `.env.production` 整理 | ローカルは Sandbox 明示、本番は受け皿作成 |
| 5a | Heroku config vars 設定（Sandbox 値） | v32 リリース、4 項目反映 |
| 5b | Heroku へコード push | v33 リリース、migration 適用成功 |

---

## 2. コミット履歴

```
0ac512a ngrok default を ALLOWED_HOSTS から除去
28da47f Square決済導入 Phase 1/2a/2b
b31cb94 （デプロイ直前の main）
```

---

## 3. Heroku に反映した設定値

| Key | Value |
|---|---|
| `SQUARE_ENVIRONMENT` | `sandbox` |
| `SQUARE_ACCESS_TOKEN` | Sandbox token（`EAAA...cieeE`） |
| `SQUARE_LOCATION_ID` | `LTCSX6K1SA35X` |
| `SQUARE_WEBHOOK_NOTIFICATION_URL` | `https://mogi-app-11259607193e.herokuapp.com/api/square/webhook/` |
| `SQUARE_WEBHOOK_SIGNATURE_KEY` | **未設定**（後述） |

既存項目（`ALLOWED_HOSTS`, `SITE_URL`, `STRIPE_*` 等）は不変。

---

## 4. デプロイ結果

- Release v33 で `payments.0001_initial` マイグレーション適用成功（`ProcessedWebhookEvent` テーブル作成）
- `squareup 44.0.1` 含む依存は全てインストール成功
- Stripe 経路は温存（旧 URL `/api/stripe/webhook/` も生存）

---

## 5. 現時点で残っている作業

### 必須（これをやらないと Square 決済は動かない）

1. **Square Developer Console で Heroku 用 Sandbox subscription を作成**
   - Notification URL: `https://mogi-app-11259607193e.herokuapp.com/api/square/webhook/`
   - 購読イベント: `payment.updated`
   - 作成後に表示される **Signature Key を控える**
2. **Heroku config vars に Signature Key を流し込む**
   ```
   heroku config:set SQUARE_WEBHOOK_SIGNATURE_KEY=<取得した key> -a mogi-app
   ```
3. Heroku 上で Sandbox 決済を E2E テスト（予約作成 → Payment Link → 決済成功 → 予約 confirmed/paid 反映 → 完了メール送信）

### 本番審査通過後

4. Square Developer Console で **Production 用 subscription** を作成（同 URL、`payment.updated` 購読）
5. Heroku config vars を本番値に差し替え:
   ```
   heroku config:set \
     SQUARE_ENVIRONMENT=production \
     SQUARE_ACCESS_TOKEN=<production token> \
     SQUARE_LOCATION_ID=<production location> \
     SQUARE_WEBHOOK_SIGNATURE_KEY=<production subscription key> \
     -a mogi-app
   ```
6. 実カードで少額決済テスト

### Phase 4（Stripe 残骸掃除）— 本番稼働確認後

- [payments/views.py](../payments/views.py) の Stripe webhook と `_handle_stripe_checkout_completed` 削除
- [payments/urls.py](../payments/urls.py) の `stripe/webhook/` ルート削除
- [reservations/models.py](../reservations/models.py) の `stripe_checkout_session_id` フィールド削除 + マイグレーション
- [config/settings.py](../config/settings.py) の `STRIPE_*` 削除
- [requirements.txt](../requirements.txt) から `stripe` 削除
- Heroku config vars から `STRIPE_*` 削除
- [.env.production](../.env.production) から Stripe 3 行削除

---

## 6. 現在の webhook エンドポイント状態

```bash
curl -X POST https://mogi-app-11259607193e.herokuapp.com/api/square/webhook/ -d 'test'
# => HTTP 500
```

これは **設計通り**。`SQUARE_WEBHOOK_SIGNATURE_KEY` が未設定のため `verify_signature` が `ValueError` を投げ、view が 500 を返す。
Square Console 側でまだ subscription を張っていないため実害なし。Signature Key 設定後に 400（署名不正）または 200（正当）を返すようになる。

---

## 7. 判断メモ

- **Webhook URL は Heroku 直 URL (`mogi-app-11259607193e.herokuapp.com`) に固定**
  理由: カスタムドメイン `mogi-app.com` は Netlify 経由の可能性があり、API リクエストのルーティング保証が取れなかった。直 URL なら Django まで確実に到達する。
- **Signature Key をまだ設定しない判断**
  ngrok 用 subscription の key を流用するとホスト不一致で全リクエストが 400 になる。Heroku 用 subscription を新規作成し、その key を別途設定するのが正解。
- **Stripe 残骸は温存**
  本番切替で問題があった場合、即時 Stripe に戻せる退避経路を残すため。Phase 4 で掃除。

---

## 8. リスク / 注意事項

- **[.env.production](../.env.production) に Stripe live secret key が平文で残っている**
  git 履歴にはないが、ローカルファイルに存在。Phase 4 で削除するまでファイル取り扱い注意。
- **Netlify frontend から Heroku backend への API 呼び出し経路は未検証**
  Payment Link 発行 API (`POST /api/...`) が Netlify 経由でも通るかは別途確認が必要。
- **SMTP 設定は本番値が入っている**
  `EMAIL_HOST=sv1416.xserver.jp` / `info@studio-shindra.com` / TLS 587。完了メール送信は本番 SMTP を経由するので、Sandbox テスト時もメールが実アドレスに飛ぶ点に注意。

---

## 9. 結論

- Heroku 上で Square Sandbox 決済を受け入れる **コードとインフラ設定は完了**
- 残るは Square Console で Heroku 用 subscription を作り、Signature Key を Heroku に流し込む 1 手順
- 本番値差し替えは config vars 4 項目の更新のみで完了する状態
