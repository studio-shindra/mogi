<script setup>
import { SALES_CHANNELS } from '../../composables/useStaffActions.js'

defineProps({
  searchQuery: { type: String, default: '' },
  selectedPerformanceId: { type: Number, default: null },
  selectedSalesChannel: { type: String, default: '' },
  performances: { type: Array, default: () => [] },
})

const emit = defineEmits([
  'update:searchQuery',
  'update:selectedPerformanceId',
  'update:selectedSalesChannel',
  'search',
])

function handleSubmit() {
  emit('search')
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="row g-2 mb-3">
    <!-- 公演フィルタ -->
    <div class="col-6 col-md-3">
      <select
        class="form-select"
        :value="selectedPerformanceId"
        @change="emit('update:selectedPerformanceId', Number($event.target.value) || null)"
      >
        <option :value="null">全公演</option>
        <option v-for="p in performances" :key="p.id" :value="p.id">
          {{ p.label }}
        </option>
      </select>
    </div>
    <!-- 販売区分フィルタ -->
    <div class="col-6 col-md-2">
      <select
        class="form-select"
        :value="selectedSalesChannel"
        @change="emit('update:selectedSalesChannel', $event.target.value)"
      >
        <option value="">全区分</option>
        <option v-for="ch in SALES_CHANNELS" :key="ch.value" :value="ch.value">
          {{ ch.label }}
        </option>
      </select>
    </div>
    <!-- テキスト検索 -->
    <div class="col">
      <input
        type="text"
        class="form-control"
        placeholder="名前 / メール / 電話 / トークン"
        :value="searchQuery"
        @input="emit('update:searchQuery', $event.target.value)"
      />
    </div>
    <!-- 検索ボタン -->
    <div class="col-auto">
      <button type="submit" class="btn btn-dark">検索</button>
    </div>
  </form>
</template>
