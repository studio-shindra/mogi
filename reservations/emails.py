from django.conf import settings
from django.core.mail import send_mail


def send_reservation_email(reservation):
    """予約登録後にゲストへ通知メールを送信する。"""
    if not reservation.guest_email:
        return

    reservation_url = (
        f"{settings.FRONTEND_URL}/reservation/{reservation.token}"
    )
    performance = reservation.performance
    seat_tier = reservation.seat_tier

    subject = f"【{performance.event.title}】ご予約ありがとうございます"

    # --- 本文組み立て ---
    lines = [
        f"{reservation.guest_name} 様",
        "",
        "ご予約ありがとうございます。",
        "以下の内容でご予約を承りました。",
        "",
        f"公演: {performance}",
        f"席種: {seat_tier.name}",
        f"枚数: {reservation.quantity}枚",
    ]

    # 決済案内
    if reservation.reservation_type == "card" and reservation.payment_status == "unpaid":
        lines += [
            "",
            "下記URLより事前決済をお願いいたします。",
            reservation_url,
        ]
    elif reservation.reservation_type == "invite":
        lines += [
            "",
            "ご招待でのご予約です。",
            "",
            "予約詳細は下記URLよりご確認いただけます。",
            reservation_url,
        ]
    else:
        lines += [
            "",
            "予約詳細は下記URLよりご確認いただけます。",
            reservation_url,
        ]

    lines += [
        "",
        "---",
        performance.event.organizer_name or "",
    ]

    body = "\n".join(lines)

    send_mail(
        subject=subject,
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[reservation.guest_email],
    )
