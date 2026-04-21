<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchLink } from '../api/links.js'
import { createReservation, createApplication } from '../api/reservations.js'
import { IconCircleCheck, IconArmchair, IconCalendarEvent } from '@tabler/icons-vue'
import { formatJstTime } from '../utils/datetime.js'

const props = defineProps({ token: String })
const router = useRouter()

const loading = ref(true)
const notFound = ref(false)
const inactive = ref(false)

const link = ref(null)
const submitting = ref(false)
const submitted = ref(false)
const submitError = ref('')

const selectedPerformanceId = ref(null)
const selectedTierId = ref(null)
const firstChoiceTierId = ref(null)
const secondChoiceTierId = ref(null)
const allowAnySeat = ref(false)
const quantity = ref(1)
const guestName = ref('')
const guestEmail = ref('')
const guestPhone = ref('')
const memo = ref('')
const isFanclubMember = ref(false)

const mode = computed(() => link.value?.mode)
const event = computed(() => link.value?.event)
const performances = computed(() => event.value?.performances ?? [])

const selectedPerformance = computed(() =>
  performances.value.find((p) => p.id === selectedPerformanceId.value),
)
const seatTiers = computed(() => selectedPerformance.value?.seat_tiers ?? [])

const selectedTier = computed(() =>
  seatTiers.value.find((t) => t.id === selectedTierId.value),
)
const secondChoiceTiers = computed(() =>
  seatTiers.value.filter((t) => t.id !== firstChoiceTierId.value),
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
  if (!selectedTier.value) return 4
  if (isApplication.value) return 4
  const r = selectedTier.value.remaining ?? 4
  return Math.max(1, Math.min(r, 4))
})

const canSubmit = computed(() => {
  if (!selectedPerformanceId.value) return false
  if (isApplication.value) {
    if (!firstChoiceTierId.value) return false
  } else {
    if (!selectedTierId.value) return false
  }
  if (!guestName.value.trim()) return false
  if (!guestPhone.value.trim()) return false
  if (quantity.value < 1 || quantity.value > 4) return false
  if (isReservation.value && selectedTier.value) {
    const r = selectedTier.value.remaining ?? 0
    if (quantity.value > r) return false
  }
  return true
})

const tierPrice = computed(() => selectedTier.value?.price_card ?? 0)
const totalPrice = computed(() => tierPrice.value * quantity.value)

const headerImageUrl = computed(
  () => link.value?.header_image_url || event.value?.flyer_image_url || '',
)
const hasHeader = computed(() => !!headerImageUrl.value)

function performanceRemaining(perf) {
  return (perf.seat_tiers ?? []).reduce(
    (sum, t) => sum + (t.remaining ?? t.capacity ?? 0),
    0,
  )
}

function performanceSoldOut(perf) {
  if (isApplication.value) return false
  return performanceRemaining(perf) <= 0
}

function resetSeatSelection() {
  selectedTierId.value = null
  firstChoiceTierId.value = null
  secondChoiceTierId.value = null
  allowAnySeat.value = false
}

function selectPerformance(perf) {
  if (performanceSoldOut(perf)) return
  selectedPerformanceId.value = perf.id
  resetSeatSelection()
  quantity.value = 1
}

function backToPerformanceSelect() {
  selectedPerformanceId.value = null
  resetSeatSelection()
}

function selectFirstChoice(tierId) {
  firstChoiceTierId.value = tierId
  if (secondChoiceTierId.value === tierId) {
    secondChoiceTierId.value = null
  }
}

function selectSecondChoice(tierId) {
  secondChoiceTierId.value = secondChoiceTierId.value === tierId ? null : tierId
}

onMounted(async () => {
  try {
    link.value = await fetchLink(props.token)
    // 公演が1本なら自動選択
    if (performances.value.length === 1) {
      selectedPerformanceId.value = performances.value[0].id
    }
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
      performance_id: selectedPerformanceId.value,
      quantity: quantity.value,
      guest_name: guestName.value.trim(),
      guest_email: guestEmail.value.trim(),
      guest_phone: guestPhone.value.trim(),
      link_token: props.token,
    }

    if (isApplication.value) {
      payload.first_choice_seat_tier_id = firstChoiceTierId.value
      payload.second_choice_seat_tier_id = secondChoiceTierId.value
      payload.allow_any_seat = allowAnySeat.value
      payload.memo = memo.value.trim()
      payload.is_fanclub_member = isFanclubMember.value
      await createApplication(payload)
      submitted.value = true
    } else {
      payload.seat_tier_id = selectedTierId.value
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

    <!-- 公演選択ステップ -->
    <template v-else-if="event && !selectedPerformance">
      <img
        v-if="hasHeader"
        :src="headerImageUrl"
        :alt="event.title"
        class="w-100 rounded mb-3"
      />
      <div v-if="hasHeader" class="mb-4">
        <span class="badge rounded-pill bg-mogi text-white px-3 py-2">
          {{ headingLabel }}
        </span>
      </div>
      <template v-else>
        <h1 class="fs-5 fw-bold mb-1">{{ headingLabel }}</h1>
        <p class="text-muted small mb-1">{{ link.label }}</p>
        <p class="small text-muted mb-4">{{ event.title }}</p>
      </template>

      <div v-if="performances.length === 0" class="text-center py-5 text-muted">
        現在予約可能な公演がありません
      </div>

      <div v-else class="mb-3">
        <label class="form-label fw-bold fs-5 mb-1">公演を選択</label>
        <p class="small text-muted mb-2">※【】内はアフタートークのゲストです</p>
        <div class="d-flex flex-column gap-2">
          <button
            v-for="perf in performances"
            :key="perf.id"
            type="button"
            class="card text-start border"
            :disabled="performanceSoldOut(perf)"
            @click="selectPerformance(perf)"
          >
            <div class="card-body py-3 d-flex align-items-center gap-2">
              <IconCalendarEvent :size="20" class="text-mogi" />
              <div class="flex-grow-1">
                <div class="fw-bold">{{ perf.label }}</div>
                <div class="text-muted small">
                  開場 {{ formatJstTime(perf.open_at) }}
                  / 開演 {{ formatJstTime(perf.starts_at) }}
                </div>
              </div>
              <div v-if="isReservation && performanceSoldOut(perf)" class="text-muted small">
                完売
              </div>
            </div>
          </button>
        </div>
      </div>
    </template>

    <!-- 席種 → 情報入力 → 送信 -->
    <template v-else-if="selectedPerformance">
      <img
        v-if="hasHeader"
        :src="headerImageUrl"
        :alt="event.title"
        class="w-100 rounded mb-3"
      />
      <div v-if="hasHeader" class="d-flex align-items-center gap-2 mb-2">
        <span class="badge rounded-pill bg-mogi text-white px-3 py-2">
          {{ headingLabel }}
        </span>
        <span class="small text-muted">
          {{ selectedPerformance.label }}
          / 開演 {{ formatJstTime(selectedPerformance.starts_at) }}
        </span>
      </div>
      <template v-else>
        <h1 class="fs-5 fw-bold mb-1">{{ headingLabel }}</h1>
        <p class="text-muted small mb-1">{{ link.label }}</p>
        <p class="small text-muted mb-1">{{ event.title }}</p>
        <p class="small text-muted mb-4">
          {{ selectedPerformance.label }}
          / 開場 {{ formatJstTime(selectedPerformance.open_at) }}
          / 開演 {{ formatJstTime(selectedPerformance.starts_at) }}
        </p>
      </template>

      <button
        v-if="performances.length > 1"
        type="button"
        class="btn btn-link btn-sm p-0 mb-3"
        @click="backToPerformanceSelect"
      >
        ← 公演を選び直す
      </button>

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

      <!-- 座席参考表 -->
      <div class="mb-3">
        <label class="form-label small text-muted">座席参考表</label>
        <img
          src="/sheet-0421.png"
          alt="新生館スタジオ 座席参考表"
          class="w-100 rounded border"
        />
      </div>

      <!-- 席種（予約モード） -->
      <div v-if="isReservation" class="mb-3">
        <label class="form-label small text-muted">
          席種 <span class="text-danger">*</span>
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
            :disabled="(t.remaining ?? 0) <= 0"
            @click="selectedTierId = t.id"
          >
            <div class="card-body py-3 d-flex justify-content-between align-items-center">
              <div class="d-flex align-items-center gap-2">
                <IconArmchair :size="20" class="text-mogi" />
                <div>
                  <div class="fw-bold">{{ t.name }}</div>
                  <div v-if="(t.remaining ?? 0) <= 0" class="text-muted small">完売</div>
                </div>
              </div>
              <div class="fw-bold">
                {{ t.price_card.toLocaleString() }}<small class="text-muted fw-normal">円</small>
              </div>
            </div>
          </button>
        </div>
      </div>

      <!-- 希望席（応募モード） -->
      <template v-else>
        <!-- 第一希望席 -->
        <div class="mb-3">
          <label class="form-label small text-muted">
            第一希望席 <span class="text-danger">*</span>
          </label>
          <div class="d-flex flex-column gap-2">
            <button
              v-for="t in seatTiers"
              :key="t.id"
              type="button"
              class="card text-start border"
              :class="{
                'border-2': firstChoiceTierId === t.id,
                'bg-mogi-light': firstChoiceTierId === t.id,
              }"
              :style="firstChoiceTierId === t.id ? 'border-color: var(--mogi-orange) !important' : ''"
              @click="selectFirstChoice(t.id)"
            >
              <div class="card-body py-3 d-flex justify-content-between align-items-center">
                <div class="d-flex align-items-center gap-2">
                  <IconArmchair :size="20" class="text-mogi" />
                  <div class="fw-bold">{{ t.name }}</div>
                </div>
                <div class="fw-bold">
                  {{ t.price_card.toLocaleString() }}<small class="text-muted fw-normal">円</small>
                </div>
              </div>
            </button>
          </div>
        </div>

        <!-- 第二希望席 -->
        <div class="mb-3">
          <label class="form-label small text-muted">第二希望席（任意）</label>
          <div class="d-flex flex-column gap-2">
            <button
              v-for="t in secondChoiceTiers"
              :key="t.id"
              type="button"
              class="card text-start border"
              :class="{
                'border-2': secondChoiceTierId === t.id,
                'bg-mogi-light': secondChoiceTierId === t.id,
              }"
              :style="secondChoiceTierId === t.id ? 'border-color: var(--mogi-orange) !important' : ''"
              @click="selectSecondChoice(t.id)"
            >
              <div class="card-body py-3 d-flex justify-content-between align-items-center">
                <div class="d-flex align-items-center gap-2">
                  <IconArmchair :size="20" class="text-mogi" />
                  <div class="fw-bold">{{ t.name }}</div>
                </div>
                <div class="fw-bold">
                  {{ t.price_card.toLocaleString() }}<small class="text-muted fw-normal">円</small>
                </div>
              </div>
            </button>
          </div>
          <div class="form-text small">もう一度押すと選択解除できます</div>
        </div>

        <!-- どの席でも可 -->
        <div class="mb-3">
          <div class="form-check">
            <input
              id="allow-any-seat"
              class="form-check-input"
              type="checkbox"
              v-model="allowAnySeat"
            />
            <label class="form-check-label small" for="allow-any-seat">
              希望席が取れない場合、どの席でもご案内可能
            </label>
          </div>
        </div>
      </template>

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
