# 作業報告書: フロントエンド F1 — プロジェクト骨格構築

- 日時: 2026-03-30 14:39
- 作業者: Claude (Opus 4.6)
- プロジェクト: Mogi（演劇向け最小票券管理システム）

---

## 1. 目的

Vue フロントエンドのプロジェクト骨格を構築する。
vue-router + Bootstrap を導入し、全7画面のルーティングを通す。

---

## 2. 前回レビューからの反映事項

| 指摘 | 対応 |
|------|------|
| F1 が6ファイルで広すぎるので2分割 | F1a(package.json, main.js, router) と F1b(App.vue, AppHeader, style.css) に分割して実施 |
| /staff の 401 時の扱いを明記 | router に `meta: { requiresAuth: true }` を付与。認証ガード実装は次ステップ |
| EventList の優先順位を下げる | ルーティングは全画面登録するが、実装順は予約導線優先に変更 |
| 実装順を予約導線優先に | 次ステップ以降: EventDetail → Reserve → Confirm → Checkin → Staff → EventList |

---

## 3. 変更ファイル一覧

| ファイル | 操作 | 概要 |
|---------|------|------|
| `frontend/package.json` | 書き換え | vue-router, axios, bootstrap 追加 |
| `frontend/src/main.js` | 書き換え | router 初期化、bootstrap CSS import |
| `frontend/src/router/index.js` | 新規 | 全7ルート定義（lazy load） |
| `frontend/src/App.vue` | 書き換え | AppHeader + RouterView 構成 |
| `frontend/src/components/layout/AppHeader.vue` | 新規 | Bootstrap navbar（作品一覧 + 受付リンク） |
| `frontend/src/style.css` | 書き換え | ボイラープレート削除、最小カスタム CSS |
| `frontend/src/views/EventListView.vue` | 新規 | スタブ（「作品一覧 - 準備中」） |
| `frontend/src/views/EventDetailView.vue` | 新規 | スタブ（slug 表示） |
| `frontend/src/views/ReserveView.vue` | 新規 | スタブ（slug + performanceId 表示） |
| `frontend/src/views/ReservationConfirmView.vue` | 新規 | スタブ（token 表示） |
| `frontend/src/views/CheckinView.vue` | 新規 | スタブ（token 表示） |
| `frontend/src/views/StaffDashboardView.vue` | 新規 | スタブ（「受付 - 準備中」） |
| `frontend/src/views/NotFoundView.vue` | 新規 | 404 ページ（トップへ戻るリンク付き） |
| `frontend/src/components/HelloWorld.vue` | 削除 | ボイラープレート |
| `frontend/src/assets/vue.svg` | 削除 | ボイラープレート |
| `frontend/src/assets/vite.svg` | 削除 | ボイラープレート |

---

## 4. 各ファイルの詳細

### 4.1 package.json

追加した dependencies:
- `vue-router@^4.5.0` — SPA ルーティング
- `axios@^1.7.0` — API 通信（次ステップで使用）
- `bootstrap@^5.3.0` — UI フレームワーク

### 4.2 main.js

```javascript
import 'bootstrap/dist/css/bootstrap.min.css'
import './style.css'
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

createApp(App).use(router).mount('#app')
```

- Bootstrap CSS をグローバル import
- Bootstrap JS は未 import（現時点で JS 依存コンポーネントを使わないため）
- 必要になった時点で `bootstrap/dist/js/bootstrap.bundle.min.js` を追加

### 4.3 router/index.js

| パス | name | view | props | meta |
|------|------|------|-------|------|
| `/` | event-list | EventListView | - | - |
| `/:slug` | event-detail | EventDetailView | `slug` | - |
| `/:slug/reserve/:performanceId` | reserve | ReserveView | `slug`, `performanceId` | - |
| `/reservation/:token` | reservation-confirm | ReservationConfirmView | `token` | - |
| `/reservation/:token/checkin` | checkin | CheckinView | `token` | - |
| `/staff` | staff-dashboard | StaffDashboardView | - | `requiresAuth: true` |
| `/:pathMatch(.*)*` | not-found | NotFoundView | - | - |

- 全 view は `() => import(...)` で lazy load（chunk 分割）
- `props: true` で route params を props として渡す
- `/staff` に `meta.requiresAuth` を付与（認証ガード実装は次ステップ）

**ルーティングの注意点:**
- `/:slug` と `/reservation/:token` は両方とも第1セグメントがパラメータだが、`/reservation/` は固定文字列なので先にマッチする
- `/:pathMatch(.*)*` は catch-all で 404 にフォールバック

### 4.4 App.vue

```vue
<AppHeader />
<main>
  <RouterView />
</main>
```

- AppHeader は全画面共通で表示
- `<main>` タグで RouterView をラップ

### 4.5 AppHeader.vue

- Bootstrap の `navbar navbar-dark bg-dark`
- リンク: 「作品一覧」(/) + 「受付」(/staff)
- `navbar-expand-sm` でモバイルではハンバーガーなし（リンク2つなので常時表示で十分）

### 4.6 style.css

ボイラープレートの CSS（create-vue 生成の hero, counter, ticks 等）をすべて削除。
Bootstrap がグローバルで効くので、カスタム CSS は最小限:

```css
body { min-height: 100vh; }
main { flex: 1; }
```

### 4.7 view スタブ（7画面）

すべてスタブ。`<div class="container py-4">` + タイトル + route params 表示。
次ステップで実際のコンテンツを入れていく。

---

## 5. 実行コマンドと動作確認結果

| コマンド | 結果 |
|---------|------|
| `npm install` | `added 30 packages, audited 67 packages` 成功 |
| `npx vite build` | 全7 view が chunk 分割されてビルド成功（505ms） |

ビルド出力:
```
dist/assets/index-CzoI9uMH.js      87.67 kB (vue + vue-router + bootstrap)
dist/assets/index-BwYukP15.css     230.09 kB (bootstrap CSS)
dist/assets/NotFoundView-*.js        0.46 kB
dist/assets/ReserveView-*.js         0.33 kB
dist/assets/CheckinView-*.js         0.30 kB
...
```

---

## 6. 未着手・残存事項

| 項目 | 備考 |
|------|------|
| api/client.js | axios インスタンス作成。次ステップ以降 |
| mock/ ディレクトリ | mock データ。F2 以降で作成 |
| composables/ | useReservationForm, useStaffActions。F4, F8 で作成 |
| /staff の認証ガード | router.beforeEach で実装。API 接続時に対応 |
| Bootstrap JS | ドロップダウン等が必要になった時点で追加 |
| vite.config.js の proxy 設定 | API 接続時に `server.proxy` を追加 |

---

## 7. 修正版の実装順（予約導線優先）

| Step | 内容 | 触るファイル |
|------|------|-------------|
| ~~F1~~ | ~~骨格~~ | **本ステップで完了** |
| **F2** | EventDetailView + PerformanceCard + mock | `views/EventDetailView.vue`, `components/event/PerformanceCard.vue`, `mock/events.js` |
| **F3** | ReserveView Step 1: SeatTierSelector | `views/ReserveView.vue`, `components/event/SeatTierSelector.vue`, `composables/useReservationForm.js` |
| **F4** | ReserveView Step 2-3: GuestInfoForm + 確認 | `components/reservation/GuestInfoForm.vue`, `components/reservation/ReservationSummary.vue` |
| **F5** | ReservationConfirmView + mock | `views/ReservationConfirmView.vue`, `mock/reservations.js`, `api/reservations.js` |
| **F6** | CheckinView + mock | `views/CheckinView.vue` |
| **F7** | StaffDashboardView: 検索 + 一覧 | `views/StaffDashboardView.vue`, `components/staff/StaffSearchBar.vue`, `components/staff/StaffReservationRow.vue` |
| **F8** | StaffDashboardView: 操作 + WalkIn | `components/staff/WalkInForm.vue`, `composables/useStaffActions.js` |
| **F9** | EventListView + mock | `views/EventListView.vue`, `api/events.js` |
| **F10** | API 実接続 | `api/client.js`, `api/events.js`, `api/reservations.js` |

---

## 8. 現在のディレクトリ構成

```
frontend/src/
├── main.js                      ← router + bootstrap 初期化
├── App.vue                      ← AppHeader + RouterView
├── style.css                    ← 最小カスタム CSS
├── router/
│   └── index.js                 ← 全7ルート定義
├── views/
│   ├── EventListView.vue        ← スタブ
│   ├── EventDetailView.vue      ← スタブ
│   ├── ReserveView.vue          ← スタブ
│   ├── ReservationConfirmView.vue ← スタブ
│   ├── CheckinView.vue          ← スタブ
│   ├── StaffDashboardView.vue   ← スタブ
│   └── NotFoundView.vue         ← 404
├── components/
│   └── layout/
│       └── AppHeader.vue        ← navbar
└── assets/
    └── hero.png                 ← 既存（残存）
```
