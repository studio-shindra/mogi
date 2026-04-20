<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchLink } from '../api/links.js'
import { createReservation, createApplication } from '../api/reservations.js'
import { IconCircleCheck, IconArmchair } from '@tabler/icons-vue'

const props = defineProps({ token: String })
const router = useRouter()

const loading = ref(true)
const notFound = ref(false)
const inactive = ref(false)

const link = ref(null)
const submitting = ref(false)
const submitted = ref(false)
const submitError = ref('')

const selectedTierId = ref(null)
const quantity = ref(1)
const guestName = ref('')
const guestEmail = ref('')
const guestPhone = ref('')
const memo = ref('')
const isFanclubMember = ref(false)

const mode = computed(() => link.value?.mode)
const performance = computed(() => link.value?.performance)
const seatTiers = computed(() => performance.value?.seat_tiers ?? [])

const selectedTier = computed(() =>
  seatTiers.value.find((t) => t.id === selectedTierId.value),
)

const isApplication = computed(() => mode.value === 'application')
const isReservation = computed(() => mode.value === 'reservation')

const headingLabel = computed(() =>
  isApplication.value ? '応募フォーム' : 'ご予約フォーム',
)
const submitLabel = computed(() =>
  isApplication.value ? '応募する' : '予約を確定する',
)

const maxQuantity = computed(() => {
  if (!selectedTier.value) return 10
  if (isApplication.value) return 10
  const r = selectedTier.value.remaining ?? 10
  return Math.max(1, Math.min(r, 10))
})

const canSubmit = computed(() => {
  if (!selectedTierId.value) return false
  if (!guestName.value.trim()) return false
  if (!guestPhone.value.trim()) return false
  if (quantity.value < 1 || quantity.value > 10) return false
  if (isReservation.value && selectedTier.value) {
    const r = selectedTier.value.remaining ?? 0
    if (quantity.value > r) return false
  }
  return true
})

const tierPrice = computed(() => selectedTier.value?.price_cash ?? 0)
const totalPrice = computed(() => tierPrice.value * quantity.value)

onMounted(async () => {
  try {
    link.value = await fetchLink(props.token)
  } catch (e) {
    if (e.response?.status === 404) notFound.value = true
    else if (e.response?.status === 410) inactive.value = true
    else notFound.value = true
  } finally {
    loading.value = false
  }
})

async function handleSubmit() {
  if (!canSubmit.value || submitting.value) return
  submitting.value = true
  submitError.value = ''
  try {
    const payload = {
      performance_id: performance.value.id,
      seat_tier_id: selectedTierId.value,
      quantity: quantity.value,
      guest_name: guestName.value.trim(),
      guest_email: guestEmail.value.trim(),
      guest_phone: guestPhone.value.trim(),
      link_token: props.token,
    }

    if (isApplication.value) {
      payload.memo = memo.value.trim()
      payload.is_fanclub_member = isFanclubMember.value
      await createApplication(payload)
      submitted.value = true
    } else {
      const result = await createReservation(payload)
      router.push({ name: 'reservation-confirm', params: { token: result.token } })
    }
  } catch (e) {
    const data = e.response?.data
    submitError.value = data
      ? Object.values(data).flat().join(' / ')
      : '送信に失敗しました'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="container py-5" style="max-width: 640px; padding-top: 56px">
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-mogi" role="status" />
    </div>

    <template v-else-if="notFound">
      <div class="text-center py-5 text-muted">
        リンクが見つかりません
      </div>
    </template>

    <template v-else-if="inactive">
      <div class="text-center py-5 text-muted">
        このリンクは現在ご利用いただけません
      </div>
    </template>

    <template v-else-if="submitted && isApplication">
      <div class="text-center py-5">
        <IconCircleCheck :size="72" class="text-mogi mb-3" stroke-width="1.2" />
        <h1 class="fs-4 fw-bold mb-3">応募を受け付けました</h1>
        <p class="text-muted">結果は後日ご案内します。</p>
      </div>
    </template>

    <template v-else-if="performance">
      <h1 class="fs-5 fw-bold mb-1">{{ headingLabel }}</h1>
      <p class="text-muted small mb-1">{{ link.label }}</p>
      <p class="small text-muted mb-1">{{ performance.event_title }}</p>
      <p class="small text-muted mb-4">
        {{ performance.label }}
        / 開場 {{ performance.open_at.slice(11, 16) }}
        / 開演 {{ performance.starts_at.slice(11, 16) }}
      </p>

      <div
        v-if="isApplication"
        class="alert bg-mogi-light border-0 small py-2 mb-4"
      >
        これは応募フォームです。当落結果は後日ご連絡します。<br>
        当選後、会場にて現金でお支払いいただきます。
      </div>
      <div
        v-else
        class="alert alert-warning border-0 small py-2 mb-4"
      >
        お支払いは当日会場にて現金でお願いいたします。
      </div>

      <!-- 席種 -->
      <div class="mb-3">
        <label class="form-label small text-muted">
          {{ isApplication ? '希望席種' : '席種' }} <span class="text-danger">*</span>
        </label>
        <div class="d-flex flex-column gap-2">
          <button
            v-for="t in seatTiers"
            :key="t.id"
            type="button"
            class="card text-start border"
            :class="{
              'border-2': selectedTierId === t.id,
              'bg-mogi-light': selectedTierId === t.id,
            }"
            :style="selectedTierId === t.id ? 'border-color: var(--mogi-orange) !important' : ''"
            :disabled="isReservation && (t.remaining ?? 0) <= 0"
            @click="selectedTierId = t.id"
          >
            <div class="card-body py-3 d-flex justify-content-between align-items-center">
              <div class="d-flex align-items-center gap-2">
                <IconArmchair :size="20" class="text-mogi" />
                <div>
                  <div class="fw-bold">{{ t.name }}</div>
                  <div v-if="isReservation && (t.remaining ?? 0) <= 0" class="text-muted small">完売</div>
                </div>
              </div>
              <div class="fw-bold">
                {{ t.price_cash.toLocaleString() }}<small class="text-muted fw-normal">円</small>
              </div>
            </div>
          </button>
        </div>
      </div>

      <!-- 枚数 -->
      <div class="mb-3">
        <label class="form-label small text-muted">
          {{ isApplication ? '希望枚数' : '枚数' }} <span class="text-danger">*</span>
        </label>
        <div class="d-flex gap-2 flex-wrap">
          <button
            v-for="n in maxQuantity"
            :key="n"
            type="button"
            class="btn"
            :class="quantity === n ? 'btn-primary' : 'btn-outline-secondary'"
            style="min-width: 48px"
            @click="quantity = n"
          >
            {{ n }}
          </button>
        </div>
      </div>

      <!-- 合計（予約モードのみ表示） -->
      <div v-if="isReservation && selectedTier" class="card bg-mogi-light mb-3">
        <div class="card-body d-flex justify-content-between align-items-center py-3">
          <div>
            <span class="fw-bold">{{ selectedTier.name }}</span>
            <span class="text-muted ms-2">× {{ quantity }}枚</span>
          </div>
          <span class="fs-5 fw-bold text-mogi">
            {{ totalPrice.toLocaleString() }}<small class="text-muted fw-normal">円</small>
          </span>
        </div>
      </div>

      <!-- 氏名 -->
      <div class="mb-3">
        <label class="form-label small text-muted">お名前 <span class="text-danger">*</span></label>
        <input type="text" class="form-control" placeholder="山田 太郎" v-model="guestName" />
      </div>

      <!-- メール -->
      <div class="mb-3">
        <label class="form-label small text-muted">メールアドレス（任意）</label>
        <input type="email" class="form-control" placeholder="example@email.com" v-model="guestEmail" />
      </div>

      <!-- 電話 -->
      <div class="mb-3">
        <label class="form-label small text-muted">電話番号 <span class="text-danger">*</span></label>
        <input type="tel" class="form-control" placeholder="090-1234-5678" v-model="guestPhone" />
      </div>

      <!-- FC会員（応募モードのみ） -->
      <div v-if="isApplication" class="mb-3">
        <label class="form-label small text-muted">ゲストのファンクラブ会員ですか？</label>
        <div class="d-flex gap-2">
          <button
            type="button"
            class="btn flex-fill"
            :class="isFanclubMember ? 'btn-primary' : 'btn-outline-secondary'"
            @click="isFanclubMember = true"
          >
            はい
          </button>
          <button
            type="button"
            class="btn flex-fill"
            :class="!isFanclubMember ? 'btn-primary' : 'btn-outline-secondary'"
            @click="isFanclubMember = false"
          >
            いいえ
          </button>
        </div>
      </div>

      <!-- 備考（応募モードのみ） -->
      <div v-if="isApplication" class="mb-4">
        <label class="form-label small text-muted">備考（任意）</label>
        <textarea class="form-control" rows="2" v-model="memo" />
      </div>

      <div v-if="submitError" class="alert alert-danger mb-3">{{ submitError }}</div>

      <button
        class="btn btn-primary w-100 py-3"
        :disabled="!canSubmit || submitting"
        @click="handleSubmit"
      >
        <span v-if="submitting" class="spinner-border spinner-border-sm me-2" />
        {{ submitLabel }}
      </button>
    </template>
  </div>
</template>
