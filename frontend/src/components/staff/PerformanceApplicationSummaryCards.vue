<script setup>
import { computed } from 'vue'

const props = defineProps({
  summaries: { type: Array, required: true },
})

function formatDateTime(iso) {
  const d = new Date(iso)
  const m = d.getMonth() + 1
  const day = d.getDate()
  const hh = String(d.getHours()).padStart(2, '0')
  const mm = String(d.getMinutes()).padStart(2, '0')
  return `${m}/${day} ${hh}:${mm}`
}

function isFinished(iso) {
  return new Date(iso).getTime() < Date.now()
}

// 並び: 未終演（starts_at 昇順） → 終演済み（starts_at 昇順）
const sortedSummaries = computed(() => {
  const arr = [...props.summaries]
  arr.sort((a, b) => {
    const aFin = isFinished(a.starts_at)
    const bFin = isFinished(b.starts_at)
    if (aFin !== bFin) return aFin ? 1 : -1
    return new Date(a.starts_at) - new Date(b.starts_at)
  })
  return arr
})
</script>

<template>
  <div v-if="summaries.length" class="d-flex gap-2 overflow-auto pb-2 mb-3">
    <slot name="leading" />
    <div
      v-for="s in sortedSummaries"
      :key="s.performance_id"
      class="card flex-shrink-0 border"
      :class="{ 'opacity-50 bg-light': isFinished(s.starts_at) }"
      style="min-width: 180px;"
    >
      <div class="card-body p-2">
        <div class="fw-bold small">{{ formatDateTime(s.starts_at) }}</div>
        <div class="text-muted" style="font-size: 0.75rem;">{{ s.label }}</div>
        <hr class="my-2" />
        <div class="d-flex justify-content-between small">
          <span class="text-muted">応募人数</span>
          <span>{{ s.application_count ?? 0 }}</span>
        </div>
        <div class="d-flex justify-content-between align-items-baseline mt-2 border-top pt-2">
          <span class="fw-bold">合計枚数</span>
          <span class="fw-bold fs-4 text-primary">{{ s.application_quantity ?? 0 }}</span>
        </div>
      </div>
    </div>
  </div>
</template>
