from datetime import timedelta

from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Reservation
from .serializers import (
    CompleteReservationSerializer,
    ReservationCreateSerializer,
    ReservationDetailSerializer,
    StaffReservationSerializer,
    WalkInCreateSerializer,
)


# ====================================================================
# Public API
# ====================================================================

@api_view(["POST"])
@permission_classes([AllowAny])
def reservation_create(request):
    """POST /api/reservations/ — 予約作成"""
    serializer = ReservationCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    reservation = serializer.save()
    return Response(
        ReservationDetailSerializer(reservation).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def reservation_by_token(request, token):
    """GET /api/reservations/<token>/ — 予約確認"""
    try:
        reservation = Reservation.objects.select_related(
            "performance__event", "seat_tier",
        ).get(token=token)
    except Reservation.DoesNotExist:
        return Response(
            {"detail": "予約が見つかりません"},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(ReservationDetailSerializer(reservation).data)


@api_view(["POST"])
@permission_classes([AllowAny])
def reservation_checkin(request, token):
    """POST /api/reservations/<token>/checkin/ — セルフチェックイン"""
    try:
        reservation = Reservation.objects.select_related(
            "performance",
        ).get(token=token)
    except Reservation.DoesNotExist:
        return Response(
            {"detail": "予約が見つかりません"},
            status=status.HTTP_404_NOT_FOUND,
        )

    # バリデーション
    if reservation.checked_in:
        return Response(
            {"detail": "すでにチェックイン済みです"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if reservation.reservation_type == "cash":
        return Response(
            {"detail": "現金予約はセルフチェックインできません"},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if reservation.status != "confirmed" or reservation.payment_status != "paid":
        return Response(
            {"detail": "この予約はチェックインできません"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    opens_at = reservation.performance.starts_at - timedelta(hours=1)
    now = timezone.now()
    if now < opens_at:
        opens_str = timezone.localtime(opens_at).strftime("%H:%M")
        return Response(
            {"detail": f"チェックイン可能時間前です（{opens_str} から）"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    reservation.checked_in = True
    reservation.checked_in_at = now
    reservation.save(update_fields=["checked_in", "checked_in_at", "updated_at"])

    return Response({
        "checked_in": True,
        "checked_in_at": reservation.checked_in_at,
    })


@api_view(["POST"])
@permission_classes([AllowAny])
def reservation_complete(request, token):
    """POST /api/reservations/<token>/complete/ — 仮受付を完成させる"""
    try:
        reservation = Reservation.objects.select_related(
            "performance__event", "seat_tier",
        ).get(token=token)
    except Reservation.DoesNotExist:
        return Response(
            {"detail": "予約が見つかりません"},
            status=status.HTTP_404_NOT_FOUND,
        )

    serializer = CompleteReservationSerializer(
        data=request.data,
        context={"reservation": reservation},
    )
    serializer.is_valid(raise_exception=True)
    reservation = serializer.save()

    # 完成後の最新状態を返す
    reservation.refresh_from_db()
    reservation = Reservation.objects.select_related(
        "performance__event", "seat_tier",
    ).get(pk=reservation.pk)
    return Response(ReservationDetailSerializer(reservation).data)


# ====================================================================
# Staff API (認証必須)
# ====================================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def staff_reservation_list(request):
    """GET /api/staff/reservations/?performance=&search= — 受付検索"""
    qs = Reservation.objects.select_related(
        "performance__event", "seat_tier",
    ).order_by("-created_at")

    performance_id = request.query_params.get("performance")
    if performance_id:
        qs = qs.filter(performance_id=performance_id)

    search = request.query_params.get("search", "").strip()
    if search:
        qs = qs.filter(
            Q(guest_name__icontains=search)
            | Q(guest_email__icontains=search)
            | Q(guest_phone__icontains=search)
            | Q(token__icontains=search)
        )

    serializer = StaffReservationSerializer(qs[:200], many=True)
    return Response({"count": len(serializer.data), "results": serializer.data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def staff_mark_paid(request, pk):
    """POST /api/staff/reservations/<id>/mark-paid/ — 現金受領"""
    try:
        reservation = Reservation.objects.get(pk=pk)
    except Reservation.DoesNotExist:
        return Response(
            {"detail": "予約が見つかりません"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if reservation.payment_status == "paid":
        return Response(
            {"detail": "すでに支払い済みです"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    reservation.payment_status = Reservation.PaymentStatus.PAID
    reservation.save(update_fields=["payment_status", "updated_at"])

    return Response({"id": reservation.pk, "payment_status": "paid"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def staff_check_in(request, pk):
    """POST /api/staff/reservations/<id>/check-in/ — 入場処理"""
    try:
        reservation = Reservation.objects.get(pk=pk)
    except Reservation.DoesNotExist:
        return Response(
            {"detail": "予約が見つかりません"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if reservation.checked_in:
        return Response(
            {"detail": "すでに入場済みです"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    now = timezone.now()
    reservation.checked_in = True
    reservation.checked_in_at = now
    reservation.save(update_fields=["checked_in", "checked_in_at", "updated_at"])

    return Response({
        "id": reservation.pk,
        "checked_in": True,
        "checked_in_at": reservation.checked_in_at,
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def staff_walk_in(request):
    """POST /api/staff/reservations/walk-in/ — 当日券作成"""
    serializer = WalkInCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    reservation = serializer.save()
    return Response(
        StaffReservationSerializer(reservation).data,
        status=status.HTTP_201_CREATED,
    )


# ====================================================================
# Stripe Checkout (token ベース)
# ====================================================================

@api_view(["POST"])
@permission_classes([AllowAny])
def reservation_checkout(request, token):
    """POST /api/reservations/<token>/checkout/ — Stripe Checkout Session 作成"""
    try:
        reservation = Reservation.objects.select_related(
            "performance__event", "seat_tier",
        ).get(token=token)
    except Reservation.DoesNotExist:
        return Response(
            {"detail": "予約が見つかりません"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if reservation.reservation_type != "card":
        return Response(
            {"detail": "この予約は Stripe 対象ではありません"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if reservation.status != "pending":
        return Response(
            {"detail": "この予約はすでに処理済みです"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    from payments.services import create_checkout_session

    try:
        checkout_url = create_checkout_session(reservation)
    except Exception as e:
        return Response(
            {"detail": f"Stripe エラー: {str(e)}"},
            status=status.HTTP_502_BAD_GATEWAY,
        )

    return Response({"checkout_url": checkout_url})
