<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { fetchReservation, startCheckout, completeReservation } from '../api/reservations.js'
import { IconTicket, IconArmchair, IconMapPin, IconCalendar, IconScan, IconCreditCard } from '@tabler/icons-vue'
import ReservationStatusBadge from '../components/reservation/ReservationStatusBadge.vue'

const props = defineProps({ token: String })
const route = useRoute()

const reservation = ref(null)
const loading = ref(true)
const notFound = ref(false)
const checkoutLoading = ref(false)
const completeLoading = ref(false)
const completeError = ref('')

// draft 用フォーム
const selectedSeatTierId = ref(null)
const selectedReservationType = ref('card')
const guestEmail = ref('')

const checkoutStatus = computed(() => route.query.checkout || null)
const isDraft = computed(() => reservation.value?.status === 'draft')

const canPay = computed(() => {
  if (!reservation.value) return false
  return (
    reservation.value.reservation_type === 'card' &&
    reservation.value.payment_status === 'unpaid' &&
    reservation.value.status !== 'cancelled'
  )
})

const selectedTier = computed(() => {
  if (!reservation.value?.available_seat_tiers || !selectedSeatTierId.value) return null
  return reservation.value.available_seat_tiers.find(t => t.id === selectedSeatTierId.value)
})

const tierPrice = computed(() => {
  if (!selectedTier.value) return null
  return selectedReservationType.value === 'cash'
    ? selectedTier.value.price_cash
    : selectedTier.value.price_card
})

const canComplete = computed(() => {
  return selectedSeatTierId.value && selectedReservationType.value
})

async function submitComplete() {
  completeLoading.value = true
  completeError.value = ''
  try {
    const payload = {
      seat_tier_id: selectedSeatTierId.value,
      reservation_type: selectedReservationType.value,
    }
    if (guestEmail.value) payload.guest_email = guestEmail.value

    const updated = await completeReservation(props.token, payload)
    reservation.value = updated

    // カード決済なら即 Stripe Checkout へ
    if (updated.reservation_type === 'card' && updated.status === 'pending') {
      checkoutLoading.value = true
      const { checkout_url } = await startCheckout(props.token)
      window.location.href = checkout_url
    }
  } catch (e) {
    const detail = e.response?.data
    if (detail) {
      const messages = Object.values(detail).flat()
      completeError.value = messages.join(' / ')
    } else {
      completeError.value = '予約の確定に失敗しました。もう一度お試しください。'
    }
    checkoutLoading.value = false
  } finally {
    completeLoading.value = false
  }
}

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

      <!-- ======== draft: 予約完成フォーム ======== -->
      <template v-if="isDraft">
        <h2 class="fs-5 fw-bold mb-1">予約を完成させてください</h2>
        <p class="small text-muted mb-4">
          {{ reservation.guest_name }} 様 &mdash;
          {{ reservation.performance.event_title }} / {{ reservation.performance.label }}
        </p>

        <!-- 支払い方法 -->
        <div class="mb-4">
          <label class="form-label small text-muted">お支払い方法</label>
          <div class="d-flex gap-2">
            <button
              type="button"
              class="btn flex-fill"
              :class="selectedReservationType === 'card' ? 'btn-primary' : 'btn-outline-secondary'"
              @click="selectedReservationType = 'card'"
            >
              カード決済
            </button>
            <button
              type="button"
              class="btn flex-fill"
              :class="selectedReservationType === 'cash' ? 'btn-primary' : 'btn-outline-secondary'"
              @click="selectedReservationType = 'cash'"
            >
              当日現金払い
            </button>
          </div>
        </div>

        <!-- 席種選択 -->
        <div class="mb-4">
          <label class="form-label small text-muted">席種を選択</label>
          <div class="d-flex flex-column gap-2">
            <button
              v-for="tier in reservation.available_seat_tiers"
              :key="tier.id"
              type="button"
              class="card text-start border"
              :class="{
                'border-2': selectedSeatTierId === tier.id,
                'bg-mogi-light': selectedSeatTierId === tier.id,
              }"
              :style="selectedSeatTierId === tier.id ? 'border-color: var(--mogi-orange) !important' : ''"
              :disabled="tier.remaining < reservation.quantity"
              @click="selectedSeatTierId = tier.id"
            >
              <div class="card-body py-3 d-flex justify-content-between align-items-center">
                <div class="d-flex align-items-center gap-2">
                  <IconArmchair :size="20" class="text-mogi" />
                  <div>
                    <div class="fw-bold">{{ tier.name }}</div>
                    <div v-if="tier.remaining < reservation.quantity" class="text-muted small">残席不足</div>
                  </div>
                </div>
                <div class="fw-bold">
                  {{ (selectedReservationType === 'cash' ? tier.price_cash : tier.price_card).toLocaleString() }}<small class="text-muted fw-normal">円</small>
                </div>
              </div>
            </button>
          </div>
        </div>

        <!-- カード決済時のメール入力（未登録の場合） -->
        <div v-if="selectedReservationType === 'card' && !reservation.guest_email" class="mb-4">
          <label class="form-label small text-muted">メールアドレス（決済に必要です）</label>
          <input type="email" class="form-control" v-model="guestEmail" placeholder="email@example.com" />
        </div>

        <!-- 合計金額 -->
        <div v-if="selectedTier" class="card bg-mogi-light mb-4">
          <div class="card-body d-flex justify-content-between align-items-center py-3">
            <div>
              <span class="fw-bold">{{ selectedTier.name }}</span>
              <span class="text-muted ms-2">&times; {{ reservation.quantity }}枚</span>
            </div>
            <span class="fs-5 fw-bold text-mogi">
              {{ (tierPrice * reservation.quantity).toLocaleString() }}<small class="text-muted fw-normal">円</small>
            </span>
          </div>
        </div>

        <!-- エラーメッセージ -->
        <div v-if="completeError" class="alert alert-danger mb-3">{{ completeError }}</div>

        <!-- 確定ボタン -->
        <button
          class="btn btn-primary w-100 py-3"
          :disabled="!canComplete || completeLoading || checkoutLoading"
          @click="submitComplete"
        >
          <span v-if="completeLoading || checkoutLoading" class="spinner-border spinner-border-sm me-2" />
          {{ selectedReservationType === 'card' ? '決済へ進む' : '予約を確定する' }}
        </button>
      </template>

      <!-- ======== 通常: 予約確認表示 ======== -->
      <template v-else>
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
                    <div class="fw-bold">{{ reservation.seat_tier?.name || '未選択' }}</div>
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
                <div class="fw-bold small">{{ typeLabel[reservation.reservation_type] || '未選択' }}</div>
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
    </template>

    <template v-else>
      <div class="text-center py-5 text-muted">予約が見つかりません</div>
    </template>
  </div>
</template>
