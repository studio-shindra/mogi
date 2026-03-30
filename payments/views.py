import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from reservations.models import Reservation


@csrf_exempt
def stripe_webhook(request):
    """POST /api/stripe/webhook/ — Stripe webhook 受信"""
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError:
        return HttpResponse("Invalid payload", status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse("Invalid signature", status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        _handle_checkout_completed(session)

    return HttpResponse(status=200)


def _handle_checkout_completed(session):
    """checkout.session.completed の処理。冪等。"""
    reservation_token = session.get("metadata", {}).get("reservation_token")
    if not reservation_token:
        return

    try:
        reservation = Reservation.objects.get(token=reservation_token)
    except Reservation.DoesNotExist:
        return

    # 冪等: pending の時だけ更新
    if reservation.status != "pending":
        return

    reservation.status = Reservation.Status.CONFIRMED
    reservation.payment_status = Reservation.PaymentStatus.PAID
    reservation.save(update_fields=["status", "payment_status", "updated_at"])
