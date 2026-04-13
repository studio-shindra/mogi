# 2026-04-13-1600 仮受付（draft）予約導線の実装

## 目的

「友人から "5/21 2枚よろしく" と来た」ケースに対応するため、
公演・枚数・名前だけの **仮受付（draft）** 状態を Reservation に追加し、
token URL を受け取った本人が席種と支払方法を選んで予約を完成させる導線を構築した。

## 状態遷移

```
draft ──→ pending ──→ confirmed
  │          │            │
  └──→ cancelled    cancelled
```

| 遷移 | トリガー | 補足 |
|------|---------|------|
| draft → pending | 本人が token ページで席種選択 + カード決済を選択 | Stripe Checkout へリダイレクト |
| draft → confirmed | 本人が token ページで席種選択 + 現金を選択 | pending を経由しない（決済待ちがないため） |
| pending → confirmed | Stripe webhook で決済完了 | 既存ロジックそのまま |
| draft/pending → cancelled | 管理者が Django admin で取消 | 手動操作 |

## 変更ファイル一覧

| # | ファイル | 変更内容 |
|---|---------|---------|
| 1 | `reservations/models.py` | Status に DRAFT 追加、seat_tier を nullable に、reservation_type を blank 許可 |
| 2 | `reservations/serializers.py` | AvailableSeatTierSerializer 追加、CompleteReservationSerializer 追加、ReservationDetailSerializer に available_seat_tiers フィールド追加（draft 時のみ席種一覧を返す） |
| 3 | `reservations/views.py` | `reservation_complete()` ビュー追加（POST /api/reservations/<token>/complete/） |
| 4 | `reservations/urls.py` | complete エンドポイントのルーティング追加 |
| 5 | `reservations/emails.py` | draft 対応のメールテンプレート分岐追加（席種未定でもエラーにならない、件名・本文を draft 用に変更） |
| 6 | `reservations/admin.py` | save_model で seat_tier または reservation_type が未設定なら自動的に draft ステータスにする処理追加 |
| 7 | `reservations/migrations/0003_alter_reservation_reservation_type_and_more.py` | マイグレーション（自動生成） |
| 8 | `frontend/src/api/reservations.js` | `completeReservation(token, payload)` API 関数追加 |
| 9 | `frontend/src/views/ReservationConfirmView.vue` | draft 時の「予約完成フォーム」UI 追加（席種リスト選択、支払方法ラジオ、メール入力、合計金額表示、確定ボタン）。完成済みなら従来の確認ページを表示 |
| 10 | `frontend/src/components/reservation/ReservationStatusBadge.vue` | draft バッジ（仮受付、bg-info）追加 |

## 各ファイルの変更詳細

### reservations/models.py
- `Status` TextChoices に `DRAFT = "draft", "仮受付"` を先頭に追加
- `seat_tier` ForeignKey に `null=True, blank=True` を追加（draft 時は席種未定のため）
- `reservation_type` CharField に `blank=True, default=""` を追加（draft 時は支払方法未定のため）

### reservations/serializers.py
- **AvailableSeatTierSerializer**: draft 予約の完成ページで表示する席種選択肢用。id, name, code, price_card, price_cash, remaining を返す
- **CompleteReservationSerializer**: draft → pending/confirmed の遷移処理。seat_tier_id と reservation_type を受け取り、バリデーション（status が draft か、席種が公演に属しているか、カード決済ならメール必須か、在庫があるか）を行い、reservation を更新する。カード決済なら pending + unpaid、現金なら confirmed + unpaid にする
- **ReservationDetailSerializer**: `available_seat_tiers` フィールドを追加。status が draft の場合のみ、performance に紐づく席種一覧を返す。draft 以外では null を返す。seat_tier に `allow_null=True` を追加

### reservations/views.py
- **reservation_complete(request, token)**: `POST /api/reservations/<token>/complete/` エンドポイント。AllowAny。CompleteReservationSerializer でバリデーション・保存後、ReservationDetailSerializer で最新状態を返す

### reservations/urls.py
- `path("reservations/<str:token>/complete/", ...)` を checkin の前に追加

### reservations/emails.py
- `is_draft` 判定を追加
- draft の場合: 件名を「ご予約のお手続きをお願いします」に変更、本文で「席種・お支払い方法を選択して予約を完成させてください」と案内し token URL を提示
- draft 以外: 従来のテンプレートを維持。`seat_tier.name` 参照を `seat_tier.name if seat_tier else '未選択'` に変更して null 安全にした

### reservations/admin.py
- `save_model` の先頭で、新規作成時に seat_tier_id または reservation_type が未設定なら `status = DRAFT`, `payment_status = UNPAID` を自動設定する処理を追加
- これにより admin で公演・枚数・名前だけを入力して保存すると自動的に draft になる

### frontend/src/api/reservations.js
- `completeReservation(token, payload)` を追加。`POST /api/reservations/${token}/complete/` を呼ぶ

### frontend/src/views/ReservationConfirmView.vue
- `isDraft` computed で `reservation.status === 'draft'` を判定
- draft 時: 席種をラジオボタン形式のリストグループで表示（残席数・カード価格・現金価格付き）。残席不足の席種は disabled。支払方法はカード/現金のラジオ。カード選択時かつメール未登録ならメール入力欄を表示。選択した席種と支払方法で合計金額を表示。確定ボタンで `completeReservation` API を呼び、カード決済なら続けて `startCheckout` で Stripe Checkout へリダイレクト、現金なら画面が確認モードに切り替わる
- 完成済み: 従来の確認ページをそのまま表示。seat_tier が null の場合に備え `reservation.seat_tier?.name || '未選択'` にフォールバック

### frontend/src/components/reservation/ReservationStatusBadge.vue
- statusMap に `draft: { label: '仮受付', cls: 'bg-info text-dark' }` を追加

## 実行コマンド

```bash
# マイグレーション生成 & 適用
./venv/bin/python manage.py makemigrations reservations
./venv/bin/python manage.py migrate

# Django システムチェック
./venv/bin/python manage.py check

# フロントエンドビルド
cd frontend && npx vite build
```

## 動作確認結果

- [x] `python manage.py check` — System check identified no issues
- [x] `python manage.py migrate` — マイグレーション正常適用
- [x] `vite build` — ビルド成功、エラーなし
- [x] モデルフィールド確認: Status.DRAFT = "draft"、seat_tier null=True blank=True、reservation_type blank=True default=""

## 運用フロー（想定）

1. 管理者が Django admin で Reservation を新規作成（公演・枚数・名前のみ入力、seat_tier と reservation_type は空）
2. 自動的に status=draft になる
3. guest_email が入力されていればメールが送信される（「席種・お支払い方法を選択して予約を完成させてください」という案内メール）
4. 本人が token URL にアクセスすると「予約を完成させてください」画面が表示される
5. 席種を選択し、支払方法を選択して確定ボタンを押す
6. カード決済の場合: draft → pending に遷移し、Stripe Checkout へリダイレクト。決済完了で pending → confirmed
7. 現金の場合: draft → confirmed に遷移し、確認画面が表示される

## 既存機能への影響

| 機能 | 影響 |
|------|------|
| 通常の新規予約（ReserveView） | **なし** — 従来通り seat_tier と reservation_type を必須で送るため draft にはならない |
| Stripe 決済 | **なし** — draft → pending 遷移後は既存フローに合流 |
| Stripe webhook | **なし** — pending → confirmed の処理は変更なし |
| セルフチェックイン | **なし** — can_self_checkin は status=confirmed & payment_status=paid を要求するので draft は対象外 |
| staff 画面 | **軽微** — draft が検索結果に表示される。StatusBadge に「仮受付」バッジが追加済み |
| pending 期限切れ処理 | **なし** — draft は期限切れ対象外（将来的に追加可能） |
| Django admin | **対応済み** — seat_tier/reservation_type 未設定での保存を許可し、自動的に draft にする |

## 未着手事項

- [ ] draft 予約の期限切れ処理（現状は期限なし。必要に応じて後から追加）
- [ ] staff 画面から draft を作成する UI（現状は Django admin からのみ）
- [ ] draft 作成用の専用 API エンドポイント（現状は admin のみ。将来的に staff API に追加可能）
- [ ] draft → complete 時にメール送信（完成通知メール）
- [ ] E2E テスト

## 次ステップ

1. **実運用テスト**: Django admin で実際に draft を作成し、token URL から席種選択→決済の導線を通しで確認
2. **draft 期限切れ**: 必要であれば draft にも pending と同様の期限切れ処理を追加
3. **staff 画面拡張**: staff ダッシュボードから直接 draft を作成できる UI を追加
4. **完成通知メール**: draft → confirmed/pending 遷移時に「予約が確定しました」メールを送信
