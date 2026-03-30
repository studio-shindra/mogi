<script setup>
import { ref, onMounted } from 'vue'
import { fetchReservation, checkin } from '../api/reservations.js'
import { IconCircleCheck, IconArmchair, IconTicket } from '@tabler/icons-vue'
import ReservationStatusBadge from '../components/reservation/ReservationStatusBadge.vue'

const props = defineProps({ token: String })

const reservation = ref(null)
const loading = ref(true)
const submitting = ref(false)
const done = ref(false)
const error = ref('')

onMounted(async () => {
  try {
    reservation.value = await fetchReservation(props.token)
  } catch (e) {
    // template handles null
  } finally {
    loading.value = false
  }
})

async function handleCheckin() {
  if (submitting.value) return
  error.value = ''
  submitting.value = true
  try {
    await checkin(props.token)
    done.value = true
  } catch (e) {
    error.value = e.response?.data?.detail || 'チェックインに失敗しました'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="container py-5" style="max-width: 640px; padding-top: 56px">
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-mogi" role="status" />
    </div>

    <template v-else-if="reservation">
      <!-- 完了 -->
      <template v-if="done">
        <div class="text-center py-5">
          <div class="mb-3">
            <IconCircleCheck :size="72" class="text-mogi" stroke-width="1.2" />
          </div>
          <h2 class="fs-4 fw-bold mb-3">チェックイン完了</h2>
          <div class="card mx-auto" style="max-width: 320px">
            <div class="card-body text-start">
              <div class="fw-bold mb-2">{{ reservation.guest_name }} 様</div>
              <div class="d-flex gap-3 small text-muted">
                <span class="d-flex align-items-center gap-1">
                  <IconArmchair :size="14" /> {{ reservation.seat_tier.name }}
                </span>
                <span class="d-flex align-items-center gap-1">
                  <IconTicket :size="14" /> {{ reservation.quantity }}枚
                </span>
              </div>
              <div class="small text-muted mt-1">{{ reservation.performance.label }}</div>
            </div>
          </div>
          <div class="mt-4">
            <RouterLink
              :to="{ name: 'reservation-confirm', params: { token } }"
              class="btn btn-outline-primary"
            >
              予約確認ページ
            </RouterLink>
          </div>
        </div>
      </template>

      <!-- チェックイン前 -->
      <template v-else>
        <h1 class="fs-4 fw-bold mb-4">セルフチェックイン</h1>

        <div class="mb-3">
          <ReservationStatusBadge
            :status="reservation.status"
            :payment-status="reservation.payment_status"
            :checked-in="reservation.checked_in"
          />
        </div>

        <div class="card mb-4">
          <div class="card-body">
            <div class="d-flex justify-content-between mb-2">
              <span class="text-muted small">お名前</span>
              <span class="fw-bold">{{ reservation.guest_name }}</span>
            </div>
            <div class="d-flex justify-content-between mb-2">
              <span class="text-muted small">公演</span>
              <span>{{ reservation.performance.label }}</span>
            </div>
            <div class="d-flex justify-content-between">
              <span class="text-muted small">席種</span>
              <span>{{ reservation.seat_tier.name }} × {{ reservation.quantity }}枚</span>
            </div>
          </div>
        </div>

        <div v-if="error" class="alert alert-danger border-0 mb-4">{{ error }}</div>

        <div v-if="reservation.checked_in" class="alert alert-info border-0">
          すでにチェックイン済みです。
        </div>

        <div v-else-if="reservation.reservation_type === 'cash'" class="alert alert-warning border-0">
          現金予約のお客様は受付にてチェックインをお願いいたします。
        </div>

        <template v-else-if="reservation.can_self_checkin">
          <button
            class="btn btn-primary btn-lg w-100 py-3"
            :disabled="submitting"
            @click="handleCheckin"
          >
            <span v-if="submitting" class="spinner-border spinner-border-sm me-2" />
            チェックインする
          </button>
        </template>

        <div v-else class="text-center text-muted small py-3">
          チェックインは開演1時間前から可能です
        </div>
      </template>
    </template>

    <template v-else>
      <div class="text-center py-5 text-muted">予約が見つかりません</div>
    </template>
  </div>
</template>
