# 当日用管理画面 mock依存解消（Turn 1）

## 目的

当日受付画面（StaffDashboardView）が mock データを直接参照していたため、
本番環境では公演フィルタ・当日券登録フォームの公演/席種選択肢が動かなかった。
real API から公演一覧・席種を取得するように切り替え、本番運用可能にする。

## 変更ファイル一覧

| # | ファイル | 変更内容 |
|---|---------|---------|
| 1 | `frontend/src/composables/useStaffActions.js` | `performances` ref と `loadPerformances()` を追加。`fetchEvents()` → `fetchEventDetail(slug)` で公演+席種を取得 |
| 2 | `frontend/src/views/StaffDashboardView.vue` | `mockPerformanceOptions` のインポートを削除。`staff.performances.value` を SearchBar / WalkInForm に渡すよう変更。`onMounted` で `loadPerformances()` を呼ぶ |
| 3 | `frontend/src/components/staff/WalkInForm.vue` | `mockEventDetail` のインポートを削除。`performances` を props で受け取るよう変更。watch で初期値を設定 |

## 各ファイルの変更内容

### useStaffActions.js
- `fetchEvents`, `fetchEventDetail` をインポート
- `performances` ref（公演リスト）と `eventDetail` ref を追加
- `loadPerformances()`: `fetchEvents()` で最初のイベントの slug を取得 → `fetchEventDetail(slug)` で公演+席種をロード
- return に `performances`, `eventDetail`, `loadPerformances` を追加

### StaffDashboardView.vue
- `mockPerformanceOptions` インポートを削除
- `onMounted` で `await staff.loadPerformances()` → `staff.search()` の順に実行
- StaffSearchBar の `:performances` に `staff.performances.value` を渡す
- WalkInForm に `:performances="staff.performances.value"` を渡す

### WalkInForm.vue
- `mockEventDetail` インポートを削除
- `defineProps({ performances: Array })` で親から受け取る
- `watch` で performances が後から渡された場合に `selectedPerfId` を初期化
- テンプレート内の `performances` を `props.performances` に変更
- `selectedPerf` computed も `props.performances` を参照

## バックエンド変更

なし。既存の `GET /api/events/` と `GET /api/events/<slug>/` をそのまま利用。

## 実行コマンド

```bash
cd frontend && npx vite build
```

## 動作確認結果

- ビルド成功（エラーなし）
- 3ファイルすべてで `mock` への参照が 0 件であることを grep で確認

## 本番での動作確認手順

1. `/staff` にアクセス
2. 公演ドロップダウンに DB のデータが表示されること
3. 公演を選択して検索 → 結果が絞り込まれること
4. 「当日券登録」を開く → 公演・席種の選択肢が DB データであること
5. 当日券を登録 → 一覧に追加されること
6. 現金受領・入場ボタンが従来通り動作すること

## 未着手事項

- 確認ダイアログ（現金受領・入場の誤タップ防止）
- エラーフィードバック（操作失敗時のユーザー通知）
- ルーターガード（未ログイン時のリダイレクト）

## 次ステップ

Turn 2: 確認ダイアログ + エラーフィードバックの追加（StaffReservationRow.vue, useStaffActions.js）
Turn 3: ルーターガード（router/index.js）
