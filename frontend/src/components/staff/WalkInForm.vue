<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  performances: { type: Array, default: () => [] },
})

const emit = defineEmits(['created'])

const selectedPerfId = ref(props.performances[0]?.id ?? null)

watch(() => props.performances, (perfs) => {
  if (perfs.length && !selectedPerfId.value) {
    selectedPerfId.value = perfs[0].id
  }
})

const selectedPerf = computed(() =>
  props.performances.find((p) => p.id === selectedPerfId.value),
)

const seatTiers = computed(() => selectedPerf.value?.seat_tiers ?? [])

const selectedTierId = ref(null)
const selectedTier = computed(() =>
  seatTiers.value.find((t) => t.id === selectedTierId.value),
)

const quantity = ref(1)
const guestName = ref('')
const guestPhone = ref('')
const memo = ref('')
const submitting = ref(false)

const canSubmit = computed(() => guestName.value.trim() && selectedTierId.value)

async function handleSubmit() {
  if (!canSubmit.value || submitting.value) return
  submitting.value = true

  emit('created', {
    performanceId: selectedPerfId.value,
    seatTierId: selectedTierId.value,
    tierName: selectedTier.value?.name ?? '',
    tierCode: selectedTier.value?.code ?? '',
    quantity: quantity.value,
    guestName: guestName.value.trim(),
    guestPhone: guestPhone.value.trim(),
    memo: memo.value.trim(),
  })

  // リセット
  guestName.value = ''
  guestPhone.value = ''
  memo.value = ''
  quantity.value = 1
  submitting.value = false
}
</script>

<template>
  <form @submit.prevent="handleSubmit">
    <div class="row g-2 mb-2">
      <!-- 公演 -->
      <div class="col-md-6">
        <label class="form-label small fw-bold">公演</label>
        <select class="form-select form-select-sm" v-model="selectedPerfId">
          <option v-for="p in props.performances" :key="p.id" :value="p.id">
            {{ p.label }}
          </option>
        </select>
      </div>
      <!-- 席種 -->
      <div class="col-md-3">
        <label class="form-label small fw-bold">席種</label>
        <select class="form-select form-select-sm" v-model="selectedTierId">
          <option :value="null" disabled>選択</option>
          <option v-for="t in seatTiers" :key="t.id" :value="t.id">
            {{ t.name }} ({{ t.price_cash.toLocaleString() }}円)
          </option>
        </select>
      </div>
      <!-- 枚数 -->
      <div class="col-md-3">
        <label class="form-label small fw-bold">枚数</label>
        <select class="form-select form-select-sm" v-model.number="quantity">
          <option v-for="n in 4" :key="n" :value="n">{{ n }}</option>
        </select>
      </div>
    </div>
    <div class="row g-2 mb-2">
      <!-- 名前 -->
      <div class="col-md-4">
        <input
          type="text"
          class="form-control form-control-sm"
          placeholder="お名前 *"
          v-model="guestName"
        />
      </div>
      <!-- 電話 -->
      <div class="col-md-4">
        <input
          type="tel"
          class="form-control form-control-sm"
          placeholder="電話番号"
          v-model="guestPhone"
        />
      </div>
      <!-- メモ -->
      <div class="col-md-4">
        <input
          type="text"
          class="form-control form-control-sm"
          placeholder="メモ"
          v-model="memo"
        />
      </div>
    </div>
    <button
      type="submit"
      class="btn btn-sm btn-dark"
      :disabled="!canSubmit || submitting"
    >
      当日券を登録
    </button>
  </form>
</template>
