import uuid

from django.conf import settings
from square import Square
from square.environment import SquareEnvironment


def _client():
    env = (
        SquareEnvironment.PRODUCTION
        if settings.SQUARE_ENVIRONMENT == "production"
        else SquareEnvironment.SANDBOX
    )
    return Square(token=settings.SQUARE_ACCESS_TOKEN, environment=env)


def create_checkout_session(reservation):
    """Square Payment Link を作成し、URL を返す。"""
    unit_price = reservation.seat_tier.price_card
    total_amount = unit_price * reservation.quantity

    name = (
        f"{reservation.performance.event.title} "
        f"/ {reservation.performance.label} "
        f"/ {reservation.seat_tier.name} x{reservation.quantity}"
    )

    redirect_url = (
        f"{settings.SITE_URL}/reservation/{reservation.token}"
        "?checkout=success"
    )

    response = _client().checkout.payment_links.create(
        idempotency_key=str(uuid.uuid4()),
        order={
            "location_id": settings.SQUARE_LOCATION_ID,
            "reference_id": reservation.token,
            "line_items": [
                {
                    "name": name,
                    "quantity": "1",
                    "base_price_money": {
                        "amount": total_amount,
                        "currency": "JPY",
                    },
                }
            ],
        },
        checkout_options={"redirect_url": redirect_url},
    )

    return response.payment_link.url
