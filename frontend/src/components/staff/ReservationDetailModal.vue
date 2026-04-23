<script setup>
import { computed, ref, watch } from 'vue'
import ReservationStatusBadge from '../reservation/ReservationStatusBadge.vue'
import { formatJstDateTime } from '../../utils/datetime.js'

const props = defineProps({
  reservation: { type: Object, default: null },
})

const emit = defineEmits(['close'])

const typeLabel = { card: 'カード', cash: '当日精算', invite: 'ご招待' }

const channelLabel = {
  advance: '先行',
  general: '一般',
  staff: '関係者',
  invite: '招待',
  hold: '取り置き',
  walk_in: '当日券',
}

const statusLabel = {
  draft: '仮受付',
  pending: '仮予約',
  confirmed: '確定',
  cancelled: 'キャンセル',
}

const payLabel = {
  unpaid: '当日精算',
  paid: '支払済',
  refunded: '返金済',
}

const copied = ref(false)

const shareText = computed(() => {
  const r = props.reservation
  if (!r) return ''
  const lines = ['【予約内容】']
  lines.push(`お名前：${r.guest_name || ''}`)
  if (r.performance?.event_title) lines.push(`作品：${r.performance.event_title}`)
  lines.push(`公演：${formatJstDateTime(r.performance?.starts_at)}`)
  if (r.performance?.venue_name) lines.push(`会場：${r.performance.venue_name}`)
  const seat = r.seat_tier?.name || '未選択'
  lines.push(`席種：${seat} × ${r.quantity}`)
  if (r.sales_channel) {
    lines.push(`区分：${r.sales_channel_display || channelLabel[r.sales_channel] || r.sales_channel}`)
  }
  if (r.status) lines.push(`状態：${statusLabel[r.status] || r.status}`)
  const pay = r.reservation_type === 'invite'
    ? 'ご招待'
    : (payLabel[r.payment_status] || typeLabel[r.reservation_type] || '当日精算')
  lines.push(`お支払い：${pay}`)
  if (r.token) lines.push(`予約番号：${r.token}`)
  return lines.join('\n')
})

async function onCopy() {
  try {
    await navigator.clipboard.writeText(shareText.value)
    copied.value = true
    setTimeout(() => (copied.value = false), 1800)
  } catch {
    // フォールバック: テキストエリア経由
    const ta = document.createElement('textarea')
    ta.value = shareText.value
    document.body.appendChild(ta)
    ta.select()
    try { document.execCommand('copy') } catch {}
    document.body.removeChild(ta)
    copied.value = true
    setTimeout(() => (copied.value = false), 1800)
  }
}

watch(() => props.reservation, () => { copied.value = false })
</script>

<template>
  <div
    v-if="reservation"
    class="modal-backdrop-custom"
    @click.self="emit('close')"
  >
    <div class="modal-panel card shadow">
      <div class="card-body pb-0">
        <div class="d-flex justify-content-between align-items-start mb-3">
          <h5 class="fw-bold mb-0">予約詳細</h5>
          <ReservationStatusBadge
            :status="reservation.status"
            :payment-status="reservation.payment_status"
            :checked-in="reservation.checked_in"
          />
        </div>
      </div>

      <div class="card-body pt-0">
        <div class="mb-3" v-if="reservation.performance?.event_title">
          <div class="small text-muted">作品</div>
          <div class="fw-bold">{{ reservation.performance.event_title }}</div>
        </div>

        <div class="row g-3 mb-3">
          <div class="col-7">
            <div class="small text-muted">公演</div>
            <div class="fw-bold">{{ formatJstDateTime(reservation.performance?.starts_at) }}</div>
            <div v-if="reservation.performance?.label" class="small text-muted">
              {{ reservation.performance.label }}
            </div>
          </div>
          <div class="col-5" v-if="reservation.performance?.venue_name">
            <div class="small text-muted">会場</div>
            <div class="fw-bold small">{{ reservation.performance.venue_name }}</div>
          </div>
        </div>

        <div class="row g-3 mb-3">
          <div class="col-6">
            <div class="small text-muted">席種</div>
            <div class="fw-bold">{{ reservation.seat_tier?.name || '未選択' }}</div>
          </div>
          <div class="col-3">
            <div class="small text-muted">枚数</div>
            <div class="fw-bold">{{ reservation.quantity }}枚</div>
          </div>
          <div class="col-3">
            <div class="small text-muted">支払</div>
            <div class="fw-bold small">
              {{ reservation.reservation_type === 'invite'
                ? 'ご招待'
                : (payLabel[reservation.payment_status] || typeLabel[reservation.reservation_type] || '当日精算') }}
            </div>
          </div>
        </div>

        <div class="row g-3 mb-3">
          <div class="col-6">
            <div class="small text-muted">区分</div>
            <div class="fw-bold small">
              {{ reservation.sales_channel_display || channelLabel[reservation.sales_channel] || '—' }}
            </div>
          </div>
          <div class="col-6">
            <div class="small text-muted">種別</div>
            <div class="fw-bold small">{{ typeLabel[reservation.reservation_type] || '—' }}</div>
          </div>
        </div>
      </div>

      <div class="position-relative" style="height: 1px;">
        <div style="border-top: 2px dashed var(--mogi-border, #dee2e6); position: absolute; left: 20px; right: 20px; top: 0;"></div>
      </div>

      <div class="card-body pt-3">
        <div class="fw-bold mb-1">{{ reservation.guest_name }}</div>
        <div v-if="reservation.guest_email" class="small text-muted">{{ reservation.guest_email }}</div>
        <div v-if="reservation.guest_phone" class="small text-muted">{{ reservation.guest_phone }}</div>
        <div v-if="reservation.memo" class="mt-2 small" style="white-space: pre-line">
          <div class="text-muted">メモ</div>
          {{ reservation.memo }}
        </div>
        <div v-if="reservation.token" class="small text-muted mt-2">
          予約番号：<span class="font-monospace">{{ reservation.token }}</span>
        </div>
      </div>

      <div class="card-body pt-0 d-flex gap-2 justify-content-end align-items-center">
        <span v-if="copied" class="small text-success me-auto">コピーしました</span>
        <button type="button" class="btn btn-sm btn-outline-secondary" @click="emit('close')">閉じる</button>
        <button type="button" class="btn btn-sm btn-primary" @click="onCopy">共有用テキストをコピー</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-backdrop-custom {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 1050;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 2rem 1rem;
  overflow-y: auto;
}
.modal-panel {
  width: 100%;
  max-width: 560px;
  background: #fff;
}
</style>
