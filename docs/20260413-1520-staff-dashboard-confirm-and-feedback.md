# 当日用管理画面 確認ダイアログ＋フィードバック（Turn 2）

## 目的

受付スタッフが現金受領・入場ボタンを誤タップした場合に取り消せない問題と、
API 失敗時に何が起きたか分からない問題を解消する。
成功時にも最小限のフィードバックを表示し、操作結果を視覚的に確認できるようにする。

## 変更ファイル一覧

| # | ファイル | 変更内容 |
|---|---------|---------|
| 1 | `frontend/src/components/staff/StaffReservationRow.vue` | 現金受領・入場ボタンに `window.confirm()` を追加 |
| 2 | `frontend/src/composables/useStaffActions.js` | `flash` ref と `setFlash()` を追加。markPaid / checkIn / createWalkIn に try/catch + 成功/失敗メッセージ |
| 3 | `frontend/src/views/StaffDashboardView.vue` | flash メッセージの表示 UI を追加。handleWalkIn に try/catch |

## 各ファイルの変更内容

### StaffReservationRow.vue
- `onMarkPaid()`: emit 前に `window.confirm('${名前} さんの現金受領を記録しますか？')` を追加。キャンセルで中断
- `onCheckIn()`: emit 前に `window.confirm('${名前} さんを入場処理しますか？')` を追加。キャンセルで中断

### useStaffActions.js
- `flash` ref を追加（`{ type: 'success' | 'error', message }` or `null`）
- `setFlash(type, message)` ヘルパーを追加。3秒後に自動消去
- `markPaid()`: try/catch 追加。成功時「現金受領を記録しました」、失敗時 API のエラー詳細を表示
- `checkIn()`: try/catch 追加。成功時「入場を記録しました」、失敗時エラー詳細を表示
- `createWalkIn()`: try/catch 追加。成功時「当日券を登録しました」、失敗時エラー詳細を表示。失敗時は re-throw してフォームを閉じない

### StaffDashboardView.vue
- ヘッダー直下に flash メッセージ表示を追加（Bootstrap alert-success / alert-danger）
- `handleWalkIn()`: try/catch 追加。失敗時はフォームを閉じない（flash は useStaffActions 側で設定済み）

## バックエンド変更

なし。

## 実行コマンド

```bash
cd frontend && npx vite build
```

## 動作確認結果

- ビルド成功（エラーなし）

## 本番での動作確認手順

1. 予約一覧で「現金受領」を押す → 確認ダイアログが出ること
2. 確認ダイアログで「キャンセル」 → 何も起きないこと
3. 確認ダイアログで「OK」 → 緑色のフラッシュ「現金受領を記録しました」が出ること
4. 「入場」ボタンも同様に確認ダイアログ → 成功フラッシュ
5. ネットワークエラー時 → 赤色のフラッシュにエラー内容が表示されること
6. 当日券登録成功 → 緑色フラッシュ + フォームが閉じること
7. 当日券登録失敗 → 赤色フラッシュ + フォームが開いたままであること
8. フラッシュメッセージが3秒後に自動消去されること

## 未着手事項

- ルーターガード（未ログイン時のリダイレクト）

## 次ステップ

Turn 3: ルーターガード（router/index.js）
