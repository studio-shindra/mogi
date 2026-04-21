<script setup>
import { computed } from 'vue'
import { IconChevronRight } from '@tabler/icons-vue'
import { formatJstTime } from '../../utils/datetime.js'

const props = defineProps({
  performance: { type: Object, required: true },
  slug: { type: String, required: true },
})

const totalRemaining = computed(() =>
  props.performance.seat_tiers.reduce((sum, t) => sum + (t.remaining ?? t.capacity), 0)
)

const totalCapacity = computed(() =>
  props.performance.seat_tiers.reduce((sum, t) => sum + t.capacity, 0)
)

const availabilityLabel = computed(() => {
  if (totalRemaining.value === 0) return { text: '完売', cls: 'status-soldout' }
  if (totalRemaining.value <= totalCapacity.value * 0.2) return { text: '残りわずか', cls: 'status-few' }
  return { text: '予約受付中', cls: 'status-available' }
})
</script>

<template>
  <RouterLink
    :to="{ name: 'reserve', params: { slug, performanceId: performance.id } }"
    class="card text-decoration-none text-body mb-2"
  >
    <div class="card-body d-flex justify-content-between align-items-center py-3">
      <div>
        <div class="fw-bold">{{ performance.label }}</div>
        <small class="text-muted">
          開場 {{ formatJstTime(performance.open_at) }} /
          開演 {{ formatJstTime(performance.starts_at) }}
        </small>
      </div>
      <div class="d-flex align-items-center gap-2">
        <span :class="availabilityLabel.cls">{{ availabilityLabel.text }}</span>
        <IconChevronRight :size="18" class="text-muted" />
      </div>
    </div>
  </RouterLink>
</template>
