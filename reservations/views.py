import logging

from django.db.models import Q, Sum
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import AccessLink, Reservation
from .serializers import (
    AccessLinkPublicSerializer,
    ApplicationCreateSerializer,
    ReservationCreateSerializer,
    ReservationDetailSerializer,
    StaffReservationSerializer,
    WalkInCreateSerializer,
)

logger = logging.getLogger(__name__)


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
    """Phase A: セルフチェックイン廃止。当日受付はスタッフ画面から行う。"""
    return Response(
        {"detail": "セルフチェックインは停止しました。当日は会場受付にお声がけください。"},
        status=status.HTTP_410_GONE,
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def reservation_complete(request, token):
    """Phase A: 決済連動の draft 完成フローを停止。"""
    return Response(
        {"detail": "この機能は停止しました。"},
        status=status.HTTP_410_GONE,
    )


# ====================================================================
# Staff API (認証必須)
# ====================================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def staff_reservation_list(request):
    """GET /api/staff/reservations/?performance=&search=&sales_channel= — 受付検索"""
    qs = Reservation.objects.select_related(
        "performance__event", "seat_tier",
    ).exclude(status=Reservation.Status.APPLIED).order_by("-created_at")

    performance_id = request.query_params.get("performance")
    if performance_id:
        qs = qs.filter(performance_id=performance_id)

    sales_channel = request.query_params.get("sales_channel", "").strip()
    if sales_channel:
        qs = qs.filter(sales_channel=sales_channel)

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
# AccessLink API（限定URL）
# ====================================================================

@api_view(["GET"])
@permission_classes([AllowAny])
def link_detail(request, token):
    """GET /api/links/<token>/ — 限定URL の公開情報を返す"""
    try:
        link = AccessLink.objects.select_related("event").prefetch_related(
            "event__performances__seat_tiers",
        ).get(token=token)
    except AccessLink.DoesNotExist:
        return Response(
            {"detail": "リンクが見つかりません"},
            status=status.HTTP_404_NOT_FOUND,
        )
    if not link.is_active:
        return Response(
            {"detail": "このリンクは無効です"},
            status=status.HTTP_410_GONE,
        )
    return Response(AccessLinkPublicSerializer(link).data)


# ====================================================================
# Application API（二次先行応募）
# ====================================================================

@api_view(["POST"])
@permission_classes([AllowAny])
def application_create(request):
    """POST /api/applications/ — 応募受付（在庫は消費しない）"""
    serializer = ApplicationCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    reservation = serializer.save()

    if reservation.guest_email:
        try:
            from .emails import send_application_received_email
            send_application_received_email(reservation)
        except Exception:
            logger.exception("応募受付メール送信失敗: reservation=%s", reservation.pk)

    return Response(
        ReservationDetailSerializer(reservation).data,
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def staff_application_list(request):
    """GET /api/staff/applications/ — 応募一覧（status=applied のみ）"""
    qs = Reservation.objects.select_related(
        "performance__event", "seat_tier",
    ).filter(status=Reservation.Status.APPLIED).order_by("-created_at")

    performance_id = request.query_params.get("performance")
    if performance_id:
        qs = qs.filter(performance_id=performance_id)

    fanclub = request.query_params.get("fanclub", "").strip().lower()
    if fanclub in ("true", "1", "yes"):
        qs = qs.filter(is_fanclub_member=True)
    elif fanclub in ("false", "0", "no"):
        qs = qs.filter(is_fanclub_member=False)

    search = request.query_params.get("search", "").strip()
    if search:
        qs = qs.filter(
            Q(guest_name__icontains=search)
            | Q(guest_email__icontains=search)
            | Q(guest_phone__icontains=search)
            | Q(token__icontains=search)
        )

    serializer = StaffReservationSerializer(qs[:500], many=True)
    return Response({"count": len(serializer.data), "results": serializer.data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def staff_application_confirm(request, pk):
    """POST /api/staff/applications/<id>/confirm/ — 応募を当選 → 予約確定へ"""
    try:
        reservation = Reservation.objects.select_related("seat_tier").get(pk=pk)
    except Reservation.DoesNotExist:
        return Response(
            {"detail": "応募が見つかりません"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if reservation.status != Reservation.Status.APPLIED:
        return Response(
            {"detail": "応募ステータスではありません"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 在庫チェック（当選時点で初めて消費）
    seat_tier = reservation.seat_tier
    if seat_tier is None:
        return Response(
            {"detail": "席種が未設定です"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    confirmed_qty = (
        Reservation.objects.filter(
            seat_tier=seat_tier,
            status__in=[Reservation.Status.PENDING, Reservation.Status.CONFIRMED],
        )
        .aggregate(total=Sum("quantity"))["total"]
        or 0
    )
    remaining = seat_tier.capacity - confirmed_qty
    if reservation.quantity > remaining:
        return Response(
            {"detail": f"残席不足。{seat_tier.name}: 残り{remaining}枚"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    now = timezone.now()
    stamp = timezone.localtime(now).strftime("%Y-%m-%d %H:%M")
    confirm_note = f"[system] application confirmed {stamp}"
    reservation.memo = (
        f"{reservation.memo}\n{confirm_note}".strip()
        if reservation.memo
        else confirm_note
    )
    reservation.status = Reservation.Status.CONFIRMED
    reservation.save(update_fields=["status", "memo", "updated_at"])

    return Response({
        "id": reservation.pk,
        "status": "confirmed",
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def staff_application_reject(request, pk):
    """POST /api/staff/applications/<id>/reject/ — 応募を落選へ"""
    try:
        reservation = Reservation.objects.get(pk=pk)
    except Reservation.DoesNotExist:
        return Response(
            {"detail": "応募が見つかりません"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if reservation.status != Reservation.Status.APPLIED:
        return Response(
            {"detail": "応募ステータスではありません"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    now = timezone.now()
    stamp = timezone.localtime(now).strftime("%Y-%m-%d %H:%M")
    reject_note = f"[system] application rejected {stamp}"
    reservation.memo = (
        f"{reservation.memo}\n{reject_note}".strip()
        if reservation.memo
        else reject_note
    )
    reservation.status = Reservation.Status.CANCELLED
    reservation.save(update_fields=["status", "memo", "updated_at"])

    return Response({
        "id": reservation.pk,
        "status": "cancelled",
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def staff_cancel(request, pk):
    """POST /api/staff/reservations/<id>/cancel/ — 予約キャンセル（在庫復帰）"""
    try:
        reservation = Reservation.objects.get(pk=pk)
    except Reservation.DoesNotExist:
        return Response(
            {"detail": "予約が見つかりません"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if reservation.status == Reservation.Status.CANCELLED:
        return Response(
            {"detail": "すでにキャンセル済みです"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    now = timezone.now()
    stamp = timezone.localtime(now).strftime("%Y-%m-%d %H:%M")
    cancel_note = f"[system] staff cancelled {stamp}"
    reservation.memo = (
        f"{reservation.memo}\n{cancel_note}".strip()
        if reservation.memo
        else cancel_note
    )
    reservation.status = Reservation.Status.CANCELLED
    reservation.save(update_fields=["status", "memo", "updated_at"])

    return Response({
        "id": reservation.pk,
        "status": "cancelled",
    })


# ====================================================================
# Stripe Checkout (token ベース)
# ====================================================================

@api_view(["POST"])
@permission_classes([AllowAny])
def reservation_checkout(request, token):
    """Phase A: オンライン事前決済を停止。当日会場にて現金精算。"""
    return Response(
        {"detail": "オンライン事前決済は停止しました。当日会場にてお支払いください。"},
        status=status.HTTP_410_GONE,
    )
