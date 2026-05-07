<script setup>
import { ref, computed } from 'vue'
import ReservationStatusBadge from '../reservation/ReservationStatusBadge.vue'
import { formatJstDate, formatJstTime } from '../../utils/datetime.js'

const props = defineProps({
  reservation: { type: Object, required: true },
})

const emit = defineEmits(['mark-paid', 'check-in', 'cancel', 'row-click'])

const acting = ref(false)

const channelMeta = {
  advance: { label: '先行', cls: 'bg-primary' },
  general: { label: '一般', cls: 'bg-secondary' },
  staff: { label: '関係者', cls: 'bg-info text-dark' },
  invite: { label: '招待', cls: 'bg-success' },
  hold: { label: '取り置き', cls: 'bg-warning text-dark' },
  walk_in: { label: '当日券', cls: 'bg-mogi' },
}

const channelBadge = computed(() => {
  return channelMeta[props.reservation.sales_channel] || null
})

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

async function onCancel() {
  const name = props.reservation.guest_name
  if (!window.confirm(`${name} さんの予約をキャンセルしますか？（在庫は解放されます）`)) return
  acting.value = true
  emit('cancel', props.reservation)
  setTimeout(() => (acting.value = false), 500)
}
</script>

<template>
  <tr
    :class="{ 'text-muted': reservation.status === 'cancelled' }"
    style="cursor: pointer"
    @click="emit('row-click', reservation)"
  >
    <!-- 名前 -->
    <td>
      <div class="fw-bold">{{ reservation.guest_name }}</div>
      <small class="text-muted">{{ reservation.guest_phone }}</small>
    </td>
    <!-- 日程 -->
    <td class="text-nowrap">
      <div><small>{{ formatJstDate(reservation.performance?.starts_at) }}</small></div>
      <div><small class="text-muted">{{ formatJstTime(reservation.performance?.starts_at) }}</small></div>
    </td>
    <!-- 席種・枚数 -->
    <td class="text-nowrap">
      {{ reservation.seat_tier?.name }}
      <span class="text-muted">× {{ reservation.quantity }}</span>
    </td>
    <!-- 販売区分 -->
    <td class="text-nowrap">
      <span
        v-if="channelBadge"
        class="badge rounded-pill"
        :class="channelBadge.cls"
      >
        {{ channelBadge.label }}
      </span>
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
      <small class="text-muted" style="white-space: pre-line">{{ reservation.memo }}</small>
    </td>
    <!-- 操作 -->
    <td class="text-end text-nowrap" @click.stop>
      <template v-if="reservation.status === 'confirmed' && !reservation.checked_in">
        <!-- 主操作: 現金受領 + 入場（横並び） -->
        <div class="d-flex gap-1 justify-content-end mb-1">
          <button
            v-if="reservation.payment_status === 'unpaid'"
            class="btn btn-sm btn-warning"
            :disabled="acting"
            @click="onMarkPaid"
          >
            現金受領
          </button>
          <button
            class="btn btn-sm btn-success"
            :disabled="acting || (reservation.payment_status === 'unpaid')"
            @click="onCheckIn"
          >
            入場
          </button>
        </div>
        <!-- 副操作: キャンセル（別行） -->
        <button
          class="btn btn-sm btn-outline-danger"
          :disabled="acting"
          @click="onCancel"
        >
          キャンセル
        </button>
      </template>
      <!-- 入場済み表示 -->
      <span v-if="reservation.checked_in" class="text-muted small">入場済</span>
      <span v-if="reservation.status === 'cancelled'" class="text-muted small">キャンセル</span>
    </td>
  </tr>
</template>
