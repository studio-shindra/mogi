<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useStaffActions, SALES_CHANNELS } from '../composables/useStaffActions.js'
import StaffSearchBar from '../components/staff/StaffSearchBar.vue'
import StaffReservationRow from '../components/staff/StaffReservationRow.vue'
import ReservationDetailModal from '../components/staff/ReservationDetailModal.vue'
import StaffApplicationRow from '../components/staff/StaffApplicationRow.vue'
import WalkInForm from '../components/staff/WalkInForm.vue'
import PerformanceSummaryCards from '../components/staff/PerformanceSummaryCards.vue'
import PerformanceApplicationSummaryCards from '../components/staff/PerformanceApplicationSummaryCards.vue'
import TotalReservationSummaryCard from '../components/staff/TotalReservationSummaryCard.vue'
import TotalApplicationSummaryCard from '../components/staff/TotalApplicationSummaryCard.vue'

const staff = useStaffActions()

const showWalkIn = ref(false)
const activeTab = ref('reservations')
const selectedReservation = ref(null)

// 予約一覧のソート状態（''=申込順デフォルト）
const sortKey = ref('')
const sortDir = ref('asc')

const sortGetters = {
  name: (r) => r.guest_name || '',
  date: (r) => r.performance?.starts_at || '',
  seat: (r) => r.seat_tier?.name || '',
  channel: (r) => r.sales_channel || '',
  type: (r) => r.reservation_type || '',
  status: (r) => r.status || '',
}

function toggleSort(key) {
  if (sortKey.value !== key) {
    sortKey.value = key
    sortDir.value = 'asc'
  } else if (sortDir.value === 'asc') {
    sortDir.value = 'desc'
  } else {
    sortKey.value = ''
    sortDir.value = 'asc'
  }
}

function sortArrow(key) {
  if (sortKey.value !== key) return ''
  return sortDir.value === 'asc' ? ' ↑' : ' ↓'
}

const sortedReservations = computed(() => {
  const list = staff.reservations.value
  if (!sortKey.value) return list
  const g = sortGetters[sortKey.value]
  const dir = sortDir.value === 'asc' ? 1 : -1
  return [...list].sort((a, b) => {
    const va = g(a)
    const vb = g(b)
    if (va < vb) return -1 * dir
    if (va > vb) return 1 * dir
    return 0
  })
})

// 応募一覧のソート状態（''=日程昇順＋応募順デフォルト）
const appSortKey = ref('')
const appSortDir = ref('asc')

const appSortGetters = {
  name: (a) => a.guest_name || '',
  seat: (a) => a.first_choice_seat_tier?.name || '',
  date: (a) => a.performance?.starts_at || '',
}

function appToggleSort(key) {
  if (appSortKey.value !== key) {
    appSortKey.value = key
    appSortDir.value = 'asc'
  } else if (appSortDir.value === 'asc') {
    appSortDir.value = 'desc'
  } else {
    appSortKey.value = ''
    appSortDir.value = 'asc'
  }
}

function appSortArrow(key) {
  if (appSortKey.value !== key) return ''
  return appSortDir.value === 'asc' ? ' ↑' : ' ↓'
}

const sortedApplications = computed(() => {
  const list = staff.applications.value
  // デフォルト: 日程昇順 → 元の応募順
  if (!appSortKey.value) {
    return list
      .map((a, i) => ({ a, i }))
      .sort((x, y) => {
        const da = x.a.performance?.starts_at || ''
        const db = y.a.performance?.starts_at || ''
        if (da < db) return -1
        if (da > db) return 1
        return x.i - y.i
      })
      .map((x) => x.a)
  }
  const g = appSortGetters[appSortKey.value]
  const dir = appSortDir.value === 'asc' ? 1 : -1
  return [...list].sort((a, b) => {
    const va = g(a)
    const vb = g(b)
    if (va < vb) return -1 * dir
    if (va > vb) return 1 * dir
    return 0
  })
})

onMounted(async () => {
  await staff.loadPerformances()
  staff.loadPerformanceSummaries()
  staff.search()
})

watch(activeTab, (tab) => {
  if (tab === 'applications') staff.loadApplications()
  else staff.search()
})

async function handleConfirmApplication(application, assignedSeatTierId) {
  await staff.confirmApplication(application, assignedSeatTierId)
}

async function handleRejectApplication(application) {
  await staff.rejectApplication(application)
}

async function handleMarkPaid(reservation) {
  await staff.markPaid(reservation)
}

async function handleCheckIn(reservation) {
  await staff.checkIn(reservation)
}

async function handleCancel(reservation) {
  await staff.cancel(reservation)
}

async function handleWalkIn(data) {
  try {
    await staff.createWalkIn(data)
    showWalkIn.value = false
  } catch {
    // flash はuseStaffActions側で設定済み
  }
}
</script>

<template>
  <div class="container-fluid py-3">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h1 class="h4 mb-0">受付</h1>
      <div class="d-flex gap-2">
        <RouterLink to="/manage/sales" class="btn btn-sm btn-outline-secondary">売上サマリー</RouterLink>
        <RouterLink
          v-if="activeTab === 'reservations'"
          to="/manage/booking"
          class="btn btn-sm btn-outline-primary"
        >
          予約登録
        </RouterLink>
        <button
          v-if="activeTab === 'reservations'"
          class="btn btn-sm btn-outline-dark"
          @click="showWalkIn = !showWalkIn"
        >
          {{ showWalkIn ? '閉じる' : '当日券登録' }}
        </button>
      </div>
    </div>

    <!-- タブ切替 -->
    <ul class="nav nav-tabs mb-3">
      <li class="nav-item">
        <button
          type="button"
          class="nav-link"
          :class="{ active: activeTab === 'reservations' }"
          @click="activeTab = 'reservations'"
        >
          予約
        </button>
      </li>
      <li class="nav-item">
        <button
          type="button"
          class="nav-link"
          :class="{ active: activeTab === 'applications' }"
          @click="activeTab = 'applications'"
        >
          応募
        </button>
      </li>
    </ul>

    <!-- フラッシュメッセージ -->
    <div
      v-if="staff.flash.value"
      class="alert alert-sm py-2 px-3 mb-3"
      :class="staff.flash.value.type === 'success' ? 'alert-success' : 'alert-danger'"
      role="alert"
    >
      {{ staff.flash.value.message }}
    </div>

    <!-- 当日券登録フォーム（予約タブのみ） -->
    <div v-if="showWalkIn && activeTab === 'reservations'" class="card mb-3">
      <div class="card-body">
        <h6 class="card-title mb-3">当日券登録</h6>
        <WalkInForm :performances="staff.performances.value" @created="handleWalkIn" />
      </div>
    </div>

    <!-- ===== 予約タブ ===== -->
    <template v-if="activeTab === 'reservations'">
    <!-- 公演別サマリーカード（上段: 運営状況）+ 左端に全公演合計 -->
    <PerformanceSummaryCards :summaries="staff.performanceSummaries.value">
      <template #leading>
        <TotalReservationSummaryCard :summaries="staff.performanceSummaries.value" />
      </template>
    </PerformanceSummaryCards>

    <!-- 検索バー -->
    <StaffSearchBar
      :search-query="staff.searchQuery.value"
      :selected-performance-id="staff.selectedPerformanceId.value"
      :selected-sales-channel="staff.selectedSalesChannel.value"
      :performances="staff.performances.value"
      @update:search-query="(v) => (staff.searchQuery.value = v)"
      @update:selected-performance-id="(v) => (staff.selectedPerformanceId.value = v)"
      @update:selected-sales-channel="(v) => (staff.selectedSalesChannel.value = v)"
      @search="staff.search()"
    />

    <!-- 集計（上段: 当日運営の主要数値） -->
    <div class="row g-2 mb-2">
      <div class="col-auto">
        <span class="badge bg-dark">予約 {{ staff.summary.value.count }}件</span>
      </div>
      <div class="col-auto">
        <span class="badge bg-dark">総枚数 {{ staff.summary.value.total }}</span>
      </div>
      <div class="col-auto">
        <span class="badge bg-success">来場済み {{ staff.summary.value.checkedIn }}</span>
      </div>
      <div class="col-auto">
        <span class="badge bg-secondary">未来場 {{ staff.summary.value.notCheckedIn }}</span>
      </div>
      <div class="col-auto">
        <span class="badge bg-info text-dark">
          残席 {{ staff.summary.value.remaining === null ? '—' : staff.summary.value.remaining }}
        </span>
      </div>
      <div class="col-auto">
        <span class="badge bg-primary">売上概算 ¥{{ staff.summary.value.revenueEstimate.toLocaleString() }}</span>
      </div>
      <div class="col-auto" v-if="staff.summary.value.unpaid > 0">
        <span class="badge bg-warning text-dark">当日精算 {{ staff.summary.value.unpaid }}</span>
      </div>
    </div>

    <!-- 販売区分サマリ -->
    <div class="row g-1 mb-3">
      <div
        v-for="ch in SALES_CHANNELS"
        :key="ch.value"
        class="col-6 col-md-auto"
      >
        <span class="badge bg-light text-dark border">
          {{ ch.label }} {{ staff.summary.value.byChannel[ch.value] || 0 }}
        </span>
      </div>
    </div>

    <!-- ローディング -->
    <div v-if="staff.loading.value" class="text-center py-4">
      <div class="spinner-border spinner-border-sm" />
    </div>

    <!-- 予約一覧テーブル -->
    <div v-else-if="staff.reservations.value.length" class="table-responsive">
      <table class="table table-hover align-middle mb-0">
        <thead class="table-light">
          <tr>
            <th role="button" class="user-select-none" @click="toggleSort('name')">名前{{ sortArrow('name') }}</th>
            <th role="button" class="user-select-none" @click="toggleSort('date')">日程{{ sortArrow('date') }}</th>
            <th role="button" class="user-select-none" @click="toggleSort('seat')">席種{{ sortArrow('seat') }}</th>
            <th role="button" class="user-select-none" @click="toggleSort('channel')">区分{{ sortArrow('channel') }}</th>
            <th role="button" class="user-select-none" @click="toggleSort('type')">種別{{ sortArrow('type') }}</th>
            <th role="button" class="user-select-none" @click="toggleSort('status')">状態{{ sortArrow('status') }}</th>
            <th>メモ</th>
            <th class="text-end">操作</th>
          </tr>
        </thead>
        <tbody>
          <StaffReservationRow
            v-for="r in sortedReservations"
            :key="r.id"
            :reservation="r"
            @mark-paid="handleMarkPaid"
            @check-in="handleCheckIn"
            @cancel="handleCancel"
            @row-click="selectedReservation = $event"
          />
        </tbody>
      </table>
    </div>

    <!-- 検索結果なし -->
    <div v-else class="text-center py-4 text-muted">
      予約が見つかりません
    </div>
    </template>

    <!-- ===== 応募タブ ===== -->
    <template v-if="activeTab === 'applications'">
      <p class="small text-muted mb-3">
        二次先行応募の一覧です。当選ボタンで予約確定へ寄せます（在庫確認あり）。
      </p>

      <!-- 公演別 応募サマリーカード（左端に全公演合計） -->
      <PerformanceApplicationSummaryCards :summaries="staff.performanceSummaries.value">
        <template #leading>
          <TotalApplicationSummaryCard :summaries="staff.performanceSummaries.value" />
        </template>
      </PerformanceApplicationSummaryCards>

      <!-- FC会員フィルタ -->
      <div class="d-flex gap-2 mb-3">
        <button
          type="button"
          class="btn btn-sm"
          :class="staff.applicationsFanclubFilter.value === '' ? 'btn-dark' : 'btn-outline-secondary'"
          @click="staff.applicationsFanclubFilter.value = ''; staff.loadApplications()"
        >
          全員
        </button>
        <button
          type="button"
          class="btn btn-sm"
          :class="staff.applicationsFanclubFilter.value === 'true' ? 'btn-dark' : 'btn-outline-secondary'"
          @click="staff.applicationsFanclubFilter.value = 'true'; staff.loadApplications()"
        >
          FC会員のみ
        </button>
        <button
          type="button"
          class="btn btn-sm"
          :class="staff.applicationsFanclubFilter.value === 'false' ? 'btn-dark' : 'btn-outline-secondary'"
          @click="staff.applicationsFanclubFilter.value = 'false'; staff.loadApplications()"
        >
          非FC会員のみ
        </button>
      </div>
      <div v-if="staff.applicationsLoading.value" class="text-center py-4">
        <div class="spinner-border spinner-border-sm" />
      </div>
      <div v-else-if="staff.applications.value.length" class="table-responsive">
        <table class="table table-hover align-middle mb-0">
          <thead class="table-light">
            <tr>
              <th role="button" class="user-select-none" @click="appToggleSort('name')">応募者{{ appSortArrow('name') }}</th>
              <th role="button" class="user-select-none" @click="appToggleSort('seat')">希望席{{ appSortArrow('seat') }}</th>
              <th role="button" class="user-select-none" @click="appToggleSort('date')">公演{{ appSortArrow('date') }}</th>
              <th>備考</th>
              <th class="text-end">操作</th>
            </tr>
          </thead>
          <tbody>
            <StaffApplicationRow
              v-for="a in sortedApplications"
              :key="a.id"
              :application="a"
              :seat-tiers="staff.getSeatTiersFor(a.performance?.id)"
              @confirm="handleConfirmApplication"
              @reject="handleRejectApplication"
            />
          </tbody>
        </table>
      </div>
      <div v-else class="text-center py-4 text-muted">
        応募がありません
      </div>
    </template>

    <!-- 予約詳細モーダル -->
    <ReservationDetailModal
      :reservation="selectedReservation"
      @close="selectedReservation = null"
    />
  </div>
</template>
