<script setup>
import { onMounted, ref } from 'vue'
import { useStaffActions } from '../composables/useStaffActions.js'
import StaffSearchBar from '../components/staff/StaffSearchBar.vue'
import StaffReservationRow from '../components/staff/StaffReservationRow.vue'
import WalkInForm from '../components/staff/WalkInForm.vue'

const staff = useStaffActions()

const showWalkIn = ref(false)

onMounted(async () => {
  await staff.loadPerformances()
  staff.search()
})

async function handleMarkPaid(reservation) {
  await staff.markPaid(reservation)
}

async function handleCheckIn(reservation) {
  await staff.checkIn(reservation)
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
      <button
        class="btn btn-sm btn-outline-dark"
        @click="showWalkIn = !showWalkIn"
      >
        {{ showWalkIn ? '閉じる' : '当日券登録' }}
      </button>
    </div>

    <!-- フラッシュメッセージ -->
    <div
      v-if="staff.flash.value"
      class="alert alert-sm py-2 px-3 mb-3"
      :class="staff.flash.value.type === 'success' ? 'alert-success' : 'alert-danger'"
      role="alert"
    >
      {{ staff.flash.value.message }}
    </div>

    <!-- 当日券登録フォーム -->
    <div v-if="showWalkIn" class="card mb-3">
      <div class="card-body">
        <h6 class="card-title mb-3">当日券登録</h6>
        <WalkInForm :performances="staff.performances.value" @created="handleWalkIn" />
      </div>
    </div>

    <!-- 検索バー -->
    <StaffSearchBar
      :search-query="staff.searchQuery.value"
      :selected-performance-id="staff.selectedPerformanceId.value"
      :performances="staff.performances.value"
      @update:search-query="(v) => (staff.searchQuery.value = v)"
      @update:selected-performance-id="(v) => (staff.selectedPerformanceId.value = v)"
      @search="staff.search()"
    />

    <!-- 集計 -->
    <div class="row g-2 mb-3">
      <div class="col-auto">
        <span class="badge bg-dark">{{ staff.summary.value.count }}件 / {{ staff.summary.value.total }}枚</span>
      </div>
      <div class="col-auto">
        <span class="badge bg-success">入場 {{ staff.summary.value.checkedIn }}</span>
      </div>
      <div class="col-auto" v-if="staff.summary.value.unpaid > 0">
        <span class="badge bg-danger">未払い {{ staff.summary.value.unpaid }}</span>
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
            <th>名前</th>
            <th>席種</th>
            <th>種別</th>
            <th>状態</th>
            <th>メモ</th>
            <th class="text-end">操作</th>
          </tr>
        </thead>
        <tbody>
          <StaffReservationRow
            v-for="r in staff.reservations.value"
            :key="r.id"
            :reservation="r"
            @mark-paid="handleMarkPaid"
            @check-in="handleCheckIn"
          />
        </tbody>
      </table>
    </div>

    <!-- 検索結果なし -->
    <div v-else class="text-center py-4 text-muted">
      予約が見つかりません
    </div>
  </div>
</template>
