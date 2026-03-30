# 作業報告書: フロントエンド F7+F8 — 受付画面一式

- 日時: 2026-03-30 15:09
- 作業者: Claude (Opus 4.6)
- プロジェクト: Mogi（演劇向け最小票券管理システム）

---

## 1. 目的

受付画面を mock データで完成形に近い状態まで実装する。
予約検索・一覧表示・現金受領・入場処理・当日券登録・招待表示を1画面で操作できる状態にする。

---

## 2. 変更ファイル一覧

| ファイル | 操作 | 概要 |
|---------|------|------|
| `frontend/src/mock/reservations.js` | 大幅拡充 | 6件の mock 予約 + 検索関数 + 公演リスト |
| `frontend/src/composables/useStaffActions.js` | 新規 | 受付操作の state + actions（検索, 現金受領, 入場, 当日券） |
| `frontend/src/components/staff/StaffSearchBar.vue` | 新規 | 公演フィルタ + テキスト検索バー |
| `frontend/src/components/staff/StaffReservationRow.vue` | 新規 | 予約行（ステータスバッジ + 操作ボタン） |
| `frontend/src/components/staff/WalkInForm.vue` | 新規 | 当日券登録フォーム |
| `frontend/src/views/StaffDashboardView.vue` | 書き換え | 受付画面全体 |

---

## 3. 各ファイルの詳細

### 3.1 mock/reservations.js（拡充）

6件の mock 予約データ:

| id | guest_name | type | status | payment | checked_in | 用途 |
|----|-----------|------|--------|---------|-----------|------|
| 1 | 山田太郎 | card | confirmed | paid | false | card 決済済み |
| 2 | 佐藤花子 | cash | confirmed | unpaid | false | cash 未払い |
| 3 | 鈴木一郎 | card | confirmed | paid | true | チェックイン済み |
| 4 | 田中監督 | invite | confirmed | paid | false | 招待 |
| 5 | 高橋次郎 | card | pending | unpaid | false | Stripe 未決済 |
| 6 | 渡辺美咲 | cash | confirmed | paid | false | cash 支払済み |

追加した関数:
- `searchMockReservations(performanceId, query)`: 公演フィルタ + テキスト検索
- `mockPerformanceOptions`: 公演フィルタ用セレクトの選択肢（5公演）
- `mockAllReservations`: 全6件の配列（export）
- `findMockReservation(token)`: 確認ページ / チェックイン用（既存を改修、can_self_checkin を動的計算に変更）

### 3.2 composables/useStaffActions.js

#### state

| 変数 | 型 | 説明 |
|------|-----|------|
| searchQuery | ref('') | テキスト検索クエリ |
| selectedPerformanceId | ref(null) | 公演フィルタ（null=全公演） |
| reservations | ref([]) | 検索結果 |
| loading | ref(false) | ローディング |

#### computed

| 名前 | 内容 |
|------|------|
| summary | { count: 件数, total: 合計枚数, checkedIn: 入場済枚数, unpaid: 未払い枚数 } |

#### actions

| 名前 | 内容 | 対応 API |
|------|------|---------|
| search() | 公演+テキストで予約を検索 | GET /api/staff/reservations/ |
| markPaid(reservation) | 現金受領（payment_status→paid） | POST .../mark-paid/ |
| checkIn(reservation) | 入場処理（checked_in→true） | POST .../check-in/ |
| createWalkIn(data) | 当日券作成（一覧に追加） | POST .../walk-in/ |

### 3.3 components/staff/StaffSearchBar.vue

- 公演セレクト（全公演 + 5公演）
- テキスト入力（名前/メール/電話/トークン）
- 検索ボタン
- Bootstrap の row + col でレスポンシブ（md以上で横並び）

### 3.4 components/staff/StaffReservationRow.vue

テーブル行。各列:

| 列 | 内容 |
|----|------|
| 名前 | guest_name + guest_phone |
| 席種 | seat_tier.name × quantity |
| 種別 | カード / 現金 / 招待 |
| 状態 | ReservationStatusBadge（既存コンポーネント再利用） |
| メモ | memo |
| 操作 | 条件付きボタン |

操作ボタンの出し分け:

| 条件 | 表示 |
|------|------|
| confirmed + unpaid | 「現金受領」ボタン（黄） |
| confirmed + !checked_in | 「入場」ボタン（緑）。ただし unpaid なら disabled |
| checked_in | 「入場済」テキスト |

**設計判断:**
- 入場ボタンは unpaid の場合 disabled にした（先に現金受領してから入場処理する運用フロー）
- pending（Stripe 未決済）は現金受領も入場もボタン非表示

### 3.5 components/staff/WalkInForm.vue

コンパクトなフォーム:
- 公演セレクト + 席種セレクト（価格表示付き） + 枚数
- 名前（必須） + 電話 + メモ
- 「当日券を登録」ボタン
- 登録後フォームリセット

**設計判断:**
- 当日券は reservation_type=cash, status=confirmed, payment_status=paid で作成
- 席種セレクトに cash 価格を表示（当日券は現金価格）
- 公演を変えると席種セレクトの選択肢が連動して切り替わる

### 3.6 views/StaffDashboardView.vue

#### 表示構成

1. **ヘッダー**: 「受付」タイトル + 「当日券登録」トグルボタン
2. **当日券フォーム**: トグルで表示/非表示
3. **検索バー**: 公演フィルタ + テキスト検索
4. **集計バッジ**: 件数/枚数、入場数、未払い数
5. **予約一覧テーブル**: StaffReservationRow × N 件
6. **検索結果なし**: 「予約が見つかりません」

- `container-fluid` を使用（受付画面はタブレット幅いっぱい使う想定）
- onMounted で初回検索を実行

---

## 4. 実行コマンドと動作確認結果

| コマンド | 結果 |
|---------|------|
| `npx vite build` | ビルド成功（252ms） |

ビルド出力:
- `StaffDashboardView-*.js`: 8.93 kB
- `ReservationStatusBadge-*.js`: 4.30 kB（共有 chunk）

---

## 5. 画面の動作

`/staff` にアクセスすると:

1. 「受付」タイトル + 「当日券登録」ボタン
2. 検索バー（全公演、テキスト空）
3. 集計:「6件 / 8枚」「入場 1」「未払い 2」
4. テーブルに6件の予約:
   - 山田太郎: card/確定/支払済 → 「入場」ボタン
   - 佐藤花子: cash/確定/未払い → 「現金受領」+「入場」(disabled)
   - 鈴木一郎: card/確定/支払済/入場済 → 「入場済」テキスト
   - 田中監督: invite/確定/支払済 → 「入場」ボタン
   - 高橋次郎: card/仮予約/未払い → ボタンなし
   - 渡辺美咲: cash/確定/支払済 → 「入場」ボタン

**操作:**
- 「現金受領」クリック → 佐藤花子の payment_status が paid に変わり、「入場」ボタンが有効に
- 「入場」クリック → checked_in が true に、バッジに「入場済」追加
- 公演フィルタで「5/21(金) 18:00 ソワレ」選択 → 検索 → 4件に絞られる
- 「当日券登録」クリック → フォーム表示 → 名前入力 + 席種選択 → 登録 → 一覧の先頭に追加

---

## 6. 未着手・残存事項

| 項目 | 備考 |
|------|------|
| API 接続（受付系4エンドポイント） | バックエンド完成後 |
| /staff 認証ガード | router.beforeEach + 401 ハンドリング。API 接続時に対応 |
| 予約キャンセル操作 | MVP では admin から実施。受付画面には不要 |
| 予約詳細モーダル | 将来的にメモ編集・手動修正用。MVP では不要 |
| 印刷用レイアウト | 将来的に「予約名簿印刷」が欲しくなる可能性 |

---

## 7. 次ステップ

フロント MVP の画面は全て完成。残りは:

**F9:** EventListView + mock（優先度低）
**F10:** API 実接続（ここから刻む）
- api/client.js
- api/events.js（mock → real）
- api/reservations.js（mock → real）

並行して **バックエンド側**:
- reservations API（予約作成, 確認, チェックイン, 受付操作）
- payments app（Stripe Checkout）
- SeatTier の remaining 計算

---

## 8. 現在のフロント完成状況

| 画面 | 状態 | 備考 |
|------|------|------|
| EventListView | スタブ | F9 で実装予定（優先度低） |
| EventDetailView | **完成（mock）** | 作品情報 + 公演一覧 |
| ReserveView | **完成（mock）** | Step 1-4 全フロー |
| ReservationConfirmView | **完成（mock）** | 予約確認 + チェックイン導線 |
| CheckinView | **完成（mock）** | セルフチェックイン |
| StaffDashboardView | **完成（mock）** | 受付画面（検索+一覧+操作+当日券） |
| NotFoundView | **完成** | 404 |

**6/7 画面が mock で動作する状態。**

---

## 9. 現在のディレクトリ構成

```
frontend/src/
├── main.js
├── App.vue
├── style.css
├── router/
│   └── index.js
├── mock/
│   ├── events.js
│   └── reservations.js          ← 6件に拡充
├── composables/
│   ├── useReservationForm.js
│   └── useStaffActions.js       ← 新規
├── views/
│   ├── EventListView.vue        ← スタブ
│   ├── EventDetailView.vue      ← 完成(mock)
│   ├── ReserveView.vue          ← 完成(mock)
│   ├── ReservationConfirmView.vue ← 完成(mock)
│   ├── CheckinView.vue          ← 完成(mock)
│   ├── StaffDashboardView.vue   ← 新規: 完成(mock)
│   └── NotFoundView.vue         ← 完成
├── components/
│   ├── layout/
│   │   └── AppHeader.vue
│   ├── event/
│   │   ├── PerformanceCard.vue
│   │   └── SeatTierSelector.vue
│   ├── reservation/
│   │   ├── GuestInfoForm.vue
│   │   ├── ReservationSummary.vue
│   │   └── ReservationStatusBadge.vue
│   └── staff/
│       ├── StaffSearchBar.vue   ← 新規
│       ├── StaffReservationRow.vue ← 新規
│       └── WalkInForm.vue       ← 新規
└── assets/
```
