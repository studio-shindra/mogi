<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: { type: String, required: true },
  paymentStatus: { type: String, required: true },
  checkedIn: { type: Boolean, default: false },
})

const badges = computed(() => {
  const list = []

  const statusMap = {
    draft: { label: '仮受付', cls: 'bg-info text-dark' },
    pending: { label: '仮予約', cls: 'bg-warning text-dark' },
    confirmed: { label: '確定', cls: 'bg-success' },
    cancelled: { label: 'キャンセル', cls: 'bg-secondary' },
  }
  const s = statusMap[props.status]
  if (s) list.push(s)

  const payMap = {
    unpaid: { label: '未払い', cls: 'bg-danger' },
    paid: { label: '支払済', cls: 'bg-mogi' },
    refunded: { label: '返金済', cls: 'bg-secondary' },
  }
  const p = payMap[props.paymentStatus]
  if (p) list.push(p)

  if (props.checkedIn) {
    list.push({ label: '入場済', cls: 'bg-info text-dark' })
  }

  return list
})
</script>

<template>
  <span
    v-for="(b, i) in badges"
    :key="i"
    class="badge rounded-pill me-1"
    :class="b.cls"
  >
    {{ b.label }}
  </span>
</template>
