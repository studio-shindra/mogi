<script setup>
import { computed } from 'vue'
import { IconArmchair } from '@tabler/icons-vue'

const props = defineProps({
  seatTiers: { type: Array, required: true },
  selectedTier: { type: Object, default: null },
  quantity: { type: Number, default: 1 },
  reservationType: { type: String, default: 'card' },
})

const emit = defineEmits([
  'update:selectedTier',
  'update:quantity',
  'update:reservationType',
])

function price(tier) {
  return props.reservationType === 'cash' ? tier.price_cash : tier.price_card
}

const maxQuantity = computed(() => {
  if (!props.selectedTier) return 1
  return Math.min(props.selectedTier.remaining ?? props.selectedTier.capacity, 10)
})

function tierAvailability(tier) {
  const r = tier.remaining ?? tier.capacity
  if (r === 0) return { text: '完売', available: false }
  return { text: '', available: true }
}
</script>

<template>
  <!-- 支払い方法 -->
  <div class="mb-4">
    <label class="form-label small text-muted">お支払い方法</label>
    <div class="d-flex gap-2">
      <button
        type="button"
        class="btn flex-fill"
        :class="reservationType === 'card' ? 'btn-primary' : 'btn-outline-secondary'"
        @click="emit('update:reservationType', 'card')"
      >
        カード決済
      </button>
      <button
        type="button"
        class="btn flex-fill"
        :class="reservationType === 'cash' ? 'btn-primary' : 'btn-outline-secondary'"
        @click="emit('update:reservationType', 'cash')"
      >
        当日現金払い
      </button>
    </div>
  </div>

  <!-- 席種 -->
  <div class="mb-4">
    <label class="form-label small text-muted">席種を選択</label>
    <div class="d-flex flex-column gap-2">
      <button
        v-for="tier in seatTiers"
        :key="tier.id"
        type="button"
        class="card text-start border"
        :class="{
          'border-2': selectedTier?.id === tier.id,
          'bg-mogi-light': selectedTier?.id === tier.id,
        }"
        :style="selectedTier?.id === tier.id ? 'border-color: var(--mogi-orange) !important' : ''"
        :disabled="!tierAvailability(tier).available"
        @click="emit('update:selectedTier', tier)"
      >
        <div class="card-body py-3 d-flex justify-content-between align-items-center">
          <div class="d-flex align-items-center gap-2">
            <IconArmchair :size="20" class="text-mogi" />
            <div>
              <div class="fw-bold">{{ tier.name }}</div>
              <div v-if="!tierAvailability(tier).available" class="text-muted small">完売</div>
            </div>
          </div>
          <div class="fw-bold">
            {{ price(tier).toLocaleString() }}<small class="text-muted fw-normal">円</small>
          </div>
        </div>
      </button>
    </div>
  </div>

  <!-- 枚数 -->
  <div v-if="selectedTier" class="mb-4">
    <label class="form-label small text-muted">枚数</label>
    <div class="d-flex gap-2">
      <button
        v-for="n in maxQuantity"
        :key="n"
        type="button"
        class="btn"
        :class="quantity === n ? 'btn-primary' : 'btn-outline-secondary'"
        style="min-width: 48px"
        @click="emit('update:quantity', n)"
      >
        {{ n }}
      </button>
    </div>
  </div>
</template>
