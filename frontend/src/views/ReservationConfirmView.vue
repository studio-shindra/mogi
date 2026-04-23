<script setup>
import { ref, onMounted } from 'vue'
import { fetchReservation } from '../api/reservations.js'
import { IconTicket, IconArmchair, IconMapPin, IconCalendar } from '@tabler/icons-vue'
import ReservationStatusBadge from '../components/reservation/ReservationStatusBadge.vue'

const props = defineProps({ token: String })

const reservation = ref(null)
const loading = ref(true)
const notFound = ref(false)

onMounted(async () => {
  try {
    reservation.value = await fetchReservation(props.token)
  } catch (e) {
    if (e.response?.status === 404) notFound.value = true
  } finally {
    loading.value = false
  }
})

const typeLabel = { cash: '当日精算', invite: 'ご招待' }
</script>

<template>
  <div class="container pb-5" style="max-width: 640px; padding-top: 6rem">
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-mogi" role="status" />
    </div>

    <template v-else-if="reservation">
      <!-- チケットカード -->
      <div class="card overflow-hidden mb-4">
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
            ご来場ありがとうございます。
          </div>
          <div
            v-else-if="reservation.status === 'cancelled'"
            class="alert alert-secondary border-0 small py-2 mb-3"
          >
            この予約はキャンセルされています。
          </div>
          <div
            v-else-if="reservation.reservation_type === 'invite'"
            class="alert bg-mogi-light border-0 small py-2 mb-3"
          >
            ご招待でのご予約です。当日は受付にてお名前をお伝えください。
          </div>
          <div
            v-else
            class="alert alert-warning border-0 small py-2 mb-3"
          >
            お支払いは当日会場にて現金でお願いいたします。
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
              <div class="fw-bold small">{{ typeLabel[reservation.reservation_type] || '当日精算' }}</div>
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

      <!-- 当日受付の案内 -->
      <div
        v-if="!reservation.checked_in && reservation.status !== 'cancelled'"
        class="text-center text-muted small"
      >
        当日は会場受付にて、お名前をお伝えください。
      </div>
    </template>

    <template v-else>
      <div class="text-center py-5 text-muted">予約が見つかりません</div>
    </template>
  </div>
</template>
