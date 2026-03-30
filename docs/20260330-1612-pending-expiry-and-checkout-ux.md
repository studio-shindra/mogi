# 作業報告書: pending 予約の期限切れ処理 + checkout 成否表示

- 日時: 2026-03-30 16:12
- 作業者: Claude (Opus 4.6)
- プロジェクト: Mogi（演劇向け最小票券管理システム）

---

## 1. 目的

1. Stripe 未決済のまま放置された pending 予約の在庫を解放する仕組みを追加
2. 予約確認ページで Stripe 決済直後の状態を分かりやすく表示する

---

## 2. 変更ファイル一覧

| ファイル | 操作 | 概要 |
|---------|------|------|
| `reservations/management/commands/expire_pending.py` | 新規 | pending 期限切れ処理コマンド |
| `frontend/src/views/ReservationConfirmView.vue` | 編集 | checkout=success/cancel のメッセージ表示 |

---

## 3. 各ファイルの詳細

### 3.1 expire_pending コマンド

```bash
python manage.py expire_pending              # 30分超の pending を cancelled に
python manage.py expire_pending --minutes 60 # 60分超
python manage.py expire_pending --dry-run    # 対象件数だけ表示
```

#### 動作

1. `status=pending` かつ `created_at < now - N分` の予約を取得
2. 一括で `status=cancelled` に更新
3. cancelled になった予約は在庫計算（`status__in=["pending", "confirmed"]`）から自動的に外れる

#### 設計判断

- 新しいステータス（expired）は追加しない。cancelled に統一
- 理由: 在庫計算のフィルタ条件を変更する必要がなく、既存ロジックとの整合性が保たれる
- Heroku 運用: Heroku Scheduler で10分ごとに実行する想定
  ```
  python manage.py expire_pending --minutes 30
  ```

#### 在庫への影響

- 在庫計算: `Sum(quantity, filter=Q(status__in=["pending", "confirmed"]))` は既存のまま
- pending → cancelled により、該当分の quantity が在庫に復帰する
- confirmed は影響なし

### 3.2 ReservationConfirmView の checkout メッセージ

URL クエリパラメータ `?checkout=success` / `?checkout=cancel` を見て表示を切り替え。

| 条件 | 表示 | Bootstrap クラス |
|------|------|-----------------|
| `?checkout=success` + status=pending | 「決済を確認中です。数秒後にページを再読み込みすると反映されます。」 | alert-info |
| `?checkout=success` + payment_status=paid | 「決済が完了しました。ご予約ありがとうございます。」 | alert-success |
| `?checkout=cancel` | 「決済は完了していません。お手数ですが再度お試しください。」 | alert-warning |
| クエリパラメータなし | メッセージなし | - |

#### タイミングの説明

- Stripe の success_url にリダイレクトされた直後、webhook がまだ到着していない場合がある
- この場合 status=pending のままなので「確認中」と表示
- ページを再読み込みすると webhook が処理済みであれば confirmed/paid に変わっている
- webhook が先に到着していれば、最初から「決済が完了しました」が表示される

---

## 4. 実行コマンドと動作確認結果

| コマンド | 結果 |
|---------|------|
| `python manage.py expire_pending --help` | ヘルプ正常表示 |
| `python manage.py expire_pending --dry-run` | 「期限切れの pending 予約はありません」（データなしの正常動作） |
| `npx vite build` | ビルド成功（330ms） |

---

## 5. 運用フロー

### pending の寿命管理

```
1. ユーザーが card 予約を作成 → status=pending
2. Stripe Checkout 画面にリダイレクト
3a. 決済完了 → webhook → confirmed/paid
3b. 決済キャンセル or 放置 → pending のまま
4. 30分経過 → expire_pending で cancelled に → 在庫復帰
```

### Heroku Scheduler 設定（デプロイ後）

```
Job: python manage.py expire_pending
Frequency: Every 10 minutes
```

---

## 6. 未着手・残存事項

| 項目 | 備考 |
|------|------|
| Heroku デプロイ準備 | Procfile, runtime.txt, .gitignore, .env.example |
| notifications app | メール送信（確認メール、リマインド、一括通知） |
| EventListView | スタブのまま（優先度低） |
| superuser 作成 | staff API 用 |
| git init + 初回コミット | まだ git リポジトリ化されていない |

---

## 7. 次ステップ候補

| 優先度 | 項目 |
|--------|------|
| 高 | デプロイ準備（Procfile, .gitignore, .env.example） |
| 高 | git init + 初回コミット |
| 中 | notifications app（確認メール → リマインド → 一括通知） |
| 低 | EventListView |

---

## 8. 現在のディレクトリ構成（差分のみ）

```
Mogi/
├── reservations/
│   └── management/commands/
│       ├── import_presale.py
│       └── expire_pending.py    ← 新規
├── frontend/src/views/
│   └── ReservationConfirmView.vue ← 編集: checkout メッセージ
└── docs/
    └── 20260330-1612-pending-expiry-and-checkout-ux.md  ← 本報告書
```
