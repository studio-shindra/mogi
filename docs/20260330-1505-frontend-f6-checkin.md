# 作業報告書: フロントエンド F6 — CheckinView

- 日時: 2026-03-30 15:05
- 作業者: Claude (Opus 4.6)
- プロジェクト: Mogi（演劇向け最小票券管理システム）

---

## 1. 目的

セルフチェックイン画面を mock で実装する。
予約確認ページからの導線で、チェックイン実行 → 完了表示まで動く状態にする。

---

## 2. 変更ファイル一覧

| ファイル | 操作 | 概要 |
|---------|------|------|
| `frontend/src/views/CheckinView.vue` | 書き換え | セルフチェックイン画面の全実装 |

既存の mock/reservations.js と ReservationStatusBadge を再利用。新規ファイルなし。

---

## 3. CheckinView.vue の詳細

### state

| 変数 | 型 | 説明 |
|------|-----|------|
| reservation | ref(null) | 予約データ |
| loading | ref(true) | データ取得中 |
| submitting | ref(false) | チェックイン送信中 |
| done | ref(false) | チェックイン完了 |
| error | ref('') | エラーメッセージ |

### 表示パターン（5パターン）

| パターン | 表示 |
|---------|------|
| can_self_checkin=true | 予約概要 + 「チェックインする」ボタン |
| checked_in=true | 「すでにチェックイン済みです」アラート |
| reservation_type=cash | 「受付にてチェックインをお願いいたします」アラート |
| can_self_checkin=false（時間前） | 「チェックイン開始時刻前です。HH:MM からチェックインできます」 |
| done=true（完了後） | チェックマーク + 名前 + 席種 + 公演名 + 「予約確認ページに戻る」 |

### handleCheckin()

- mock では 500ms の delay 後にバリデーション実行
- チェック順: checked_in済み → cash → can_self_checkin=false → 成功
- 成功時: reservation の checked_in を true に、can_self_checkin を false に、done を true に
- API 接続後: POST /api/reservations/:token/checkin/ に差し替え

### エラーハンドリング

- checked_in 済み → 「すでにチェックイン済みです」
- cash → 「現金予約はセルフチェックインできません」
- 時間前 → 「チェックイン可能時間前です」
- エラーは `alert alert-danger` で表示

### 完了画面

- 大きなチェックマーク（&#10003;）
- 「チェックイン完了」
- ゲスト名 + 席種×枚数 + 公演ラベル
- 「予約確認ページに戻る」ボタン

---

## 4. 実行コマンドと動作確認結果

| コマンド | 結果 |
|---------|------|
| `npx vite build` | ビルド成功（296ms） |

ビルド出力:
- `CheckinView-*.js`: 3.48 kB
- `ReservationStatusBadge-*.js`: 2.42 kB（共有 chunk、ConfirmView と CheckinView で共有）

---

## 5. 画面の動作

**`/reservation/abc123def456/checkin`**（card, paid, チェックイン可能）:
1. 予約概要（名前、公演、席種）表示
2. 「チェックインする」ボタン
3. ボタン押下 → spinner → 完了画面（チェックマーク + 「チェックイン完了」）

**`/reservation/cash999xyz/checkin`**（cash）:
- 「現金予約のお客様は受付にてチェックインをお願いいたします」アラート

**`/reservation/checked111/checkin`**（チェックイン済み）:
- 「すでにチェックイン済みです」アラート

---

## 6. 未着手・残存事項

| 項目 | 備考 |
|------|------|
| API 接続 (POST /api/reservations/:token/checkin/) | バックエンド完成後 |
| 二重チェックイン防止 | API 側で制御。フロント側は submitting フラグで連打防止 |
| 時間チェック | 現在 mock なのでフロント側でのリアルタイム判定は未実装。API 側で制御 |

---

## 7. 次ステップ

**F7:** StaffDashboardView — 検索 + 予約一覧

対象ファイル:
- `frontend/src/views/StaffDashboardView.vue`
- `frontend/src/components/staff/StaffSearchBar.vue`
- `frontend/src/components/staff/StaffReservationRow.vue`

---

## 8. 現在のディレクトリ構成（差分のみ）

```
frontend/src/
├── views/
│   ├── CheckinView.vue          ← 書き換え: セルフチェックイン実装
│   └── ...（他は変更なし）
└── ...
```
