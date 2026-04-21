<script setup>
import { onMounted, ref, computed } from 'vue'
import { fetchEventDetail } from '../api/events.js'
import { createApplication } from '../api/reservations.js'
import { IconCircleCheck } from '@tabler/icons-vue'
import { formatJstTime } from '../utils/datetime.js'

const props = defineProps({ slug: String, performanceId: String })

const loading = ref(true)
const submitting = ref(false)
const submitted = ref(false)
const submitError = ref('')

const eventTitle = ref('')
const performance = ref(null)

const firstChoiceTierId = ref(null)
const secondChoiceTierId = ref(null)
const allowAnySeat = ref(false)
const quantity = ref(1)
const guestName = ref('')
const guestEmail = ref('')
const guestPhone = ref('')
const memo = ref('')
const isFanclubMember = ref(false)

const secondChoiceTiers = computed(() =>
  (performance.value?.seat_tiers ?? []).filter((t) => t.id !== firstChoiceTierId.value),
)

const canSubmit = computed(() => {
  if (!firstChoiceTierId.value) return false
  if (!guestName.value.trim()) return false
  if (!guestPhone.value.trim()) return false
  return quantity.value >= 1 && quantity.value <= 4
})

function selectFirst(tierId) {
  firstChoiceTierId.value = tierId
  if (secondChoiceTierId.value === tierId) {
    secondChoiceTierId.value = null
  }
}

function selectSecond(tierId) {
  secondChoiceTierId.value = secondChoiceTierId.value === tierId ? null : tierId
}

onMounted(async () => {
  try {
    const event = await fetchEventDetail(props.slug)
    eventTitle.value = event.title
    performance.value = event.performances.find(
      (p) => p.id === Number(props.performanceId),
    )
  } catch (e) {
    // null で表示
  } finally {
    loading.value = false
  }
})

async function handleSubmit() {
  if (!canSubmit.value || submitting.value) return
  submitting.value = true
  submitError.value = ''
  try {
    await createApplication({
      performance_id: performance.value.id,
      first_choice_seat_tier_id: firstChoiceTierId.value,
      second_choice_seat_tier_id: secondChoiceTierId.value,
      allow_any_seat: allowAnySeat.value,
      quantity: quantity.value,
      guest_name: guestName.value.trim(),
      guest_email: guestEmail.value.trim(),
      guest_phone: guestPhone.value.trim(),
      memo: memo.value.trim(),
      is_fanclub_member: isFanclubMember.value,
    })
    submitted.value = true
  } catch (e) {
    const data = e.response?.data
    if (data) {
      submitError.value = Object.values(data).flat().join(' / ')
    } else {
      submitError.value = '応募の送信に失敗しました'
    }
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

    <template v-else-if="submitted">
      <div class="text-center py-5">
        <IconCircleCheck :size="72" class="text-mogi mb-3" stroke-width="1.2" />
        <h1 class="fs-4 fw-bold mb-3">応募を受け付けました</h1>
        <p class="text-muted">結果は後日ご案内します。</p>
      </div>
    </template>

    <template v-else-if="performance">
      <h1 class="fs-5 fw-bold mb-1">二次先行応募</h1>
      <p class="text-muted small mb-1">{{ eventTitle }}</p>
      <p class="small text-muted mb-4">
        {{ performance.label }}
        / 開場 {{ formatJstTime(performance.open_at) }}
        / 開演 {{ formatJstTime(performance.starts_at) }}
      </p>

      <div class="alert bg-mogi-light border-0 small py-2 mb-4">
        これは応募フォームです。応募後、当落結果は後日ご連絡いたします。<br>
        当選後、会場にて現金でお支払いいただきます。
      </div>

      <!-- 第一希望席 -->
      <div class="mb-3">
        <label class="form-label small text-muted">第一希望席 <span class="text-danger">*</span></label>
        <div class="d-flex flex-column gap-2">
          <button
            v-for="t in performance.seat_tiers"
            :key="t.id"
            type="button"
            class="card text-start border"
            :class="{
              'border-2': firstChoiceTierId === t.id,
              'bg-mogi-light': firstChoiceTierId === t.id,
            }"
            :style="firstChoiceTierId === t.id ? 'border-color: var(--mogi-orange) !important' : ''"
            @click="selectFirst(t.id)"
          >
            <div class="card-body py-3 d-flex justify-content-between align-items-center">
              <span class="fw-bold">{{ t.name }}</span>
              <span class="fw-bold">{{ t.price_card.toLocaleString() }}<small class="text-muted fw-normal">円</small></span>
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
            @click="selectSecond(t.id)"
          >
            <div class="card-body py-3 d-flex justify-content-between align-items-center">
              <span class="fw-bold">{{ t.name }}</span>
              <span class="fw-bold">{{ t.price_card.toLocaleString() }}<small class="text-muted fw-normal">円</small></span>
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

      <!-- 枚数 -->
      <div class="mb-3">
        <label class="form-label small text-muted">希望枚数 <span class="text-danger">*</span></label>
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

      <!-- 氏名 -->
      <div class="mb-3">
        <label class="form-label small text-muted">お名前 <span class="text-danger">*</span></label>
        <input type="text" class="form-control" placeholder="山田 太郎" v-model="guestName" />
      </div>

      <!-- メール -->
      <div class="mb-3">
        <label class="form-label small text-muted">メールアドレス（任意）</label>
        <input type="email" class="form-control" placeholder="example@email.com" v-model="guestEmail" />
        <div class="form-text small">受付確認と結果連絡にメールをお送りします</div>
      </div>

      <!-- 電話 -->
      <div class="mb-3">
        <label class="form-label small text-muted">電話番号 <span class="text-danger">*</span></label>
        <input type="tel" class="form-control" placeholder="090-1234-5678" v-model="guestPhone" />
      </div>

      <!-- FC会員 -->
      <div class="mb-3">
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

      <!-- 備考 -->
      <div class="mb-4">
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
        応募する
      </button>
    </template>

    <template v-else>
      <div class="text-center py-5 text-muted">公演が見つかりません</div>
    </template>
  </div>
</template>
