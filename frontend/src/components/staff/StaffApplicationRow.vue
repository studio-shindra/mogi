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
      {{ application.seat_tier?.name }}
      <span class="text-muted">× {{ application.quantity }}</span>
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
