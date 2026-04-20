"""Phase A/B1/B2/B3 の機械テスト。

目的:
    - 決済切離しと当日精算前提の挙動確認
    - sales_channel の運用
    - 二次先行応募受付
    - 限定URL（AccessLink）経由の予約/応募
    - 在庫連動の維持

実行:
    python3 manage.py test reservations
"""

from datetime import timedelta

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from events.models import Event, Performance, SeatTier
from reservations.models import AccessLink, Reservation


def _make_fixture():
    event = Event.objects.create(
        title="Test Event",
        slug="test-event",
        organizer_email="organizer@example.com",
    )
    perf = Performance.objects.create(
        event=event,
        label="1st",
        starts_at=timezone.now() + timedelta(days=7),
        open_at=timezone.now() + timedelta(days=7, hours=-1),
    )
    tier = SeatTier.objects.create(
        performance=perf,
        code=SeatTier.TierCode.CENTER,
        name="中央席",
        capacity=10,
        price_card=3000,
        price_cash=3000,
    )
    return event, perf, tier


class LinkDetailApiTests(APITestCase):
    def setUp(self):
        _event, self.perf, self.tier = _make_fixture()
        self.link = AccessLink.objects.create(
            performance=self.perf,
            mode=AccessLink.Mode.RESERVATION,
            sales_channel=Reservation.SalesChannel.ADVANCE,
            label="1次先行予約",
            is_active=True,
        )

    def test_link_detail_returns_mode_and_performance(self):
        res = self.client.get(f"/api/links/{self.link.token}/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["mode"], "reservation")
        self.assertEqual(res.data["sales_channel"], "advance")
        self.assertEqual(res.data["label"], "1次先行予約")
        self.assertTrue(res.data["is_active"])
        self.assertEqual(res.data["performance"]["id"], self.perf.id)
        self.assertEqual(len(res.data["performance"]["seat_tiers"]), 1)

    def test_link_detail_inactive_returns_410(self):
        self.link.is_active = False
        self.link.save()
        res = self.client.get(f"/api/links/{self.link.token}/")
        self.assertEqual(res.status_code, 410)

    def test_link_detail_not_found_returns_404(self):
        res = self.client.get("/api/links/nonexistent/")
        self.assertEqual(res.status_code, 404)


class ReservationWithLinkTests(APITestCase):
    """B3: 限定URL経由の予約で sales_channel が link に従う"""

    def setUp(self):
        _event, self.perf, self.tier = _make_fixture()
        self.link_a = AccessLink.objects.create(
            performance=self.perf,
            mode=AccessLink.Mode.RESERVATION,
            sales_channel=Reservation.SalesChannel.ADVANCE,
            label="1次先行予約",
        )
        self.link_c = AccessLink.objects.create(
            performance=self.perf,
            mode=AccessLink.Mode.RESERVATION,
            sales_channel=Reservation.SalesChannel.ADVANCE,
            label="2次先行通過者予約",
        )

    def _payload(self, token=""):
        return {
            "performance_id": self.perf.id,
            "seat_tier_id": self.tier.id,
            "quantity": 1,
            "guest_name": "山田太郎",
            "guest_phone": "090-0000-0000",
            "link_token": token,
        }

    def test_link_a_reservation_is_confirmed_advance(self):
        res = self.client.post("/api/reservations/", self._payload(self.link_a.token), format="json")
        self.assertEqual(res.status_code, 201)
        r = Reservation.objects.get(token=res.data["token"])
        self.assertEqual(r.status, "confirmed")
        self.assertEqual(r.sales_channel, "advance")
        self.assertEqual(r.payment_status, "unpaid")

    def test_link_c_reservation_is_confirmed_advance(self):
        res = self.client.post("/api/reservations/", self._payload(self.link_c.token), format="json")
        self.assertEqual(res.status_code, 201)
        r = Reservation.objects.get(token=res.data["token"])
        self.assertEqual(r.status, "confirmed")
        self.assertEqual(r.sales_channel, "advance")

    def test_reservation_without_link_is_confirmed_general(self):
        """本URL経由（link_token なし）は sales_channel=general"""
        res = self.client.post("/api/reservations/", self._payload(""), format="json")
        self.assertEqual(res.status_code, 201)
        r = Reservation.objects.get(token=res.data["token"])
        self.assertEqual(r.status, "confirmed")
        self.assertEqual(r.sales_channel, "general")

    def test_inactive_link_rejects_reservation(self):
        self.link_a.is_active = False
        self.link_a.save()
        res = self.client.post("/api/reservations/", self._payload(self.link_a.token), format="json")
        self.assertEqual(res.status_code, 400)

    def test_invalid_token_rejects_reservation(self):
        res = self.client.post("/api/reservations/", self._payload("invalid_token"), format="json")
        self.assertEqual(res.status_code, 400)

    def test_application_link_rejects_reservation_create(self):
        """application mode の link で /api/reservations/ は弾く"""
        app_link = AccessLink.objects.create(
            performance=self.perf,
            mode=AccessLink.Mode.APPLICATION,
            sales_channel=Reservation.SalesChannel.ADVANCE,
            label="2次先行応募",
        )
        res = self.client.post("/api/reservations/", self._payload(app_link.token), format="json")
        self.assertEqual(res.status_code, 400)

    def test_performance_mismatch_rejects(self):
        other_perf = Performance.objects.create(
            event=self.perf.event,
            label="2nd",
            starts_at=timezone.now() + timedelta(days=8),
            open_at=timezone.now() + timedelta(days=8, hours=-1),
        )
        other_link = AccessLink.objects.create(
            performance=other_perf,
            mode=AccessLink.Mode.RESERVATION,
            sales_channel=Reservation.SalesChannel.ADVANCE,
            label="他公演の先行予約",
        )
        res = self.client.post("/api/reservations/", self._payload(other_link.token), format="json")
        self.assertEqual(res.status_code, 400)


class ApplicationWithLinkTests(APITestCase):
    """B2/B3: 応募は status=applied、在庫非消費、link 経由で sales_channel 注入"""

    def setUp(self):
        _event, self.perf, self.tier = _make_fixture()
        self.link_b = AccessLink.objects.create(
            performance=self.perf,
            mode=AccessLink.Mode.APPLICATION,
            sales_channel=Reservation.SalesChannel.ADVANCE,
            label="2次先行応募",
        )

    def _payload(self, token=""):
        return {
            "performance_id": self.perf.id,
            "seat_tier_id": self.tier.id,
            "quantity": 2,
            "guest_name": "応募花子",
            "guest_phone": "090-1111-1111",
            "link_token": token,
        }

    def test_link_b_application_is_applied_advance(self):
        res = self.client.post("/api/applications/", self._payload(self.link_b.token), format="json")
        self.assertEqual(res.status_code, 201)
        r = Reservation.objects.get(token=res.data["token"])
        self.assertEqual(r.status, "applied")
        self.assertEqual(r.sales_channel, "advance")

    def test_reservation_link_rejects_application(self):
        res_link = AccessLink.objects.create(
            performance=self.perf,
            mode=AccessLink.Mode.RESERVATION,
            sales_channel=Reservation.SalesChannel.ADVANCE,
            label="予約用",
        )
        res = self.client.post("/api/applications/", self._payload(res_link.token), format="json")
        self.assertEqual(res.status_code, 400)

    def test_application_does_not_consume_stock(self):
        """応募は在庫を減らさない（10席満員まで応募できる、超過応募も可）"""
        for i in range(15):
            res = self.client.post(
                "/api/applications/",
                {
                    "performance_id": self.perf.id,
                    "seat_tier_id": self.tier.id,
                    "quantity": 1,
                    "guest_name": f"応募者{i}",
                    "guest_phone": f"090-{i:04d}-0000",
                    "link_token": self.link_b.token,
                },
                format="json",
            )
            self.assertEqual(res.status_code, 201)
        # applied 15件、在庫集計（pending/confirmed）は 0
        from django.db.models import Sum
        consumed = (
            Reservation.objects.filter(seat_tier=self.tier, status__in=["pending", "confirmed"])
            .aggregate(total=Sum("quantity"))["total"] or 0
        )
        self.assertEqual(consumed, 0)


class StockInvariantTests(APITestCase):
    """B1/B3: 在庫集計が status__in=[pending,confirmed] 固定で applied/cancelled は除外"""

    def setUp(self):
        _event, self.perf, self.tier = _make_fixture()

    def test_stock_aggregate_excludes_applied_and_cancelled(self):
        Reservation.objects.create(
            performance=self.perf, seat_tier=self.tier, quantity=3,
            reservation_type="cash", sales_channel="general",
            status="confirmed", payment_status="unpaid",
            guest_name="A",
        )
        Reservation.objects.create(
            performance=self.perf, seat_tier=self.tier, quantity=5,
            reservation_type="cash", sales_channel="advance",
            status="applied", payment_status="unpaid",
            guest_name="B",
        )
        Reservation.objects.create(
            performance=self.perf, seat_tier=self.tier, quantity=4,
            reservation_type="cash", sales_channel="general",
            status="cancelled", payment_status="unpaid",
            guest_name="C",
        )
        from django.db.models import Sum
        consumed = (
            Reservation.objects.filter(seat_tier=self.tier, status__in=["pending", "confirmed"])
            .aggregate(total=Sum("quantity"))["total"] or 0
        )
        self.assertEqual(consumed, 3)  # applied と cancelled は除外、confirmed の 3 のみ


class StaffSeparationTests(APITestCase):
    """B2: staff 予約一覧と応募一覧が分離される"""

    def setUp(self):
        _event, self.perf, self.tier = _make_fixture()
        self.user = User.objects.create_user("staff", password="pass")
        self.client.force_authenticate(user=self.user)

        self.confirmed = Reservation.objects.create(
            performance=self.perf, seat_tier=self.tier, quantity=1,
            reservation_type="cash", sales_channel="general",
            status="confirmed", payment_status="unpaid", guest_name="予約太郎",
        )
        self.applied = Reservation.objects.create(
            performance=self.perf, seat_tier=self.tier, quantity=1,
            reservation_type="cash", sales_channel="advance",
            status="applied", payment_status="unpaid", guest_name="応募花子",
        )

    def test_reservation_list_excludes_applied(self):
        res = self.client.get("/api/staff/reservations/")
        self.assertEqual(res.status_code, 200)
        ids = {r["id"] for r in res.data["results"]}
        self.assertIn(self.confirmed.id, ids)
        self.assertNotIn(self.applied.id, ids)

    def test_application_list_only_applied(self):
        res = self.client.get("/api/staff/applications/")
        self.assertEqual(res.status_code, 200)
        ids = {r["id"] for r in res.data["results"]}
        self.assertIn(self.applied.id, ids)
        self.assertNotIn(self.confirmed.id, ids)


class ApplicationConfirmTests(APITestCase):
    """B2: 応募 → 当選（confirmed）で在庫消費、落選で cancelled"""

    def setUp(self):
        _event, self.perf, self.tier = _make_fixture()
        self.user = User.objects.create_user("staff", password="pass")
        self.client.force_authenticate(user=self.user)

    def _make_applied(self, quantity=1):
        return Reservation.objects.create(
            performance=self.perf, seat_tier=self.tier, quantity=quantity,
            reservation_type="cash", sales_channel="advance",
            status="applied", payment_status="unpaid", guest_name="応募者",
        )

    def test_confirm_moves_applied_to_confirmed(self):
        app = self._make_applied()
        res = self.client.post(f"/api/staff/applications/{app.id}/confirm/")
        self.assertEqual(res.status_code, 200)
        app.refresh_from_db()
        self.assertEqual(app.status, "confirmed")
        self.assertIn("application confirmed", app.memo)

    def test_reject_moves_applied_to_cancelled(self):
        app = self._make_applied()
        res = self.client.post(f"/api/staff/applications/{app.id}/reject/")
        self.assertEqual(res.status_code, 200)
        app.refresh_from_db()
        self.assertEqual(app.status, "cancelled")
        self.assertIn("application rejected", app.memo)

    def test_confirm_rejects_when_stock_insufficient(self):
        # 先に 10 席分 confirmed を作って満席にする
        Reservation.objects.create(
            performance=self.perf, seat_tier=self.tier, quantity=10,
            reservation_type="cash", sales_channel="general",
            status="confirmed", payment_status="unpaid", guest_name="満席",
        )
        app = self._make_applied(quantity=1)
        res = self.client.post(f"/api/staff/applications/{app.id}/confirm/")
        self.assertEqual(res.status_code, 400)
        app.refresh_from_db()
        self.assertEqual(app.status, "applied")


class PhaseACheckinGateTests(APITestCase):
    """A: セルフチェックインは 410 Gone で停止している"""

    def setUp(self):
        _event, self.perf, self.tier = _make_fixture()

    def test_reservation_checkin_returns_410(self):
        r = Reservation.objects.create(
            performance=self.perf, seat_tier=self.tier, quantity=1,
            reservation_type="cash", sales_channel="general",
            status="confirmed", payment_status="paid", guest_name="来場者",
        )
        res = self.client.post(f"/api/reservations/{r.token}/checkin/")
        self.assertEqual(res.status_code, 410)

    def test_reservation_checkout_returns_410(self):
        r = Reservation.objects.create(
            performance=self.perf, seat_tier=self.tier, quantity=1,
            reservation_type="cash", sales_channel="general",
            status="confirmed", payment_status="unpaid", guest_name="決済",
        )
        res = self.client.post(f"/api/reservations/{r.token}/checkout/")
        self.assertEqual(res.status_code, 410)


class FanclubMemberTests(APITestCase):
    """応募フォームの FC会員フラグ"""

    def setUp(self):
        _event, self.perf, self.tier = _make_fixture()
        self.link_b = AccessLink.objects.create(
            performance=self.perf,
            mode=AccessLink.Mode.APPLICATION,
            sales_channel=Reservation.SalesChannel.ADVANCE,
            label="2次先行応募",
        )
        self.user = User.objects.create_user("staff", password="pass")

    def _payload(self, is_fc):
        return {
            "performance_id": self.perf.id,
            "seat_tier_id": self.tier.id,
            "quantity": 1,
            "guest_name": "FC太郎" if is_fc else "一般花子",
            "guest_phone": "090-0000-0000",
            "link_token": self.link_b.token,
            "is_fanclub_member": is_fc,
        }

    def test_application_stores_fanclub_true(self):
        res = self.client.post("/api/applications/", self._payload(True), format="json")
        self.assertEqual(res.status_code, 201)
        r = Reservation.objects.get(token=res.data["token"])
        self.assertTrue(r.is_fanclub_member)

    def test_application_stores_fanclub_false_default(self):
        """is_fanclub_member 未指定なら False"""
        payload = self._payload(False)
        payload.pop("is_fanclub_member")
        res = self.client.post("/api/applications/", payload, format="json")
        self.assertEqual(res.status_code, 201)
        r = Reservation.objects.get(token=res.data["token"])
        self.assertFalse(r.is_fanclub_member)

    def test_reservation_ignores_fanclub_field(self):
        """通常予約は is_fanclub_member を受け付けず default False"""
        res_link = AccessLink.objects.create(
            performance=self.perf,
            mode=AccessLink.Mode.RESERVATION,
            sales_channel=Reservation.SalesChannel.GENERAL,
            label="一般",
        )
        payload = {
            "performance_id": self.perf.id,
            "seat_tier_id": self.tier.id,
            "quantity": 1,
            "guest_name": "通常予約太郎",
            "guest_phone": "090-9999-9999",
            "link_token": res_link.token,
            "is_fanclub_member": True,  # 送っても無視される
        }
        res = self.client.post("/api/reservations/", payload, format="json")
        self.assertEqual(res.status_code, 201)
        r = Reservation.objects.get(token=res.data["token"])
        self.assertFalse(r.is_fanclub_member)

    def test_staff_application_list_filter_fanclub_true(self):
        self.client.post("/api/applications/", self._payload(True), format="json")
        self.client.post("/api/applications/", self._payload(False), format="json")
        self.client.force_authenticate(user=self.user)
        res = self.client.get("/api/staff/applications/?fanclub=true")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 1)
        self.assertTrue(res.data["results"][0]["is_fanclub_member"])

    def test_staff_application_list_filter_fanclub_false(self):
        self.client.post("/api/applications/", self._payload(True), format="json")
        self.client.post("/api/applications/", self._payload(False), format="json")
        self.client.force_authenticate(user=self.user)
        res = self.client.get("/api/staff/applications/?fanclub=false")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 1)
        self.assertFalse(res.data["results"][0]["is_fanclub_member"])


class StaffCancelTests(APITestCase):
    """B1: staff_cancel で在庫復帰、memo 自動追記"""

    def setUp(self):
        _event, self.perf, self.tier = _make_fixture()
        self.user = User.objects.create_user("staff", password="pass")
        self.client.force_authenticate(user=self.user)

    def test_cancel_releases_stock_and_appends_memo(self):
        r = Reservation.objects.create(
            performance=self.perf, seat_tier=self.tier, quantity=3,
            reservation_type="cash", sales_channel="general",
            status="confirmed", payment_status="unpaid", guest_name="キャンセル太郎",
        )
        res = self.client.post(f"/api/staff/reservations/{r.id}/cancel/")
        self.assertEqual(res.status_code, 200)
        r.refresh_from_db()
        self.assertEqual(r.status, "cancelled")
        self.assertIn("staff cancelled", r.memo)
        # 在庫集計から外れる
        from django.db.models import Sum
        consumed = (
            Reservation.objects.filter(seat_tier=self.tier, status__in=["pending", "confirmed"])
            .aggregate(total=Sum("quantity"))["total"] or 0
        )
        self.assertEqual(consumed, 0)
