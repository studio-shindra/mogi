<script setup>
import { computed } from 'vue'

const props = defineProps({
  summaries: { type: Array, required: true },
})

const totals = computed(() => {
  return props.summaries.reduce(
    (acc, s) => {
      acc.count += s.count || 0
      acc.quantity += s.quantity || 0
      acc.checkedIn += s.checked_in || 0
      acc.revenueEstimate += s.revenue_estimate || 0
      return acc
    },
    { count: 0, quantity: 0, checkedIn: 0, revenueEstimate: 0 },
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
        <span class="text-muted">予約件数</span>
        <span>{{ totals.count }}</span>
      </div>
      <div class="d-flex justify-content-between small">
        <span class="text-muted">総枚数</span>
        <span>{{ totals.quantity }}</span>
      </div>
      <div class="d-flex justify-content-between small">
        <span class="text-muted">入場済</span>
        <span>{{ totals.checkedIn }}</span>
      </div>
      <div class="d-flex justify-content-between align-items-baseline mt-2 border-top pt-2">
        <span class="fw-bold">売上概算</span>
        <span class="fw-bold text-primary">¥{{ totals.revenueEstimate.toLocaleString() }}</span>
      </div>
    </div>
  </div>
</template>
