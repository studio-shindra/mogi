import logging

from django.conf import settings
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.db.models import Q, Sum
from django.http import HttpResponse, HttpResponseNotFound
from django.utils import timezone
from django.utils.html import escape as html_escape
from django.views.decorators.csrf import ensure_csrf_cookie
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

    if reservation.guest_email:
        try:
            from .emails import send_reservation_email
            send_reservation_email(reservation)
        except Exception:
            logger.exception("予約通知メール送信失敗: reservation=%s", reservation.pk)

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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def staff_performance_summary(request):
    """GET /api/staff/performance-summary/ — 公演別の運営サマリー + 売上サマリー

    各公演について以下を返す:
      capacity / remaining / checked_in / not_checked_in（運営）
      count / quantity / revenue_estimate / unpaid_count / invite_qty /
      advance_qty / walk_in_qty（売上）

    母集団: Reservation.status in ('pending', 'confirmed')（applied/cancelled/draft は除外）。
    売上概算ルール:
      - reservation_type='invite' または sales_channel='invite' は 0 円
      - sales_channel='walk_in' は seat_tier.price_cash
      - それ以外は seat_tier.price_card
    """
    from django.db.models.functions import Coalesce
    from events.models import Performance

    active_statuses = [Reservation.Status.PENDING, Reservation.Status.CONFIRMED]

    performances = (
        Performance.objects
        .select_related("event")
        .annotate(
            capacity_sum=Coalesce(Sum("seat_tiers__capacity"), 0),
        )
        .order_by("starts_at")
    )

    results = []
    for perf in performances:
        reservations = (
            Reservation.objects
            .filter(performance=perf, status__in=active_statuses)
            .select_related("seat_tier")
        )

        count = 0
        quantity = 0
        checked_in_qty = 0
        revenue_estimate = 0
        unpaid_count = 0
        invite_qty = 0
        walk_in_qty = 0
        advance_qty = 0

        for r in reservations:
            count += 1
            quantity += r.quantity
            if r.checked_in:
                checked_in_qty += r.quantity
            if r.payment_status == Reservation.PaymentStatus.UNPAID:
                unpaid_count += 1

            is_invite = (
                r.reservation_type == Reservation.ReservationType.INVITE
                or r.sales_channel == Reservation.SalesChannel.INVITE
            )
            is_walk_in = r.sales_channel == Reservation.SalesChannel.WALK_IN

            if is_invite:
                invite_qty += r.quantity
            elif is_walk_in:
                walk_in_qty += r.quantity
                price = getattr(r.seat_tier, "price_cash", 0) or 0
                revenue_estimate += price * r.quantity
            else:
                advance_qty += r.quantity
                price = getattr(r.seat_tier, "price_card", 0) or 0
                revenue_estimate += price * r.quantity

        capacity = perf.capacity_sum or 0
        results.append({
            "performance_id": perf.id,
            "event_title": perf.event.title,
            "label": perf.label,
            "starts_at": perf.starts_at,
            "capacity": capacity,
            "remaining": max(capacity - quantity, 0),
            "checked_in": checked_in_qty,
            "not_checked_in": max(quantity - checked_in_qty, 0),
            "count": count,
            "quantity": quantity,
            "revenue_estimate": revenue_estimate,
            "unpaid_count": unpaid_count,
            "invite_qty": invite_qty,
            "advance_qty": advance_qty,
            "walk_in_qty": walk_in_qty,
        })

    return Response({"results": results})


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
    """POST /api/staff/applications/<id>/confirm/ — 応募を当選 → 予約確定へ

    body: { "assigned_seat_tier_id": <int> }
    確定席は運営が割り当てる。応募時の希望席との一致は問わない。
    """
    from events.models import SeatTier

    try:
        reservation = Reservation.objects.select_related("performance__event").get(pk=pk)
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

    assigned_id = request.data.get("assigned_seat_tier_id")
    if not assigned_id:
        return Response(
            {"detail": "確定席（assigned_seat_tier_id）を指定してください"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        seat_tier = SeatTier.objects.get(pk=assigned_id)
    except (SeatTier.DoesNotExist, ValueError, TypeError):
        return Response(
            {"detail": "指定された席種が見つかりません"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if seat_tier.performance_id != reservation.performance_id:
        return Response(
            {"detail": "この席種はこの公演に属していません"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 在庫チェック（当選時点で初めて消費）
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
    confirm_note = f"[system] application confirmed {stamp} → {seat_tier.name}"
    reservation.seat_tier = seat_tier
    reservation.memo = (
        f"{reservation.memo}\n{confirm_note}".strip()
        if reservation.memo
        else confirm_note
    )
    reservation.status = Reservation.Status.CONFIRMED
    reservation.save(update_fields=["seat_tier", "status", "memo", "updated_at"])

    email_sent = False
    if reservation.guest_email:
        try:
            from .emails import send_application_won_email
            send_application_won_email(reservation)
            email_sent = True
        except Exception:
            logger.exception("当選メール送信失敗: reservation=%s", reservation.pk)

    return Response({
        "id": reservation.pk,
        "status": "confirmed",
        "seat_tier_id": seat_tier.pk,
        "email_sent": email_sent,
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


# ====================================================================
# OGP HTML (SNSクローラー向け)
# ====================================================================

def link_ogp_html(request, token):
    """GET /r/<token>/ — LINE/Twitter/FB 等クローラー向け OGP メタタグ入り HTML。
    Netlify 側で User-Agent 判定し、クローラーのみ Heroku にプロキシされる想定。
    """
    try:
        link = AccessLink.objects.select_related("event").get(token=token)
    except AccessLink.DoesNotExist:
        return HttpResponseNotFound("Not Found")

    event = link.event
    title = f"{event.title} | {link.label}" if link.label else event.title

    if event.description:
        description = event.description
    elif event.organizer_name:
        description = f"{event.organizer_name} 主催の公演チケット受付ページです"
    else:
        description = "公演チケット受付ページです"

    image_url = link.header_image_url or ""
    page_url = f"{settings.FRONTEND_URL.rstrip('/')}/r/{token}/"

    t = html_escape(title)
    d = html_escape(description)
    i = html_escape(image_url)
    u = html_escape(page_url)

    image_tags = ""
    if image_url:
        image_tags = (
            f'<meta property="og:image" content="{i}">\n'
            f'<meta name="twitter:image" content="{i}">\n'
        )
    twitter_card = "summary_large_image" if image_url else "summary"

    html = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t}</title>
<meta name="description" content="{d}">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:type" content="website">
<meta property="og:url" content="{u}">
{image_tags}<meta name="twitter:card" content="{twitter_card}">
<meta name="twitter:title" content="{t}">
<meta name="twitter:description" content="{d}">
</head>
<body>
<p><a href="{u}">こちらをタップして開く</a></p>
</body>
</html>
"""
    return HttpResponse(html, content_type="text/html; charset=utf-8")


# ====================================================================
# Auth API（/manage 用）
# ====================================================================

def _user_payload(user):
    return {
        "username": user.username,
        "is_staff": bool(user.is_staff or user.is_superuser),
    }


@api_view(["POST"])
@permission_classes([AllowAny])
def auth_login(request):
    """POST /api/auth/login/ — username/password でセッションログイン"""
    username = (request.data.get("username") or "").strip()
    password = request.data.get("password") or ""
    if not username or not password:
        return Response({"detail": "ユーザー名とパスワードを入力してください。"},
                        status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(request, username=username, password=password)
    if user is None or not user.is_active:
        return Response({"detail": "ログインに失敗しました。"},
                        status=status.HTTP_401_UNAUTHORIZED)
    if not (user.is_staff or user.is_superuser):
        return Response({"detail": "管理画面への権限がありません。"},
                        status=status.HTTP_403_FORBIDDEN)

    django_login(request, user)
    return Response(_user_payload(user))


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def auth_logout(request):
    """POST /api/auth/logout/"""
    django_logout(request)
    return Response(status=status.HTTP_204_NO_CONTENT)


@ensure_csrf_cookie
@api_view(["GET"])
@permission_classes([AllowAny])
def auth_me(request):
    """GET /api/auth/me/ — 認証状態確認（CSRFクッキー発行も兼ねる）"""
    if request.user.is_authenticated:
        return Response(_user_payload(request.user))
    return Response({"username": None, "is_staff": False})
