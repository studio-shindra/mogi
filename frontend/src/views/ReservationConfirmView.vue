<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { fetchReservation, startCheckout } from '../api/reservations.js'
import { IconTicket, IconArmchair, IconMapPin, IconCalendar, IconScan, IconCreditCard } from '@tabler/icons-vue'
import ReservationStatusBadge from '../components/reservation/ReservationStatusBadge.vue'

const props = defineProps({ token: String })
const route = useRoute()

const reservation = ref(null)
const loading = ref(true)
const notFound = ref(false)
const checkoutLoading = ref(false)

const checkoutStatus = computed(() => route.query.checkout || null)

const canPay = computed(() => {
  if (!reservation.value) return false
  return (
    reservation.value.reservation_type === 'card' &&
    reservation.value.payment_status === 'unpaid' &&
    reservation.value.status !== 'cancelled'
  )
})

async function goToCheckout() {
  checkoutLoading.value = true
  try {
    const { checkout_url } = await startCheckout(props.token)
    window.location.href = checkout_url
  } catch (e) {
    alert('決済ページの取得に失敗しました。もう一度お試しください。')
    checkoutLoading.value = false
  }
}

onMounted(async () => {
  try {
    reservation.value = await fetchReservation(props.token)
  } catch (e) {
    if (e.response?.status === 404) notFound.value = true
  } finally {
    loading.value = false
  }
})

const typeLabel = { card: 'カード決済', cash: '当日現金払い', invite: '招待' }
</script>

<template>
  <div class="container py-5" style="max-width: 640px; padding-top: 56px">
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-mogi" role="status" />
    </div>

    <template v-else-if="reservation">
      <!-- Stripe 直後メッセージ -->
      <div
        v-if="checkoutStatus === 'success' && reservation.status === 'pending'"
        class="alert bg-mogi-light border-0 mb-4"
      >
        決済を確認中です。数秒後にページを再読み込みすると反映されます。
      </div>
      <div
        v-else-if="checkoutStatus === 'success' && reservation.payment_status === 'paid'"
        class="alert alert-success border-0 mb-4"
      >
        決済が完了しました。ご予約ありがとうございます。
      </div>
      <div
        v-else-if="checkoutStatus === 'cancel'"
        class="alert alert-warning border-0 mb-4"
      >
        決済は完了していません。お手数ですが再度お試しください。
      </div>

      <!-- チケットカード -->
      <div class="card overflow-hidden mb-4">
        <!-- ヘッダー部 -->
        <div class="card-body pb-0">
          <div class="d-flex justify-content-between align-items-start mb-3">
            <h1 class="fs-5 fw-bold mb-0">予約確認</h1>
            <ReservationStatusBadge
              :status="reservation.status"
              :payment-status="reservation.payment_status"
              :checked-in="reservation.checked_in"
            />
          </div>

          <!-- 状態メッセージ -->
          <div v-if="reservation.checked_in" class="alert alert-info border-0 small py-2 mb-3">
            チェックイン済みです。ご来場ありがとうございます。
          </div>
          <div
            v-else-if="reservation.reservation_type === 'cash' && reservation.payment_status === 'unpaid'"
            class="alert alert-warning border-0 small py-2 mb-3"
          >
            当日受付でお支払いください。
          </div>
        </div>

        <!-- 予約情報 -->
        <div class="card-body pt-0">
          <div class="mb-3">
            <div class="small text-muted">作品</div>
            <div class="fw-bold">{{ reservation.performance.event_title }}</div>
          </div>

          <div class="row g-3 mb-3">
            <div class="col-7">
              <div class="d-flex align-items-center gap-1">
                <IconCalendar :size="16" class="text-mogi" />
                <div>
                  <div class="small text-muted">公演</div>
                  <div class="fw-bold">{{ reservation.performance.label }}</div>
                </div>
              </div>
            </div>
            <div class="col-5">
              <div class="d-flex align-items-center gap-1">
                <IconMapPin :size="16" class="text-mogi" />
                <div>
                  <div class="small text-muted">会場</div>
                  <div class="fw-bold small">{{ reservation.performance.venue_name }}</div>
                </div>
              </div>
            </div>
          </div>

          <div class="row g-3">
            <div class="col-4">
              <div class="d-flex align-items-center gap-1">
                <IconArmchair :size="16" class="text-mogi" />
                <div>
                  <div class="small text-muted">席種</div>
                  <div class="fw-bold">{{ reservation.seat_tier.name }}</div>
                </div>
              </div>
            </div>
            <div class="col-4">
              <div class="d-flex align-items-center gap-1">
                <IconTicket :size="16" class="text-mogi" />
                <div>
                  <div class="small text-muted">枚数</div>
                  <div class="fw-bold">{{ reservation.quantity }}枚</div>
                </div>
              </div>
            </div>
            <div class="col-4">
              <div class="small text-muted">お支払い</div>
              <div class="fw-bold small">{{ typeLabel[reservation.reservation_type] }}</div>
            </div>
          </div>
        </div>

        <!-- 切り離し風 -->
        <div class="position-relative" style="height: 1px;">
          <div style="border-top: 2px dashed var(--mogi-border); position: absolute; left: 20px; right: 20px; top: 0;"></div>
          <div class="position-absolute rounded-circle" style="width: 24px; height: 24px; left: -12px; top: -12px; background: var(--mogi-bg);"></div>
          <div class="position-absolute rounded-circle" style="width: 24px; height: 24px; right: -12px; top: -12px; background: var(--mogi-bg);"></div>
        </div>

        <!-- お客様情報 -->
        <div class="card-body pt-3">
          <div class="fw-bold mb-1">{{ reservation.guest_name }}</div>
          <div v-if="reservation.guest_email" class="small text-muted">{{ reservation.guest_email }}</div>
          <div v-if="reservation.guest_phone" class="small text-muted">{{ reservation.guest_phone }}</div>
        </div>
      </div>

      <!-- 決済ボタン -->
      <div v-if="canPay" class="d-grid mb-3">
        <button
          class="btn btn-lg py-3 d-flex align-items-center justify-content-center gap-2"
          style="background: var(--mogi); color: #fff;"
          :disabled="checkoutLoading"
          @click="goToCheckout"
        >
          <span v-if="checkoutLoading" class="spinner-border spinner-border-sm" />
          <IconCreditCard v-else :size="22" />
          決済へ進む
        </button>
      </div>

      <!-- セルフチェックイン -->
      <div v-if="reservation.can_self_checkin" class="d-grid">
        <RouterLink
          :to="{ name: 'checkin', params: { token: reservation.token } }"
          class="btn btn-primary btn-lg py-3 d-flex align-items-center justify-content-center gap-2"
        >
          <IconScan :size="22" />
          セルフチェックイン
        </RouterLink>
      </div>

      <div
        v-else-if="
          !reservation.checked_in &&
          reservation.reservation_type !== 'cash' &&
          reservation.status === 'confirmed'
        "
        class="text-center text-muted small"
      >
        セルフチェックインは開演1時間前から可能です
      </div>
    </template>

    <template v-else>
      <div class="text-center py-5 text-muted">予約が見つかりません</div>
    </template>
  </div>
</template>
