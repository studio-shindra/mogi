<script setup>
defineProps({
  searchQuery: { type: String, default: '' },
  selectedPerformanceId: { type: Number, default: null },
  performances: { type: Array, default: () => [] },
})

const emit = defineEmits([
  'update:searchQuery',
  'update:selectedPerformanceId',
  'search',
])

function handleSubmit() {
  emit('search')
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="row g-2 mb-3">
    <!-- 公演フィルタ -->
    <div class="col-12 col-md-4">
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
