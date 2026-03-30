# 作業報告書: フロントエンド F4 — ReserveView Step 2-3 + GuestInfoForm + ReservationSummary

- 日時: 2026-03-30 14:54
- 作業者: Claude (Opus 4.6)
- プロジェクト: Mogi（演劇向け最小票券管理システム）

---

## 1. 目的

予約画面の Step 2（お客様情報入力）と Step 3（予約内容確認）を実装し、
Step 1 → 2 → 3 → 仮完了 の全フローを mock で動かせる状態にする。

---

## 2. 変更ファイル一覧

| ファイル | 操作 | 概要 |
|---------|------|------|
| `frontend/src/components/reservation/GuestInfoForm.vue` | 新規 | 氏名・メール・電話の入力フォーム |
| `frontend/src/components/reservation/ReservationSummary.vue` | 新規 | 予約内容確認カード |
| `frontend/src/views/ReserveView.vue` | 書き換え | Step 2, 3, 4（仮完了）を追加 |
| `frontend/src/composables/useReservationForm.js` | 編集 | canProceedStep2 追加、nextStep() に Step 2→3 遷移追加 |

---

## 3. 各ファイルの詳細

### 3.1 components/reservation/GuestInfoForm.vue

#### props / emit

| prop | 型 | 説明 |
|------|-----|------|
| guestName | String | 氏名 |
| guestEmail | String | メール |
| guestPhone | String | 電話番号 |
| emailRequired | Boolean | メール必須かどうか（card=true, cash=false） |

| emit | 説明 |
|------|------|
| update:guestName | 氏名入力時 |
| update:guestEmail | メール入力時 |
| update:guestPhone | 電話入力時 |

#### 表示構成

- **お名前**: 必須マーク付き
- **メールアドレス**: emailRequired が true なら必須マーク + 「予約確認メールをお送りします」、false なら「（任意）」
- **電話番号**: 常に任意

**設計判断:**
- card 予約はメール必須（Stripe 決済後の確認メール送信のため）
- cash 予約はメール任意（当日現金払いなので必須にする理由がない）
- props + emit パターン。v-model は使わず親の composable が state を持つ

### 3.2 components/reservation/ReservationSummary.vue

#### props

| prop | 型 | 説明 |
|------|-----|------|
| performanceLabel | String | 公演ラベル |
| tierName | String | 席種名 |
| quantity | Number | 枚数 |
| reservationType | String | 'card' or 'cash' |
| totalPrice | Number | 合計金額 |
| guestName | String | 氏名 |
| guestEmail | String | メール（空なら非表示） |
| guestPhone | String | 電話（空なら非表示） |

#### 表示構成

Bootstrap の card + list-group-flush で2セクション:

1. **予約内容**: 公演 / 席種 / 枚数 / お支払い / 合計金額
2. **お客様情報**: お名前 / メール（あれば） / 電話（あれば）

合計金額は `fs-5 fw-bold` で目立たせる。

### 3.3 views/ReserveView.vue（差分）

#### 追加した要素

1. **ステップインジケーター**: 3つの横並びバッジ。現在ステップは `bg-dark text-white`、他は `bg-light text-muted`
2. **Step 2**: GuestInfoForm + 「戻る」「次へ — 確認」ボタン
3. **Step 3**: ReservationSummary + 「戻る」「決済へ進む / 予約を確定する」ボタン
4. **Step 4（仮完了）**: 「予約を受け付けました」メッセージ + 作品ページへ戻るリンク

#### ボタンテキストの出し分け

- Step 3 の確定ボタン: card → 「決済へ進む」、cash → 「予約を確定する」
- Step 4 のメッセージ: card → 「カード決済画面にリダイレクトします...」、cash → 「当日会場にてお支払いください。」

#### handleSubmit()

- 現時点では console.log でフォーム値を出力し、step を 4 に遷移するだけ
- API 接続後: POST /api/reservations/ → card なら POST /api/reservations/:id/checkout/ で Stripe リダイレクト

### 3.4 composables/useReservationForm.js（差分）

追加:

```javascript
const canProceedStep2 = computed(() => {
  if (!guestName.value.trim()) return false
  if (reservationType.value === 'card' && !guestEmail.value.trim()) return false
  return true
})
```

nextStep() に Step 2→3 遷移を追加:
```javascript
} else if (step.value === 2 && canProceedStep2.value) {
  step.value = 3
}
```

---

## 4. 実行コマンドと動作確認結果

| コマンド | 結果 |
|---------|------|
| `npx vite build` | ビルド成功（235ms） |

ビルド出力:
- `ReserveView-*.js`: 11.82 kB（Step 1-4 + 3コンポーネント + composable）
- 他の chunk は変化なし

---

## 5. 画面の動作フロー

`/paradise-effect/reserve/1` にアクセスすると:

**Step 1（席種選択）:**
1. ステップインジケーター「[席種選択] お客様情報 確認」
2. 支払方法 → 席種 → 枚数 → 小計
3. 「次へ — お客様情報入力」→ Step 2 へ

**Step 2（お客様情報）:**
1. ステップインジケーター「席種選択 [お客様情報] 確認」
2. 氏名（必須）、メール（card=必須/cash=任意）、電話（任意）
3. 「戻る」→ Step 1 へ（入力値は保持）
4. 「次へ — 確認」→ Step 3 へ（氏名空なら disabled）

**Step 3（確認）:**
1. ステップインジケーター「席種選択 お客様情報 [確認]」
2. 予約内容カード（公演/席種/枚数/支払い/合計/氏名/メール/電話）
3. 「戻る」→ Step 2 へ（入力値は保持）
4. 「決済へ進む」or「予約を確定する」→ Step 4 へ（仮完了）

**Step 4（仮完了）:**
1. 「予約を受け付けました」
2. card → 「カード決済画面にリダイレクトします...」
3. cash → 「当日会場にてお支払いください。」
4. 「作品ページに戻る」リンク

**戻るボタンの動作:**
- Step 2→1: 席種・枚数・種別の選択は保持される
- Step 3→2: 入力した氏名・メール・電話は保持される

---

## 6. 未着手・残存事項

| 項目 | 備考 |
|------|------|
| API 送信（POST /api/reservations/） | バックエンド API 完成後 |
| Stripe Checkout リダイレクト | payments app 完成後 |
| バリデーション強化（メール形式チェック等） | MVP では最低限で十分 |
| エラーハンドリング（在庫不足の 400 等） | API 接続時に対応 |

---

## 7. 次ステップ

**F5:** ReservationConfirmView + mock

対象ファイル:
- `frontend/src/views/ReservationConfirmView.vue` — 予約確認ページ（token ベース）
- `frontend/src/mock/reservations.js` — mock 予約データ
- `frontend/src/components/reservation/ReservationStatusBadge.vue`（必要に応じて）

---

## 8. 現在のディレクトリ構成（差分のみ）

```
frontend/src/
├── composables/
│   └── useReservationForm.js    ← canProceedStep2 追加
├── components/
│   └── reservation/
│       ├── GuestInfoForm.vue    ← 新規
│       └── ReservationSummary.vue ← 新規
├── views/
│   ├── ReserveView.vue          ← Step 2, 3, 4 追加
│   └── ...
└── ...
```
