<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { fetchEventDetail } from '../api/events.js'
import { createReservation } from '../api/reservations.js'
import { useReservationForm } from '../composables/useReservationForm.js'
import SeatTierSelector from '../components/event/SeatTierSelector.vue'
import GuestInfoForm from '../components/reservation/GuestInfoForm.vue'
import ReservationSummary from '../components/reservation/ReservationSummary.vue'

const props = defineProps({ slug: String, performanceId: String })
const router = useRouter()

const loading = ref(true)
const eventTitle = ref('')
const submitError = ref('')

const form = useReservationForm()

onMounted(async () => {
  try {
    const event = await fetchEventDetail(props.slug)
    const perf = event.performances.find(
      (p) => p.id === Number(props.performanceId),
    )
    if (perf) {
      form.performance.value = perf
      eventTitle.value = event.title
    }
  } catch (e) {
    // エラー時は performance が null のまま → テンプレートで「公演が見つかりません」表示
  } finally {
    loading.value = false
  }
})

async function handleSubmit() {
  submitError.value = ''
  try {
    const result = await createReservation({
      performance_id: form.performance.value.id,
      seat_tier_id: form.selectedTier.value.id,
      quantity: form.quantity.value,
      reservation_type: form.reservationType.value,
      guest_name: form.guestName.value,
      guest_email: form.guestEmail.value,
      guest_phone: form.guestPhone.value,
    })

    router.push({ name: 'reservation-confirm', params: { token: result.token } })
  } catch (e) {
    const data = e.response?.data
    if (data) {
      // バリデーションエラーを表示
      const messages = Object.values(data).flat()
      submitError.value = messages.join(' / ')
    } else {
      submitError.value = '予約の送信に失敗しました'
    }
  }
}
</script>

<template>
  <div class="container py-5" style="max-width: 640px; padding-top: 56px">
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-mogi" role="status" />
    </div>

    <template v-else-if="form.performance.value">
      <!-- 戻るリンク -->
      <RouterLink
        :to="{ name: 'event-detail', params: { slug } }"
        class="d-inline-flex align-items-center gap-1 text-decoration-none text-muted small mb-3"
      >
        &larr; {{ eventTitle }}
      </RouterLink>

      <h2 class="fs-5 fw-bold mb-1">{{ form.performance.value.label }}</h2>
      <p class="small text-muted mb-4">
        開場 {{ form.performance.value.open_at.slice(11, 16) }}
        / 開演 {{ form.performance.value.starts_at.slice(11, 16) }}
      </p>

      <!-- ステップインジケーター -->
      <!-- ステップ 1 / 3 -->
      <div class="d-flex mb-4 gap-1">
        <button
          v-for="s in 3"
          :key="s"
          type="button"
          class="btn flex-fill small py-2 rounded-pill"
          :class="
            form.step.value === s
              ? 'bg-mogi-light text-mogi fw-bold'
              : s < form.step.value
                ? 'btn-link text-mogi text-decoration-none'
                : 'text-muted'
          "
          :style="form.step.value === s ? 'border: 1px solid var(--mogi-orange)' : 'border: 1px solid transparent'"
          :disabled="s > form.step.value"
          @click="s < form.step.value && (form.step.value = s)"
        >
          {{ s }}. {{ ['席種選択', 'お客様情報', '確認'][s - 1] }}
        </button>
      </div>

      <!-- ===== Step 1 ===== -->
      <template v-if="form.step.value === 1">
        <SeatTierSelector
          :seat-tiers="form.performance.value.seat_tiers"
          :selected-tier="form.selectedTier.value"
          :quantity="form.quantity.value"
          @update:selected-tier="form.selectTier"
          @update:quantity="(v) => (form.quantity.value = v)"
        />

        <div v-if="form.selectedTier.value" class="card bg-mogi-light mb-4">
          <div class="card-body d-flex justify-content-between align-items-center py-3">
            <div>
              <span class="fw-bold">{{ form.selectedTier.value.name }}</span>
              <span class="text-muted ms-2">× {{ form.quantity.value }}枚</span>
            </div>
            <span class="fs-5 fw-bold text-mogi">
              {{ form.totalPrice.value.toLocaleString() }}<small class="text-muted fw-normal">円</small>
            </span>
          </div>
        </div>

        <button
          class="btn btn-primary w-100 py-3"
          :disabled="!form.canProceedStep1.value"
          @click="form.nextStep()"
        >
          次へ
        </button>
      </template>

      <!-- ===== Step 2 ===== -->
      <template v-else-if="form.step.value === 2">
        <GuestInfoForm
          :guest-name="form.guestName.value"
          :guest-email="form.guestEmail.value"
          :guest-phone="form.guestPhone.value"
          :email-required="false"
          @update:guest-name="(v) => (form.guestName.value = v)"
          @update:guest-email="(v) => (form.guestEmail.value = v)"
          @update:guest-phone="(v) => (form.guestPhone.value = v)"
        />

        <div class="d-flex gap-2">
          <button class="btn btn-outline-secondary flex-fill py-3" @click="form.prevStep()">
            戻る
          </button>
          <button
            class="btn btn-primary flex-fill py-3"
            :disabled="!form.canProceedStep2.value"
            @click="form.nextStep()"
          >
            確認へ
          </button>
        </div>
      </template>

      <!-- ===== Step 3 ===== -->
      <template v-else-if="form.step.value === 3">
        <ReservationSummary
          :performance-label="form.performance.value.label"
          :tier-name="form.selectedTier.value.name"
          :quantity="form.quantity.value"
          :reservation-type="form.reservationType.value"
          :total-price="form.totalPrice.value"
          :guest-name="form.guestName.value"
          :guest-email="form.guestEmail.value"
          :guest-phone="form.guestPhone.value"
          class="mb-4"
        />

        <div v-if="submitError" class="alert alert-danger mb-3">{{ submitError }}</div>

        <div class="d-flex gap-2">
          <button class="btn btn-outline-secondary flex-fill py-3" @click="form.prevStep()">
            戻る
          </button>
          <button class="btn btn-primary flex-fill py-3" @click="handleSubmit">
            予約を確定する
          </button>
        </div>
      </template>
    </template>

    <template v-else>
      <div class="text-center py-5 text-muted">公演が見つかりません</div>
    </template>
  </div>
</template>
