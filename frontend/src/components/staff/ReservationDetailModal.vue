<script setup>
import { computed, reactive, ref, watch } from 'vue'
import ReservationStatusBadge from '../reservation/ReservationStatusBadge.vue'
import { formatJstDateTime } from '../../utils/datetime.js'
import { SALES_CHANNELS } from '../../composables/useStaffActions.js'

const props = defineProps({
  reservation: { type: Object, default: null },
  performances: { type: Array, default: () => [] },
  getSeatTiersFor: { type: Function, default: () => () => [] },
})

const emit = defineEmits(['close', 'save'])

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

const RESERVATION_TYPES = [
  { value: 'card', label: 'カード' },
  { value: 'cash', label: '当日精算' },
  { value: 'invite', label: 'ご招待' },
]

const copied = ref(false)
const editMode = ref(false)
const saving = ref(false)
const form = reactive({
  performance_id: null,
  seat_tier_id: null,
  quantity: 1,
  sales_channel: '',
  reservation_type: '',
  guest_name: '',
  guest_email: '',
  guest_phone: '',
  memo: '',
})

const canEdit = computed(() => {
  const r = props.reservation
  if (!r) return false
  if (r.checked_in) return false
  if (r.status === 'cancelled') return false
  return true
})

const seatTierOptions = computed(() => {
  return props.getSeatTiersFor(form.performance_id) || []
})

function resetForm() {
  const r = props.reservation
  if (!r) return
  form.performance_id = r.performance?.id ?? null
  form.seat_tier_id = r.seat_tier?.id ?? null
  form.quantity = r.quantity ?? 1
  form.sales_channel = r.sales_channel ?? ''
  form.reservation_type = r.reservation_type ?? ''
  form.guest_name = r.guest_name ?? ''
  form.guest_email = r.guest_email ?? ''
  form.guest_phone = r.guest_phone ?? ''
  form.memo = r.memo ?? ''
}

function startEdit() {
  resetForm()
  editMode.value = true
}

function cancelEdit() {
  editMode.value = false
  resetForm()
}

function onPerformanceChange() {
  // 公演を変えたら席種選択肢が変わるので、現在の選択が無ければクリア
  const tiers = props.getSeatTiersFor(form.performance_id) || []
  if (!tiers.some((t) => t.id === form.seat_tier_id)) {
    form.seat_tier_id = tiers[0]?.id ?? null
  }
}

async function onSave() {
  const r = props.reservation
  if (!r) return

  const payload = {}
  if (form.performance_id !== (r.performance?.id ?? null)) {
    payload.performance_id = form.performance_id
  }
  if (form.seat_tier_id !== (r.seat_tier?.id ?? null)) {
    payload.seat_tier_id = form.seat_tier_id
  }
  if (form.quantity !== r.quantity) payload.quantity = form.quantity
  if (form.sales_channel !== (r.sales_channel ?? '')) payload.sales_channel = form.sales_channel
  if (form.reservation_type !== (r.reservation_type ?? '')) payload.reservation_type = form.reservation_type
  if (form.guest_name !== (r.guest_name ?? '')) payload.guest_name = form.guest_name
  if (form.guest_email !== (r.guest_email ?? '')) payload.guest_email = form.guest_email
  if (form.guest_phone !== (r.guest_phone ?? '')) payload.guest_phone = form.guest_phone
  if (form.memo !== (r.memo ?? '')) payload.memo = form.memo

  if (Object.keys(payload).length === 0) {
    editMode.value = false
    return
  }

  saving.value = true
  try {
    await emit('save', { reservation: r, payload })
    editMode.value = false
  } finally {
    saving.value = false
  }
}

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

watch(() => props.reservation, () => {
  copied.value = false
  editMode.value = false
  resetForm()
})
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
          <h5 class="fw-bold mb-0">{{ editMode ? '予約編集' : '予約詳細' }}</h5>
          <ReservationStatusBadge
            :status="reservation.status"
            :payment-status="reservation.payment_status"
            :checked-in="reservation.checked_in"
          />
        </div>
      </div>

      <!-- 表示モード -->
      <template v-if="!editMode">
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

        <div class="card-body pt-0 d-flex gap-2 justify-content-end align-items-center flex-wrap">
          <span v-if="copied" class="small text-success me-auto">コピーしました</span>
          <button type="button" class="btn btn-sm btn-outline-secondary" @click="emit('close')">閉じる</button>
          <button
            v-if="canEdit"
            type="button"
            class="btn btn-sm btn-outline-primary"
            @click="startEdit"
          >編集</button>
          <button type="button" class="btn btn-sm btn-primary" @click="onCopy">共有用テキストをコピー</button>
        </div>
      </template>

      <!-- 編集モード -->
      <template v-else>
        <div class="card-body pt-0">
          <div class="mb-3">
            <label class="form-label small text-muted mb-1">公演</label>
            <select v-model.number="form.performance_id" class="form-select form-select-sm" @change="onPerformanceChange">
              <option v-for="p in performances" :key="p.id" :value="p.id">
                {{ formatJstDateTime(p.starts_at) }}{{ p.label ? `（${p.label}）` : '' }}
              </option>
            </select>
          </div>

          <div class="row g-3 mb-3">
            <div class="col-8">
              <label class="form-label small text-muted mb-1">席種</label>
              <select v-model.number="form.seat_tier_id" class="form-select form-select-sm">
                <option :value="null">未選択</option>
                <option v-for="t in seatTierOptions" :key="t.id" :value="t.id">
                  {{ t.name }}<span v-if="typeof t.remaining === 'number'">（残{{ t.remaining }}）</span>
                </option>
              </select>
            </div>
            <div class="col-4">
              <label class="form-label small text-muted mb-1">枚数</label>
              <input v-model.number="form.quantity" type="number" min="1" max="10" class="form-control form-control-sm" />
            </div>
          </div>

          <div class="row g-3 mb-3">
            <div class="col-6">
              <label class="form-label small text-muted mb-1">区分</label>
              <select v-model="form.sales_channel" class="form-select form-select-sm">
                <option v-for="c in SALES_CHANNELS" :key="c.value" :value="c.value">{{ c.label }}</option>
              </select>
            </div>
            <div class="col-6">
              <label class="form-label small text-muted mb-1">種別</label>
              <select v-model="form.reservation_type" class="form-select form-select-sm">
                <option v-for="t in RESERVATION_TYPES" :key="t.value" :value="t.value">{{ t.label }}</option>
              </select>
            </div>
          </div>

          <div class="mb-3">
            <label class="form-label small text-muted mb-1">氏名</label>
            <input v-model="form.guest_name" type="text" class="form-control form-control-sm" />
          </div>

          <div class="row g-3 mb-3">
            <div class="col-7">
              <label class="form-label small text-muted mb-1">メール</label>
              <input v-model="form.guest_email" type="email" class="form-control form-control-sm" />
            </div>
            <div class="col-5">
              <label class="form-label small text-muted mb-1">電話</label>
              <input v-model="form.guest_phone" type="text" class="form-control form-control-sm" />
            </div>
          </div>

          <div class="mb-3">
            <label class="form-label small text-muted mb-1">メモ</label>
            <textarea v-model="form.memo" rows="2" class="form-control form-control-sm"></textarea>
          </div>
        </div>

        <div class="card-body pt-0 d-flex gap-2 justify-content-end">
          <button type="button" class="btn btn-sm btn-outline-secondary" :disabled="saving" @click="cancelEdit">キャンセル</button>
          <button type="button" class="btn btn-sm btn-primary" :disabled="saving" @click="onSave">
            {{ saving ? '保存中…' : '保存' }}
          </button>
        </div>
      </template>
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
