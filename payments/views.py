import json
import logging

import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from square.utils.webhooks_helper import verify_signature

from payments.models import ProcessedWebhookEvent
from payments.services import _client
from reservations.emails import send_payment_complete_email
from reservations.models import Reservation

logger = logging.getLogger(__name__)


@csrf_exempt
def stripe_webhook(request):
    """POST /api/stripe/webhook/ — Stripe webhook 受信（旧経路、Phase 3 で削除予定）"""
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
        _handle_stripe_checkout_completed(session)

    return HttpResponse(status=200)


def _handle_stripe_checkout_completed(session):
    try:
        reservation_token = session["metadata"]["reservation_token"]
    except (KeyError, TypeError):
        return
    if not reservation_token:
        return

    try:
        reservation = Reservation.objects.get(token=reservation_token)
    except Reservation.DoesNotExist:
        return

    if reservation.status != Reservation.Status.PENDING:
        return

    reservation.status = Reservation.Status.CONFIRMED
    reservation.payment_status = Reservation.PaymentStatus.PAID
    reservation.save(update_fields=["status", "payment_status", "updated_at"])


@csrf_exempt
def square_webhook(request):
    """POST /api/square/webhook/ — Square webhook 受信"""
    raw_body = request.body.decode("utf-8")
    signature = request.META.get("HTTP_X_SQUARE_HMACSHA256_SIGNATURE", "")

    try:
        valid = verify_signature(
            request_body=raw_body,
            signature_header=signature,
            signature_key=settings.SQUARE_WEBHOOK_SIGNATURE_KEY,
            notification_url=settings.SQUARE_WEBHOOK_NOTIFICATION_URL,
        )
    except ValueError:
        return HttpResponse("Webhook not configured", status=500)

    if not valid:
        return HttpResponse("Invalid signature", status=400)

    try:
        event = json.loads(raw_body)
    except json.JSONDecodeError:
        return HttpResponse("Invalid payload", status=400)

    event_id = event.get("event_id")
    event_type = event.get("type", "")
    if not event_id:
        return HttpResponse("Missing event_id", status=400)

    _, created = ProcessedWebhookEvent.objects.get_or_create(
        event_id=event_id,
        defaults={"event_type": event_type},
    )
    if not created:
        return HttpResponse(status=200)

    if event_type == "payment.updated":
        _handle_square_payment_updated(event)

    return HttpResponse(status=200)


def _handle_square_payment_updated(event):
    payment = event.get("data", {}).get("object", {}).get("payment", {})
    if payment.get("status") != "COMPLETED":
        return

    order_id = payment.get("order_id")
    if not order_id:
        return

    try:
        order_resp = _client().orders.get(order_id=order_id)
    except Exception:
        return

    order = getattr(order_resp, "order", None)
    reference_id = getattr(order, "reference_id", None) if order else None
    if not reference_id:
        return

    try:
        reservation = Reservation.objects.get(token=reference_id)
    except Reservation.DoesNotExist:
        return

    if reservation.payment_status == Reservation.PaymentStatus.PAID:
        return

    reservation.status = Reservation.Status.CONFIRMED
    reservation.payment_status = Reservation.PaymentStatus.PAID
    reservation.save(update_fields=["status", "payment_status", "updated_at"])

    try:
        send_payment_complete_email(reservation)
    except Exception:
        logger.exception("send_payment_complete_email failed for %s", reservation.token)
