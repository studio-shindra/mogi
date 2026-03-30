# 作業報告書: フロントエンド F5 — ReservationConfirmView + ReservationStatusBadge + mock

- 日時: 2026-03-30 15:00
- 作業者: Claude (Opus 4.6)
- プロジェクト: Mogi（演劇向け最小票券管理システム）

---

## 1. 目的

token ベースの予約確認ページを mock データで実装する。
予約内容・支払い状態・チェックイン状態を表示し、条件に応じてセルフチェックイン導線を出す。

---

## 2. 変更ファイル一覧

| ファイル | 操作 | 概要 |
|---------|------|------|
| `frontend/src/mock/reservations.js` | 新規 | 3パターンの mock 予約データ + token 検索関数 |
| `frontend/src/components/reservation/ReservationStatusBadge.vue` | 新規 | status / payment_status / checked_in のバッジ表示 |
| `frontend/src/views/ReservationConfirmView.vue` | 書き換え | 予約確認ページ全体 |

---

## 3. 各ファイルの詳細

### 3.1 mock/reservations.js

3パターンの mock データ。API 契約 7.6 に準拠。

| 変数名 | token | 種別 | status | payment | checked_in | can_self_checkin |
|--------|-------|------|--------|---------|-----------|-----------------|
| mockReservationCard | abc123def456 | card | confirmed | paid | false | **true** |
| mockReservationCash | cash999xyz | cash | confirmed | unpaid | false | false |
| mockReservationCheckedIn | checked111 | card | confirmed | paid | true | false |

`findMockReservation(token)`: token で引き当て。一致なしなら card データをフォールバック。

各 mock に含まれるフィールド:
- `id`, `token`, `guest_name`, `guest_email`, `guest_phone`
- `performance`: `{ id, label, starts_at, event_title, venue_name }`
- `seat_tier`: `{ id, name, code }`
- `quantity`, `reservation_type`, `status`, `payment_status`
- `checked_in`, `can_self_checkin`, `checkin_opens_at`

### 3.2 components/reservation/ReservationStatusBadge.vue

#### props

| prop | 型 | 説明 |
|------|-----|------|
| status | String | pending / confirmed / cancelled |
| paymentStatus | String | unpaid / paid / refunded |
| checkedIn | Boolean | 入場済みかどうか |

#### 表示

computed `badges` で条件に応じたバッジ配列を生成:

| 条件 | ラベル | 色 |
|------|--------|-----|
| status=pending | 仮予約 | warning (黄) |
| status=confirmed | 確定 | success (緑) |
| status=cancelled | キャンセル | secondary (灰) |
| payment=unpaid | 未払い | danger (赤) |
| payment=paid | 支払済 | success (緑) |
| payment=refunded | 返金済 | secondary (灰) |
| checkedIn=true | 入場済 | info (水色) |

複数バッジが横並びで表示される（例: 「確定」「支払済」「入場済」）。

**再利用性**: この Badge は ReservationConfirmView だけでなく、StaffDashboardView でも使い回す想定。

### 3.3 views/ReservationConfirmView.vue

#### データ取得

- onMounted で `findMockReservation(token)` を呼んで reservation を取得
- API 接続後は `GET /api/reservations/:token/` に差し替え

#### 表示構成

1. **ステータスバッジ**: ReservationStatusBadge で status / payment / checkedIn を表示
2. **状態別アラート**:
   - `checked_in === true` → info「チェックイン済みです。ご来場ありがとうございます。」
   - `cash && unpaid` → warning「当日受付でお支払いください。受付にてお名前をお伝えください。」
3. **予約内容カード**: 作品名 / 公演 / 会場 / 席種+枚数 / 支払方法
4. **お客様情報カード**: 名前 / メール（あれば） / 電話（あれば）
5. **セルフチェックイン導線**: `can_self_checkin === true` の時のみ表示
   - `btn btn-dark btn-lg` で `/reservation/:token/checkin` へ遷移
6. **チェックイン開始前案内**: card/invite でまだチェックイン不可 → 開始日時を表示

#### 条件分岐まとめ

| パターン | アラート | チェックインボタン | 開始前案内 |
|---------|---------|------------------|-----------|
| card, paid, can_self_checkin=true | なし | 表示 | なし |
| card, paid, can_self_checkin=false | なし | なし | 表示（開始時刻） |
| card, paid, checked_in=true | 「チェックイン済み」 | なし | なし |
| cash, unpaid | 「受付でお支払い」 | なし | なし |
| invite, paid, can_self_checkin=true | なし | 表示 | なし |

---

## 4. 実行コマンドと動作確認結果

| コマンド | 結果 |
|---------|------|
| `npx vite build` | ビルド成功（383ms） |

ビルド出力:
- `ReservationConfirmView-*.js`: 6.06 kB（mock + Badge 含む）
- 他は変化なし

---

## 5. 画面の動作

**`/reservation/abc123def456`**（card, paid, チェックイン可能）:
- バッジ: 「確定」「支払済」
- 予約内容カード表示
- 「セルフチェックインへ」ボタン表示

**`/reservation/cash999xyz`**（cash, unpaid）:
- バッジ: 「確定」「未払い」
- 黄色アラート「当日受付でお支払いください」
- チェックインボタンなし

**`/reservation/checked111`**（card, paid, チェックイン済み）:
- バッジ: 「確定」「支払済」「入場済」
- 水色アラート「チェックイン済みです」
- チェックインボタンなし

**`/reservation/unknown-token`**（一致なし）:
- card データにフォールバック（mock の仕様）

---

## 6. 未着手・残存事項

| 項目 | 備考 |
|------|------|
| API 接続 (GET /api/reservations/:token/) | バックエンド完成後 |
| 404 表示（token 不正時） | API 接続後に 404 ハンドリング追加 |
| QR コード表示 | 将来的に予約確認ページ URL を QR で表示する想定 |

---

## 7. 次ステップ

**F6:** CheckinView

対象ファイル:
- `frontend/src/views/CheckinView.vue` — セルフチェックイン画面

mock/reservations.js と ReservationStatusBadge は既に作成済みなので、CheckinView 1ファイルの変更で済む。

---

## 8. 現在のディレクトリ構成（差分のみ）

```
frontend/src/
├── mock/
│   ├── events.js
│   └── reservations.js          ← 新規: 3パターンの mock
├── components/
│   └── reservation/
│       ├── GuestInfoForm.vue
│       ├── ReservationSummary.vue
│       └── ReservationStatusBadge.vue ← 新規: ステータスバッジ
├── views/
│   ├── ReservationConfirmView.vue ← 書き換え: 予約確認ページ
│   └── ...
└── ...
```
