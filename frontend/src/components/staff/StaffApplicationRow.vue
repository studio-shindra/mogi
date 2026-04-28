<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  application: { type: Object, required: true },
  seatTiers: { type: Array, default: () => [] },
})

const emit = defineEmits(['confirm', 'reject'])

const acting = ref(false)
const choosing = ref(false)
const selectedSeatTierId = ref(null)

const sortedSeatTiers = computed(() => {
  return [...props.seatTiers].sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0))
})

function pickInitialSeatTierId() {
  const first = props.application.first_choice_seat_tier
  const second = props.application.second_choice_seat_tier
  const exists = (id) => id && props.seatTiers.some((t) => t.id === id)
  if (exists(first?.id)) return first.id
  if (exists(second?.id)) return second.id
  return null
}

function startConfirm() {
  selectedSeatTierId.value = pickInitialSeatTierId()
  choosing.value = true
}

function cancelConfirm() {
  choosing.value = false
  selectedSeatTierId.value = null
}

async function submitConfirm() {
  if (!selectedSeatTierId.value) return
  acting.value = true
  emit('confirm', props.application, selectedSeatTierId.value)
  setTimeout(() => {
    acting.value = false
    choosing.value = false
    selectedSeatTierId.value = null
  }, 500)
}

async function onReject() {
  const name = props.application.guest_name
  if (!window.confirm(`${name} さんを落選処理しますか？`)) return
  acting.value = true
  emit('reject', props.application)
  setTimeout(() => (acting.value = false), 500)
}
</script>

<template>
  <tr>
    <td>
      <div class="fw-bold">
        {{ application.guest_name }}
        <span
          v-if="application.is_fanclub_member"
          class="badge bg-mogi ms-1"
          title="ファンクラブ会員"
        >FC</span>
      </div>
      <small class="text-muted">{{ application.guest_phone }}</small>
      <small v-if="application.guest_email" class="text-muted d-block">{{ application.guest_email }}</small>
    </td>
    <td>
      <div>
        <span class="text-muted small">第一希望:</span>
        <span class="fw-bold ms-1">{{ application.first_choice_seat_tier?.name || '—' }}</span>
        <span class="text-muted ms-1">× {{ application.quantity }}</span>
      </div>
      <div>
        <span class="text-muted small">第二希望:</span>
        <span class="ms-1">{{ application.second_choice_seat_tier?.name || '—' }}</span>
      </div>
      <div v-if="application.allow_any_seat">
        <span class="badge bg-mogi-light text-mogi border">席不問 可</span>
      </div>
    </td>
    <td>
      <small class="text-muted">{{ application.performance?.label }}</small>
    </td>
    <td>
      <small class="text-muted" style="white-space: pre-line">{{ application.memo }}</small>
    </td>
    <td class="text-end text-nowrap">
      <template v-if="!choosing">
        <button
          class="btn btn-sm btn-success me-1"
          :disabled="acting"
          @click="startConfirm"
        >
          当選
        </button>
        <button
          class="btn btn-sm btn-outline-danger"
          :disabled="acting"
          @click="onReject"
        >
          落選
        </button>
      </template>
      <template v-else>
        <div class="d-flex align-items-center justify-content-end gap-1">
          <select
            v-model="selectedSeatTierId"
            class="form-select form-select-sm"
            style="width: auto; min-width: 9rem"
            :disabled="acting"
          >
            <option :value="null" disabled>席種を選択</option>
            <option
              v-for="t in sortedSeatTiers"
              :key="t.id"
              :value="t.id"
              :disabled="(t.remaining ?? 0) <= 0"
            >
              {{ t.name }}（残{{ t.remaining ?? 0 }}）
            </option>
          </select>
          <button
            class="btn btn-sm btn-success"
            :disabled="acting || !selectedSeatTierId"
            @click="submitConfirm"
          >
            確定
          </button>
          <button
            class="btn btn-sm btn-outline-secondary"
            :disabled="acting"
            @click="cancelConfirm"
          >
            キャンセル
          </button>
        </div>
      </template>
    </td>
  </tr>
</template>
