# 作業報告書: フロントエンド F3 — ReserveView Step 1 + SeatTierSelector + useReservationForm

- 日時: 2026-03-30 14:48
- 作業者: Claude (Opus 4.6)
- プロジェクト: Mogi（演劇向け最小票券管理システム）

---

## 1. 目的

予約画面の Step 1（席種選択・枚数選択・支払方法選択）を mock データで実装する。
state 管理は composable に寄せ、ReserveView と SeatTierSelector の責務を分離する。

---

## 2. 変更ファイル一覧

| ファイル | 操作 | 概要 |
|---------|------|------|
| `frontend/src/composables/useReservationForm.js` | 新規 | 予約フォームの state + validation + actions |
| `frontend/src/components/event/SeatTierSelector.vue` | 新規 | 席種・枚数・支払方法の選択UI |
| `frontend/src/views/ReserveView.vue` | 書き換え | Step 1 の実装（composable + SeatTierSelector を組み合わせ） |

---

## 3. 各ファイルの詳細

### 3.1 composables/useReservationForm.js

#### state

| 変数 | 型 | 初期値 | 説明 |
|------|-----|--------|------|
| step | ref(1) | 1 | 現在のステップ (1:席種, 2:情報入力, 3:確認, 4:完了) |
| performance | ref(null) | null | 対象公演データ |
| selectedTier | ref(null) | null | 選択した席種 |
| quantity | ref(1) | 1 | 枚数 |
| reservationType | ref('card') | 'card' | 予約種別 (card/cash) |
| guestName | ref('') | '' | 氏名 |
| guestEmail | ref('') | '' | メール |
| guestPhone | ref('') | '' | 電話番号 |

#### computed

| 名前 | 内容 |
|------|------|
| unitPrice | reservationType に応じて price_card or price_cash を返す |
| totalPrice | unitPrice × quantity |
| canProceedStep1 | selectedTier が選択済み、quantity が 1〜10 かつ remaining 以下 |

#### actions

| 名前 | 内容 |
|------|------|
| selectTier(tier) | 席種を選択。quantity が remaining を超えていたらリセット |
| nextStep() | step を +1（canProceed チェック付き） |
| prevStep() | step を -1（1 より下がらない） |
| reset() | 全 state を初期値に戻す |

**設計判断:**
- invite は composable に含めない（受付画面 or CSVインポートで作成。一般予約画面では選べない）
- guestName / guestEmail / guestPhone は Step 2 で使用。今回は定義のみで UI 未実装
- canProceedStep1 を computed にした理由: ボタンの disabled と validation を一箇所で管理

### 3.2 components/event/SeatTierSelector.vue

#### props / emit

| prop | 型 | 説明 |
|------|-----|------|
| seatTiers | Array | 席種リスト |
| selectedTier | Object | 選択中の席種 |
| quantity | Number | 枚数 |
| reservationType | String | 'card' or 'cash' |

| emit | 説明 |
|------|------|
| update:selectedTier | 席種選択時 |
| update:quantity | 枚数変更時 |
| update:reservationType | 支払方法変更時 |

#### 表示構成

1. **お支払い方法**: Bootstrap btn-group（ラジオボタン風）
   - 「カード決済」 / 「当日現金払い」の2択
   - invite は選択肢に含めない
2. **席種を選択**: list-group
   - 各行: 席種名 + 残席バッジ + 価格
   - 選択中の席種は `.active`
   - 完売（remaining === 0）は `.disabled`
   - 価格は reservationType に応じて price_card or price_cash を表示
3. **枚数**: select（席種選択後に表示）
   - 1〜min(remaining, 10) の範囲
   - max-width: 120px

**設計判断:**
- v-model ではなく props + emit パターン。親の composable が state を持つため
- 価格切り替え: reservationType を変えると即座に全席種の価格表示が切り替わる
- 枚数上限を 10 に制限（CSV インポーターと同じ制約）

### 3.3 views/ReserveView.vue

#### 表示構成

1. **パンくずリスト**: 作品名 → 予約（作品詳細へ戻れる）
2. **公演情報**: ラベル + 開場/開演時刻
3. **SeatTierSelector**: 席種・枚数・種別選択
4. **小計カード**: 席種名 × 枚数 = 合計金額（席種選択後に表示）
5. **「次へ」ボタン**: canProceedStep1 が false なら disabled

#### データ取得

- onMounted で mock/events.js から performanceId に一致する公演を取得
- API 接続後は `api/events.js` の fetch に差し替え

#### max-width: 640px

- 予約フォームはナローレイアウト（640px）にした
- 理由: スマートフォンでの操作が主。幅が広すぎると見づらい

---

## 4. 実行コマンドと動作確認結果

| コマンド | 結果 |
|---------|------|
| `npx vite build` | ビルド成功（297ms） |

ビルド出力:
- `events-*.js`: 3.29 kB（mock データ、EventDetailView と ReserveView で共有 chunk）
- `ReserveView-*.js`: 5.41 kB（composable + SeatTierSelector 含む）
- `EventDetailView-*.js`: 2.65 kB（mock を共有 chunk に分離したため軽量化）

---

## 5. 画面の動作

`/paradise-effect/reserve/1` にアクセスすると:

1. パンくず「パラダイスエフェクト〖第一回単独公演〗 > 予約」表示
2. 「5/21(金) 18:00 ソワレ」「開場 17:30 / 開演 18:00」表示
3. 支払方法: カード決済 / 当日現金払い のトグル
4. 席種一覧: 最前席(残4, 4,000円), 前方席(残8, 3,500円), 中央席(残15, 3,000円), 後方席(残12, 2,500円)
5. 「当日現金払い」に切り替えると全席種の価格が cash 価格に切り替わる
6. 席種をクリックすると active + 枚数セレクト表示
7. 小計カード表示（例: 「前方席 × 2枚 7,000円」）
8. 「次へ — お客様情報入力」ボタン（席種未選択時は disabled）

---

## 6. 未着手・残存事項

| 項目 | 備考 |
|------|------|
| ReserveView Step 2 | GuestInfoForm（氏名・メール・電話入力）。F4 で実装 |
| ReserveView Step 3 | ReservationSummary（確認画面）。F4 で実装 |
| ReserveView Step 4 | 完了表示 + Stripe リダイレクト。API 接続後 |
| api/events.js | mock → API 切り替え |
| 在庫の楽観ロック | API 側で対応。フロントは submit 時の 400 エラーをハンドリング |

---

## 7. 次ステップ

**F4:** ReserveView Step 2-3 — GuestInfoForm + ReservationSummary

対象ファイル:
- `frontend/src/components/reservation/GuestInfoForm.vue` — 氏名・メール・電話入力
- `frontend/src/components/reservation/ReservationSummary.vue` — 予約確認表示
- `frontend/src/views/ReserveView.vue` — Step 2, 3 の追加

---

## 8. 現在のディレクトリ構成（差分のみ）

```
frontend/src/
├── composables/
│   └── useReservationForm.js    ← 新規
├── components/
│   └── event/
│       ├── PerformanceCard.vue
│       └── SeatTierSelector.vue ← 新規
├── views/
│   ├── ReserveView.vue          ← 書き換え: Step 1 実装
│   └── ...
└── ...
```
