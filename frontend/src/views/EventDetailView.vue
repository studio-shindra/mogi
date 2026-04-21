<script setup>
import { ref, onMounted } from 'vue'
import { fetchEventDetail } from '../api/events.js'
import { IconMapPin, IconUser } from '@tabler/icons-vue'
import PerformanceCard from '../components/event/PerformanceCard.vue'

const props = defineProps({ slug: String })

const event = ref(null)
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    event.value = await fetchEventDetail(props.slug)
  } catch (e) {
    error.value = 'データの取得に失敗しました'
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div style="max-width: 640px; margin: 0 auto">
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-mogi" role="status" />
    </div>

    <div v-else-if="error" class="container py-5">
      <div class="alert alert-danger">{{ error }}</div>
    </div>

    <template v-else-if="event">
      <!-- フライヤー画像 -->
      <div v-if="event.flyer_image_url" class="mb-0">
        <img
          :src="event.flyer_image_url"
          :alt="event.title"
          class="w-100 d-block"
          style="object-fit: contain"
        />
      </div>

      <div class="container py-4" style="padding-top: 24px !important">
        <!-- タイトル -->
        <h1 class="fs-3 fw-bold mb-3" :style="event.flyer_image_url ? '' : 'padding-top: 32px'">
          {{ event.title }}
        </h1>

        <!-- 説明 -->
        <p class="mb-4" style="white-space: pre-line; color: var(--mogi-text-muted)">
          {{ event.description }}
        </p>

        <!-- 会場・出演 -->
        <div class="d-flex flex-column gap-2 mb-4">
          <div v-if="event.venue_name" class="d-flex align-items-start gap-2">
            <IconMapPin :size="18" class="text-mogi mt-1 flex-shrink-0" />
            <div>
              <div class="fw-bold small">{{ event.venue_name }}</div>
              <div class="text-muted small">{{ event.venue_address }}</div>
            </div>
          </div>
          <div v-if="event.cast" class="d-flex align-items-start gap-2">
            <IconUser :size="18" class="text-mogi mt-1 flex-shrink-0" />
            <div class="fw-bold small" style="white-space: pre-line">{{ event.cast }}</div>
          </div>
        </div>

        <!-- 公演一覧 -->
        <h2 class="fs-6 text-muted text-uppercase mb-3" style="letter-spacing: 0.1em">Schedule</h2>
        <div v-if="event.public_entry_enabled">
          <PerformanceCard
            v-for="perf in event.performances"
            :key="perf.id"
            :performance="perf"
            :slug="event.slug"
          />
        </div>
        <div v-else class="alert alert-secondary small text-center mb-0">
          現在この受付は公開されていません
        </div>
      </div>
    </template>
  </div>
</template>
