<script setup>
import { ref } from 'vue'

const props = defineProps({
  application: { type: Object, required: true },
})

const emit = defineEmits(['confirm', 'reject'])

const acting = ref(false)

async function onConfirm() {
  const name = props.application.guest_name
  if (!window.confirm(`${name} さんを当選処理（予約確定）しますか？\n在庫が不足している場合は失敗します。`)) return
  acting.value = true
  emit('confirm', props.application)
  setTimeout(() => (acting.value = false), 500)
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
      <button
        class="btn btn-sm btn-success me-1"
        :disabled="acting"
        @click="onConfirm"
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
    </td>
  </tr>
</template>
