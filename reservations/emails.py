from django.conf import settings
from django.core.mail import send_mail


def send_reservation_email(reservation):
    """予約登録後にゲストへ通知メールを送信する（Phase A: 当日精算前提）。"""
    if not reservation.guest_email:
        return

    reservation_url = (
        f"{settings.FRONTEND_URL}/reservation/{reservation.token}"
    )
    performance = reservation.performance
    event = performance.event
    seat_tier = reservation.seat_tier

    subject = f"【{event.title}】ご予約ありがとうございます"

    lines = [
        f"{reservation.guest_name} 様",
        "",
        "ご予約ありがとうございます。",
        "以下の内容でご予約を承りました。",
        "",
        f"作品: {event.title}",
        f"公演: {performance.label}",
        f"日時: {performance.starts_at.strftime('%Y年%m月%d日 %H:%M')} 開演"
        f"（{performance.open_at.strftime('%H:%M')} 開場）",
    ]
    if event.venue_name:
        lines.append(f"会場: {event.venue_name}")
    lines += [
        f"席種: {seat_tier.name if seat_tier else '未選択'}",
        f"枚数: {reservation.quantity}枚",
    ]

    if reservation.reservation_type == "invite":
        lines += [
            "",
            "ご招待でのご予約です。当日は受付にてお名前をお伝えください。",
        ]
    else:
        lines += [
            "",
            "お支払いは当日会場にて現金でお願いいたします。",
            "ご来場の際は受付にてお名前をお伝えください。",
        ]

    lines += [
        "",
        "予約詳細は下記URLよりご確認いただけます。",
        reservation_url,
    ]

    if event.organizer_email:
        lines += [
            "",
            "ご予約のキャンセル・変更は下記までご連絡ください。",
            event.organizer_email,
        ]

    if event.email_signature:
        lines += ["", event.email_signature]
    else:
        lines += ["", "---", "Mogi"]

    body = "\n".join(lines)

    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[reservation.guest_email],
    )


def send_application_received_email(reservation):
    """応募受付メール（最小文面）。"""
    if not reservation.guest_email:
        return

    event = reservation.performance.event
    subject = f"【{event.title}】応募を受け付けました"
    lines = [
        f"{reservation.guest_name} 様",
        "",
        "応募を受け付けました。",
        "結果は後日ご案内します。",
        "",
        f"作品: {event.title}",
        f"公演: {reservation.performance.label}",
    ]
    if reservation.seat_tier:
        lines.append(f"席種: {reservation.seat_tier.name}")
    lines.append(f"枚数: {reservation.quantity}枚")
    if event.email_signature:
        lines += ["", event.email_signature]
    else:
        lines += ["", "---", "Mogi"]

    send_mail(
        subject=subject,
        message="\n".join(lines),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[reservation.guest_email],
    )


def send_application_won_email(reservation):
    """応募当選メール（運営が確定席を割り当てて確定した際に送る）。"""
    if not reservation.guest_email:
        return

    performance = reservation.performance
    event = performance.event
    seat_tier = reservation.seat_tier

    reservation_url = (
        f"{settings.FRONTEND_URL}/reservation/{reservation.token}"
    )

    subject = f"【{event.title}】ご応募結果のご案内（当選）"

    lines = [
        f"{reservation.guest_name} 様",
        "",
        "この度はご応募いただきありがとうございます。",
        "ご応募の結果、当選となりましたのでご案内いたします。",
        "",
        f"作品: {event.title}",
        f"公演: {performance.label}",
        f"日時: {performance.starts_at.strftime('%Y年%m月%d日 %H:%M')} 開演"
        f"（{performance.open_at.strftime('%H:%M')} 開場）",
    ]
    if event.venue_name:
        lines.append(f"会場: {event.venue_name}")
    lines += [
        f"確定席種: {seat_tier.name if seat_tier else '未設定'}",
        f"枚数: {reservation.quantity}枚",
        "",
        "お支払いは当日会場にて現金でお願いいたします。",
        "ご来場の際は受付にてお名前をお伝えください。",
        "",
        "予約詳細は下記URLよりご確認いただけます。",
        reservation_url,
    ]

    if event.organizer_email:
        lines += [
            "",
            "ご予約のキャンセル・変更は下記までご連絡ください。",
            event.organizer_email,
        ]

    if event.email_signature:
        lines += ["", event.email_signature]
    else:
        lines += ["", "---", "Mogi"]

    send_mail(
        subject=subject,
        message="\n".join(lines),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[reservation.guest_email],
    )


def send_payment_complete_email(reservation):
    """決済完了時にゲストへ確認メールを送信する。"""
    if not reservation.guest_email:
        return

    performance = reservation.performance
    event = performance.event
    seat_tier = reservation.seat_tier

    reservation_url = (
        f"{settings.FRONTEND_URL}/reservation/{reservation.token}"
    )

    price = seat_tier.price_card if seat_tier else 0
    total = price * reservation.quantity

    subject = f"【{event.title}】決済が完了しました"

    lines = [
        f"{reservation.guest_name} 様",
        "",
        "決済が完了しました。ご予約ありがとうございます。",
        "",
        "━━━ ご予約内容 ━━━",
        "",
        f"作品: {event.title}",
        f"公演: {performance.label}",
        f"日時: {performance.starts_at.strftime('%Y年%m月%d日 %H:%M')} 開演"
        f"（{performance.open_at.strftime('%H:%M')} 開場）",
        f"会場: {event.venue_name}" if event.venue_name else "",
        f"席種: {seat_tier.name}" if seat_tier else "",
        f"枚数: {reservation.quantity}枚",
        f"金額: ¥{total:,}",
        "",
        "━━━━━━━━━━━━━━━━",
        "",
        "予約詳細は下記URLよりご確認いただけます。",
        reservation_url,
    ]
    if event.email_signature:
        lines += ["", event.email_signature]
    else:
        lines += ["", "---", "Mogi"]

    # 空行が連続しないよう空文字の行はそのまま残す
    body = "\n".join(lines)

    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[reservation.guest_email],
    )
