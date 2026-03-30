# 作業報告書: フロントエンド F2 — EventDetailView + PerformanceCard + mock

- 日時: 2026-03-30 14:43
- 作業者: Claude (Opus 4.6)
- プロジェクト: Mogi（演劇向け最小票券管理システム）

---

## 1. 目的

作品詳細画面を mock データで先行実装する。
作品情報・会場・出演者・公演回一覧を表示し、公演カードクリックで予約画面へ遷移できる状態にする。

---

## 2. 変更ファイル一覧

| ファイル | 操作 | 概要 |
|---------|------|------|
| `frontend/src/mock/events.js` | 新規 | パラダイスエフェクトの mock データ（Event 1件 + Performance 5件 + SeatTier 各4種） |
| `frontend/src/components/event/PerformanceCard.vue` | 新規 | 公演回カード（日時・残席・最安価格表示、クリックで予約画面遷移） |
| `frontend/src/views/EventDetailView.vue` | 書き換え | 作品情報 + 公演回一覧の表示（mock データ使用） |

---

## 3. 各ファイルの詳細

### 3.1 mock/events.js

#### mockEventDetail

パラダイスエフェクトの完全なレスポンスデータ。API 契約（7.2 + 7.3）に準拠。

| フィールド | 値 |
|-----------|-----|
| title | パラダイスエフェクト〖第一回単独公演〗 |
| slug | paradise-effect |
| description | コヤナギシンが語り紡ぐ〜オムニバス短編集。 |
| venue_name | 新生館スタジオ |
| venue_address | 東京都板橋区中板橋19-6 ダイアパレス中板橋B1 |
| cast | コヤナギシン |

Performance 5件（5/21〜5/24）、各公演に SeatTier 4種。
各 SeatTier に `remaining` フィールド含む（API 契約 7.3 の拡張仕様に準拠）。

mock 価格設定:
| 席種 | price_card | price_cash |
|------|-----------|-----------|
| 最前席 | 4,000 | 4,500 |
| 前方席 | 3,500 | 4,000 |
| 中央席 | 3,000 | 3,500 |
| 後方席 | 2,500 | 3,000 |

mock 残席は公演ごとにばらつきを持たせている（5/22 ソワレと 5/24 ソワレは少なめ）。

#### mockEvents

一覧用。`[{ id, title, slug }]` の配列。EventListView（F9）で使用予定。

### 3.2 components/event/PerformanceCard.vue

#### props

| prop | 型 | 説明 |
|------|-----|------|
| performance | Object | Performance データ（seat_tiers ネスト含む） |
| slug | String | Event の slug（遷移先 URL に使用） |

#### computed

| 名前 | 計算内容 |
|------|---------|
| totalRemaining | 全席種の remaining 合計 |
| totalCapacity | 全席種の capacity 合計 |
| minPrice | 全席種の price_card の最安値 |

#### 表示内容

- 左側: 公演ラベル（"5/21(金) 18:00 ソワレ"）、開場/開演時刻
- 右側: 残席バッジ（残あり=緑、完売=グレー）、最安価格

#### 操作

- カード全体が `<RouterLink>` で `/:slug/reserve/:performanceId` に遷移

### 3.3 views/EventDetailView.vue

#### state

| 変数 | 型 | 説明 |
|------|-----|------|
| event | ref(null) | 作品データ |
| loading | ref(true) | ローディング状態 |

#### 表示構成

1. **ローディング**: Bootstrap spinner
2. **作品情報**: タイトル（h1）、説明（lead テキスト）
3. **会場・出演者**: Bootstrap カード2列（md 以上で横並び）
   - 左: 会場名 + 住所
   - 右: 出演者
4. **公演スケジュール**: h2 + PerformanceCard × 5件

#### データ取得

- `onMounted` で mock データを代入
- API 接続後は `api/events.js` の fetch に差し替える（TODO コメント付き）

---

## 4. 実行コマンドと動作確認結果

| コマンド | 結果 |
|---------|------|
| `npx vite build` | ビルド成功（286ms） |

ビルド出力で EventDetailView が 5.90 kB（mock データ + PerformanceCard 含む）。
他の view スタブは 0.26〜0.46 kB で変化なし。

---

## 5. 画面の動作

`/paradise-effect` にアクセスすると:
1. 「パラダイスエフェクト〖第一回単独公演〗」のタイトル表示
2. 説明文表示
3. 会場カード（新生館スタジオ / 東京都板橋区...）と出演カード（コヤナギシン）が横並び
4. 「公演スケジュール」セクションに5件のカード
5. 各カードに公演ラベル、開場/開演時刻、残席バッジ、最安価格
6. カードクリックで `/paradise-effect/reserve/1` 等に遷移（ReserveView スタブが表示）

---

## 6. 未着手・残存事項

| 項目 | 備考 |
|------|------|
| api/events.js | API クライアント。F10 で実装 |
| api/client.js | axios インスタンス。F10 で実装 |
| 残席のリアルタイム更新 | MVP では画面遷移時に再 fetch で十分 |
| 公演が過去かどうかの判定 | 将来的に「この公演は終了しました」表示が必要 |

---

## 7. 次ステップ

**F3:** ReserveView Step 1 — SeatTierSelector

対象ファイル:
- `frontend/src/views/ReserveView.vue` — ステップ式予約フォーム（Step 1: 席種選択）
- `frontend/src/components/event/SeatTierSelector.vue` — 席種・枚数選択コンポーネント
- `frontend/src/composables/useReservationForm.js` — 予約フォームの state 管理

---

## 8. 現在のディレクトリ構成（差分のみ）

```
frontend/src/
├── mock/
│   └── events.js                ← 新規: mock データ
├── components/
│   ├── layout/
│   │   └── AppHeader.vue
│   └── event/
│       └── PerformanceCard.vue  ← 新規: 公演回カード
├── views/
│   ├── EventDetailView.vue      ← 書き換え: 作品詳細画面
│   └── ...（他はスタブのまま）
└── ...
```
