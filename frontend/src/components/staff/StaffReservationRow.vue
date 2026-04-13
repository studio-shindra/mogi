<script setup>
import { ref } from 'vue'
import ReservationStatusBadge from '../reservation/ReservationStatusBadge.vue'

const props = defineProps({
  reservation: { type: Object, required: true },
})

const emit = defineEmits(['mark-paid', 'check-in'])

const acting = ref(false)

const typeLabel = { card: 'カード', cash: '現金', invite: '招待' }

async function onMarkPaid() {
  const name = props.reservation.guest_name
  if (!window.confirm(`${name} さんの現金受領を記録しますか？`)) return
  acting.value = true
  emit('mark-paid', props.reservation)
  setTimeout(() => (acting.value = false), 500)
}

async function onCheckIn() {
  const name = props.reservation.guest_name
  if (!window.confirm(`${name} さんを入場処理しますか？`)) return
  acting.value = true
  emit('check-in', props.reservation)
  setTimeout(() => (acting.value = false), 500)
}
</script>

<template>
  <tr>
    <!-- 名前 -->
    <td>
      <div class="fw-bold">{{ reservation.guest_name }}</div>
      <small class="text-muted">{{ reservation.guest_phone }}</small>
    </td>
    <!-- 席種・枚数 -->
    <td>
      {{ reservation.seat_tier.name }}
      <span class="text-muted">× {{ reservation.quantity }}</span>
    </td>
    <!-- 種別 -->
    <td>
      <small>{{ typeLabel[reservation.reservation_type] }}</small>
    </td>
    <!-- ステータス -->
    <td>
      <ReservationStatusBadge
        :status="reservation.status"
        :payment-status="reservation.payment_status"
        :checked-in="reservation.checked_in"
      />
    </td>
    <!-- メモ -->
    <td>
      <small class="text-muted">{{ reservation.memo }}</small>
    </td>
    <!-- 操作 -->
    <td class="text-end text-nowrap">
      <!-- 現金受領 -->
      <button
        v-if="reservation.payment_status === 'unpaid' && reservation.status === 'confirmed'"
        class="btn btn-sm btn-warning me-1"
        :disabled="acting"
        @click="onMarkPaid"
      >
        現金受領
      </button>
      <!-- 入場処理 -->
      <button
        v-if="!reservation.checked_in && reservation.status === 'confirmed'"
        class="btn btn-sm btn-success"
        :disabled="acting || (reservation.payment_status === 'unpaid')"
        @click="onCheckIn"
      >
        入場
      </button>
      <!-- 入場済み表示 -->
      <span v-if="reservation.checked_in" class="text-muted small">入場済</span>
    </td>
  </tr>
</template>
