<script setup>
import { ref, onMounted } from 'vue'
import { fetchEvents } from '../api/events.js'
import { IconChevronRight } from '@tabler/icons-vue'

const events = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    events.value = await fetchEvents()
  } catch (e) {
    // empty
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="container py-5" style="max-width: 640px; padding-top: 56px">
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-mogi" role="status" />
    </div>

    <div v-else-if="events.length === 0" class="text-center py-5 text-muted">
      現在公開中の公演はありません
    </div>

    <div v-else class="d-flex flex-column gap-3">
      <RouterLink
        v-for="event in events"
        :key="event.id"
        :to="{ name: 'event-detail', params: { slug: event.slug } }"
        class="card overflow-hidden text-decoration-none text-body"
      >
        <!-- フライヤー画像 -->
        <div v-if="event.flyer_image_url">
          <img
            :src="event.flyer_image_url"
            :alt="event.title"
            class="w-100 d-block"
            style="object-fit: cover; max-height: 280px"
          />
        </div>
        <!-- タイトル -->
        <div class="card-body d-flex justify-content-between align-items-center py-3">
          <span class="fw-bold">{{ event.title }}</span>
          <IconChevronRight :size="18" class="text-mogi flex-shrink-0" />
        </div>
      </RouterLink>
    </div>
  </div>
</template>
