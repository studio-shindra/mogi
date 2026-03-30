import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_checkout_session(reservation):
    """Stripe Checkout Session を作成し、URL を返す。"""
    unit_price = reservation.seat_tier.price_card
    line_items = [
        {
            "price_data": {
                "currency": "jpy",
                "unit_amount": unit_price,
                "product_data": {
                    "name": (
                        f"{reservation.performance.event.title} "
                        f"/ {reservation.performance.label} "
                        f"/ {reservation.seat_tier.name}"
                    ),
                },
            },
            "quantity": reservation.quantity,
        }
    ]

    success_url = (
        f"{settings.SITE_URL}/reservation/{reservation.token}"
        "?checkout=success"
    )
    cancel_url = (
        f"{settings.SITE_URL}/reservation/{reservation.token}"
        "?checkout=cancel"
    )

    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=line_items,
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=str(reservation.pk),
        metadata={
            "reservation_id": str(reservation.pk),
            "reservation_token": reservation.token,
        },
        customer_email=reservation.guest_email or None,
    )

    # session id を予約に保存
    reservation.stripe_checkout_session_id = session.id
    reservation.save(update_fields=["stripe_checkout_session_id", "updated_at"])

    return session.url
