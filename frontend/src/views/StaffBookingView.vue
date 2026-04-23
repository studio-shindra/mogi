<script setup>
import { computed, onMounted, ref } from 'vue'
import { fetchEvents, fetchStaffEventDetail } from '../api/events.js'
import { staffWalkIn } from '../api/reservations.js'
import { SALES_CHANNELS } from '../composables/useStaffActions.js'
import { formatJstTime } from '../utils/datetime.js'

const loading = ref(true)
const submitting = ref(false)
const eventTitle = ref('')
const performances = ref([])

const performanceId = ref(null)
const seatTierId = ref(null)
const quantity = ref(1)
const bookingMode = ref('advance') // 'advance' = 事前予約 / 'walk_in' = 当日券
const salesChannel = ref('general')
const guestName = ref('')
const guestPhone = ref('')
const memo = ref('')

// 事前予約モードで選べる販売区分（当日券を除く）
const advanceChannels = SALES_CHANNELS.filter((ch) => ch.value !== 'walk_in')

function setBookingMode(mode) {
  bookingMode.value = mode
  salesChannel.value = mode === 'walk_in' ? 'walk_in' : 'general'
}

const flash = ref(null) // { type, message }
let flashTimer = null

function setFlash(type, message) {
  flash.value = { type, message }
  clearTimeout(flashTimer)
  flashTimer = setTimeout(() => { flash.value = null }, 4000)
}

const selectedPerf = computed(() =>
  performances.value.find((p) => p.id === performanceId.value),
)
// 通常席種は code 辞書順（row_a→row_b→…→row_e_bench）、関係者席は末尾に並べる
const seatTiers = computed(() => {
  const tiers = selectedPerf.value?.seat_tiers ?? []
  return [...tiers].sort((a, b) => {
    const aStaff = a.code === 'staff_seat'
    const bStaff = b.code === 'staff_seat'
    if (aStaff !== bStaff) return aStaff ? 1 : -1
    return (a.code || '').localeCompare(b.code || '')
  })
})
const selectedTier = computed(() =>
  seatTiers.value.find((t) => t.id === seatTierId.value),
)

function tierLabel(tier) {
  // 「A列」「D列ベンチシート」「関係者席」の先頭1文字を取り出して A / B / C / D / E / 関
  return (tier.name || '').charAt(0) || tier.code
}

function selectTier(tier) {
  // 席種選択で販売区分は自動変更しない。
  // （関係者席でも有料・無料の両用途があるため、販売区分はユーザーが都度選ぶ）
  seatTierId.value = tier.id
}

// 販売区分=招待は0円、事前は前売り価格、当日は当日価格を採用
const unitPrice = computed(() => {
  if (!selectedTier.value) return 0
  if (salesChannel.value === 'invite') return 0
  return bookingMode.value === 'walk_in'
    ? selectedTier.value.price_cash
    : selectedTier.value.price_card
})

const canSubmit = computed(() =>
  !!performanceId.value &&
  !!seatTierId.value &&
  !!guestName.value.trim() &&
  !submitting.value,
)

function selectPerformance(id) {
  if (performanceId.value !== id) {
    performanceId.value = id
    seatTierId.value = null
  }
}

function tierRemaining(tier) {
  return typeof tier.remaining === 'number' ? tier.remaining : null
}

onMounted(async () => {
  try {
    const events = await fetchEvents()
    if (!events.length) return
    const detail = await fetchStaffEventDetail(events[0].slug)
    eventTitle.value = detail.title
    performances.value = detail.performances ?? []
    if (performances.value.length) {
      performanceId.value = performances.value[0].id
    }
  } catch (e) {
    console.error('公演取得失敗:', e)
    setFlash('error', '公演情報の取得に失敗しました')
  } finally {
    loading.value = false
  }
})

function resetForm() {
  seatTierId.value = null
  quantity.value = 1
  bookingMode.value = 'advance'
  salesChannel.value = 'general'
  guestName.value = ''
  guestPhone.value = ''
  memo.value = ''
}

async function handleSubmit() {
  if (!canSubmit.value) return
  submitting.value = true
  try {
    await staffWalkIn({
      performance_id: performanceId.value,
      seat_tier_id: seatTierId.value,
      quantity: quantity.value,
      guest_name: guestName.value.trim(),
      guest_phone: guestPhone.value.trim(),
      memo: memo.value.trim(),
      sales_channel: salesChannel.value,
    })
    setFlash('success', `${guestName.value.trim()} さんの予約を登録しました`)
    resetForm()
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } catch (e) {
    console.error('予約登録失敗:', e)
    const detail = e.response?.data
    let msg = '予約登録に失敗しました'
    if (detail) {
      if (typeof detail === 'string') msg = detail
      else if (detail.detail) msg = detail.detail
      else msg = Object.values(detail).flat().join(' / ') || msg
    }
    setFlash('error', msg)
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="container py-5" style="max-width: 640px; padding-top: 56px">
    <!-- 戻る -->
    <RouterLink
      :to="{ name: 'manage-dashboard' }"
      class="d-inline-flex align-items-center gap-1 text-decoration-none text-muted small mb-3"
    >
      &larr; 受付へ戻る
    </RouterLink>

    <h1 class="fs-5 fw-bold mb-1">予約登録</h1>
    <p v-if="eventTitle" class="text-muted small mb-4">{{ eventTitle }}</p>

    <!-- フラッシュ -->
    <div
      v-if="flash"
      class="alert py-2 px-3 mb-3"
      :class="flash.type === 'success' ? 'alert-success' : 'alert-danger'"
      role="alert"
    >
      {{ flash.message }}
    </div>

    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-mogi" role="status" />
    </div>

    <template v-else-if="performances.length">
      <!-- 事前 / 当日 モード切替（最上段） -->
      <div class="mb-3">
        <label class="form-label small text-muted">予約区分 <span class="text-danger">*</span></label>
        <div class="d-flex gap-2">
          <button
            type="button"
            class="btn flex-fill py-2"
            :class="bookingMode === 'advance' ? 'btn-primary' : 'btn-outline-secondary'"
            @click="setBookingMode('advance')"
          >
            事前
          </button>
          <button
            type="button"
            class="btn flex-fill py-2"
            :class="bookingMode === 'walk_in' ? 'btn-primary' : 'btn-outline-secondary'"
            @click="setBookingMode('walk_in')"
          >
            当日
          </button>
        </div>
      </div>

      <!-- 公演日程 -->
      <div class="mb-3">
        <label class="form-label small text-muted">公演 <span class="text-danger">*</span></label>
        <div class="d-flex flex-column gap-2">
          <button
            v-for="p in performances"
            :key="p.id"
            type="button"
            class="card text-start border"
            :class="{
              'border-2': performanceId === p.id,
              'bg-mogi-light': performanceId === p.id,
            }"
            :style="performanceId === p.id ? 'border-color: var(--mogi-orange) !important' : ''"
            @click="selectPerformance(p.id)"
          >
            <div class="card-body py-3">
              <div class="fw-bold">{{ p.label }}</div>
              <div class="small text-muted mt-1">
                開場 {{ formatJstTime(p.open_at) }} / 開演 {{ formatJstTime(p.starts_at) }}
              </div>
            </div>
          </button>
        </div>
      </div>

      <!-- 席種（横並び、スマホでも等分） -->
      <div class="mb-3">
        <label class="form-label small text-muted">席種 <span class="text-danger">*</span></label>
        <div class="d-flex gap-2">
          <button
            v-for="t in seatTiers"
            :key="t.id"
            type="button"
            class="card text-center border"
            :class="{
              'border-2': seatTierId === t.id,
              'bg-mogi-light': seatTierId === t.id,
            }"
            :style="[
              'flex: 1 1 0; min-width: 0;',
              seatTierId === t.id ? 'border-color: var(--mogi-orange) !important' : '',
            ]"
            @click="selectTier(t)"
          >
            <div class="card-body px-1 py-2">
              <div class="fs-4 fw-bold lh-1">{{ tierLabel(t) }}</div>
              <div v-if="tierRemaining(t) !== null" class="small text-muted mt-1">
                残 {{ tierRemaining(t) }}
              </div>
            </div>
          </button>
        </div>
      </div>

      <!-- 枚数 -->
      <div class="mb-3">
        <label class="form-label small text-muted">枚数 <span class="text-danger">*</span></label>
        <div class="d-flex gap-2 flex-wrap">
          <button
            v-for="n in 4"
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

      <!-- 販売区分（事前モードのみ選択可） -->
      <div v-if="bookingMode === 'advance'" class="mb-3">
        <label class="form-label small text-muted">販売区分 <span class="text-danger">*</span></label>
        <div class="d-flex gap-2 flex-wrap">
          <button
            v-for="ch in advanceChannels"
            :key="ch.value"
            type="button"
            class="btn"
            :class="salesChannel === ch.value ? 'btn-primary' : 'btn-outline-secondary'"
            style="min-width: 88px"
            @click="salesChannel = ch.value"
          >
            {{ ch.label }}
          </button>
        </div>
      </div>

      <!-- 氏名 -->
      <div class="mb-3">
        <label class="form-label small text-muted">お名前 <span class="text-danger">*</span></label>
        <input
          type="text"
          class="form-control"
          placeholder="山田 太郎"
          v-model="guestName"
          autocomplete="off"
        />
      </div>

      <!-- 電話 -->
      <div class="mb-3">
        <label class="form-label small text-muted">電話番号</label>
        <input
          type="tel"
          class="form-control"
          placeholder="090-1234-5678"
          v-model="guestPhone"
          autocomplete="off"
        />
      </div>

      <!-- 備考 -->
      <div class="mb-4">
        <label class="form-label small text-muted">備考（任意）</label>
        <textarea class="form-control" rows="2" v-model="memo" />
      </div>

      <!-- 小計プレビュー -->
      <div v-if="selectedTier" class="card bg-mogi-light mb-3">
        <div class="card-body d-flex justify-content-between align-items-center py-3">
          <div>
            <span class="fw-bold">{{ tierLabel(selectedTier) }}</span>
            <span class="text-muted ms-2">× {{ quantity }}枚</span>
            <span class="text-muted ms-2 small">
              ／ {{ bookingMode === 'walk_in' ? '当日' : '事前' }}
            </span>
          </div>
          <span class="fs-5 fw-bold text-mogi">
            {{ (unitPrice * quantity).toLocaleString() }}<small class="text-muted fw-normal">円</small>
          </span>
        </div>
      </div>

      <!-- 登録 -->
      <button
        class="btn btn-primary w-100 py-3"
        :disabled="!canSubmit"
        @click="handleSubmit"
      >
        <span v-if="submitting" class="spinner-border spinner-border-sm me-2" />
        予約を登録
      </button>
    </template>

    <div v-else class="text-center py-5 text-muted">
      公演が見つかりません
    </div>
  </div>
</template>
