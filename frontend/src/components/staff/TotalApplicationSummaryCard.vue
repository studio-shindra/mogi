<script setup>
import { computed } from 'vue'

const props = defineProps({
  summaries: { type: Array, required: true },
})

const totals = computed(() => {
  return props.summaries.reduce(
    (acc, s) => {
      acc.count += s.application_count || 0
      acc.quantity += s.application_quantity || 0
      return acc
    },
    { count: 0, quantity: 0 },
  )
})
</script>

<template>
  <div
    class="card flex-shrink-0 border-primary bg-primary bg-opacity-10"
    style="min-width: 180px;"
  >
    <div class="card-body p-2">
      <div class="fw-bold small text-primary">全公演 合計</div>
      <div class="text-muted" style="font-size: 0.75rem;">&nbsp;</div>
      <hr class="my-2" />
      <div class="d-flex justify-content-between small">
        <span class="text-muted">応募人数</span>
        <span>{{ totals.count }}</span>
      </div>
      <div class="d-flex justify-content-between align-items-baseline mt-2 border-top pt-2">
        <span class="fw-bold">合計枚数</span>
        <span class="fw-bold fs-4 text-primary">{{ totals.quantity }}</span>
      </div>
    </div>
  </div>
</template>
