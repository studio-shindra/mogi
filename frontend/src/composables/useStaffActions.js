import { ref, computed } from 'vue'
import {
  staffSearchReservations,
  staffMarkPaid,
  staffCheckIn,
  staffWalkIn,
  staffCancel,
  staffListApplications,
  staffConfirmApplication,
  staffRejectApplication,
  staffPerformanceSummary,
} from '../api/reservations.js'
import { fetchEvents, fetchEventDetail } from '../api/events.js'

export const SALES_CHANNELS = [
  { value: 'advance', label: '先行' },
  { value: 'general', label: '一般' },
  { value: 'staff', label: '関係者' },
  { value: 'invite', label: '招待' },
  { value: 'hold', label: '取り置き' },
  { value: 'walk_in', label: '当日券' },
]

export function useStaffActions() {
  const searchQuery = ref('')
  const selectedPerformanceId = ref(null)
  const selectedSalesChannel = ref('')
  const reservations = ref([])
  const applications = ref([])
  const applicationsLoading = ref(false)
  const applicationsFanclubFilter = ref('')
  const loading = ref(false)
  const performances = ref([])
  const performanceSummaries = ref([])
  const eventDetail = ref(null)
  const flash = ref(null) // { type: 'success' | 'error', message: string }
  let flashTimer = null

  function setFlash(type, message) {
    flash.value = { type, message }
    clearTimeout(flashTimer)
    flashTimer = setTimeout(() => { flash.value = null }, 3000)
  }

  // --- 公演一覧取得 ---
  async function loadPerformances() {
    try {
      const events = await fetchEvents()
      if (!events.length) return
      const detail = await fetchEventDetail(events[0].slug)
      eventDetail.value = detail
      performances.value = detail.performances ?? []
    } catch (e) {
      console.error('公演取得失敗:', e)
    }
  }

  // --- 公演別サマリー取得（サーバ集計） ---
  async function loadPerformanceSummaries() {
    try {
      performanceSummaries.value = await staffPerformanceSummary()
    } catch (e) {
      console.error('公演別サマリー取得失敗:', e)
    }
  }

  // --- 検索 ---
  async function search() {
    loading.value = true
    try {
      reservations.value = await staffSearchReservations(
        selectedPerformanceId.value,
        searchQuery.value,
        selectedSalesChannel.value,
      )
    } catch (e) {
      console.error('検索失敗:', e)
      reservations.value = []
    } finally {
      loading.value = false
    }
  }

  // --- 集計 ---
  // 母集団: status !== 'cancelled'（applied は API 側で除外済み）
  const summary = computed(() => {
    const list = reservations.value.filter((r) => r.status !== 'cancelled')
    const total = list.reduce((s, r) => s + r.quantity, 0)
    const checkedIn = list.filter((r) => r.checked_in).reduce((s, r) => s + r.quantity, 0)
    const notCheckedIn = Math.max(total - checkedIn, 0)
    const unpaid = list
      .filter((r) => r.payment_status === 'unpaid')
      .reduce((s, r) => s + r.quantity, 0)

    // 残席: 公演を選択中のときのみ算出。未選択なら null（UI側で「—」表示）。
    let remaining = null
    if (selectedPerformanceId.value) {
      const perf = performances.value.find((p) => p.id === selectedPerformanceId.value)
      if (perf && Array.isArray(perf.seat_tiers)) {
        remaining = perf.seat_tiers.reduce(
          (s, t) => s + (typeof t.remaining === 'number' ? t.remaining : 0),
          0,
        )
      }
    }

    // 売上概算: 招待は0円、当日券は price_cash、それ以外は price_card
    const revenueEstimate = list.reduce((s, r) => {
      if (r.reservation_type === 'invite') return s
      const price = r.sales_channel === 'walk_in'
        ? (r.seat_tier?.price_cash ?? 0)
        : (r.seat_tier?.price_card ?? 0)
      return s + price * r.quantity
    }, 0)

    const byChannel = {}
    for (const ch of SALES_CHANNELS) byChannel[ch.value] = 0
    for (const r of list) {
      if (r.sales_channel && byChannel[r.sales_channel] !== undefined) {
        byChannel[r.sales_channel] += r.quantity
      }
    }
    return {
      count: list.length,
      total,
      checkedIn,
      notCheckedIn,
      remaining,
      revenueEstimate,
      unpaid,
      byChannel,
    }
  })

  // --- 現金受領 ---
  async function markPaid(reservation) {
    try {
      await staffMarkPaid(reservation.id)
      reservation.payment_status = 'paid'
      setFlash('success', `${reservation.guest_name} さんの現金受領を記録しました`)
    } catch (e) {
      console.error('現金受領失敗:', e)
      setFlash('error', `現金受領に失敗しました: ${e.response?.data?.detail ?? e.message}`)
    }
  }

  // --- 入場処理 ---
  async function checkIn(reservation) {
    try {
      await staffCheckIn(reservation.id)
      reservation.checked_in = true
      setFlash('success', `${reservation.guest_name} さんの入場を記録しました`)
      loadPerformanceSummaries()
    } catch (e) {
      console.error('入場処理失敗:', e)
      setFlash('error', `入場処理に失敗しました: ${e.response?.data?.detail ?? e.message}`)
    }
  }

  // --- 応募一覧 ---
  async function loadApplications() {
    applicationsLoading.value = true
    try {
      applications.value = await staffListApplications(
        selectedPerformanceId.value,
        searchQuery.value,
        applicationsFanclubFilter.value,
      )
    } catch (e) {
      console.error('応募一覧取得失敗:', e)
      applications.value = []
    } finally {
      applicationsLoading.value = false
    }
  }

  async function confirmApplication(application) {
    try {
      await staffConfirmApplication(application.id)
      applications.value = applications.value.filter((a) => a.id !== application.id)
      setFlash('success', `${application.guest_name} さんを当選処理しました`)
    } catch (e) {
      console.error('当選処理失敗:', e)
      setFlash('error', `当選処理に失敗しました: ${e.response?.data?.detail ?? e.message}`)
    }
  }

  async function rejectApplication(application) {
    try {
      await staffRejectApplication(application.id)
      applications.value = applications.value.filter((a) => a.id !== application.id)
      setFlash('success', `${application.guest_name} さんを落選処理しました`)
    } catch (e) {
      console.error('落選処理失敗:', e)
      setFlash('error', `落選処理に失敗しました: ${e.response?.data?.detail ?? e.message}`)
    }
  }

  // --- キャンセル ---
  async function cancel(reservation) {
    try {
      await staffCancel(reservation.id)
      reservation.status = 'cancelled'
      setFlash('success', `${reservation.guest_name} さんの予約をキャンセルしました`)
      loadPerformanceSummaries()
    } catch (e) {
      console.error('キャンセル失敗:', e)
      setFlash('error', `キャンセルに失敗しました: ${e.response?.data?.detail ?? e.message}`)
    }
  }

  // --- 当日券作成 ---
  async function createWalkIn(data) {
    try {
      const created = await staffWalkIn({
        performance_id: data.performanceId,
        seat_tier_id: data.seatTierId,
        quantity: data.quantity,
        guest_name: data.guestName,
        guest_phone: data.guestPhone || '',
        memo: data.memo || '',
      })
      reservations.value.unshift(created)
      setFlash('success', `${data.guestName} さんの当日券を登録しました`)
      loadPerformanceSummaries()
      return created
    } catch (e) {
      console.error('当日券登録失敗:', e)
      setFlash('error', `当日券登録に失敗しました: ${e.response?.data?.detail ?? e.message}`)
      throw e
    }
  }

  return {
    searchQuery,
    selectedPerformanceId,
    selectedSalesChannel,
    reservations,
    applications,
    applicationsLoading,
    applicationsFanclubFilter,
    loading,
    performances,
    performanceSummaries,
    eventDetail,
    flash,
    summary,
    loadPerformances,
    loadPerformanceSummaries,
    search,
    loadApplications,
    confirmApplication,
    rejectApplication,
    markPaid,
    checkIn,
    cancel,
    createWalkIn,
  }
}
