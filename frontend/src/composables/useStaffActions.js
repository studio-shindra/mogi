import { ref, computed } from 'vue'
import {
  staffSearchReservations,
  staffMarkPaid,
  staffCheckIn,
  staffWalkIn,
} from '../api/reservations.js'
import { fetchEvents, fetchEventDetail } from '../api/events.js'

export function useStaffActions() {
  const searchQuery = ref('')
  const selectedPerformanceId = ref(null)
  const reservations = ref([])
  const loading = ref(false)
  const performances = ref([])
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

  // --- 検索 ---
  async function search() {
    loading.value = true
    try {
      reservations.value = await staffSearchReservations(
        selectedPerformanceId.value,
        searchQuery.value,
      )
    } catch (e) {
      console.error('検索失敗:', e)
      reservations.value = []
    } finally {
      loading.value = false
    }
  }

  // --- 集計 ---
  const summary = computed(() => {
    const list = reservations.value
    const total = list.reduce((s, r) => s + r.quantity, 0)
    const checkedIn = list.filter((r) => r.checked_in).reduce((s, r) => s + r.quantity, 0)
    const unpaid = list
      .filter((r) => r.payment_status === 'unpaid' && r.status !== 'cancelled')
      .reduce((s, r) => s + r.quantity, 0)
    return { count: list.length, total, checkedIn, unpaid }
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
    } catch (e) {
      console.error('入場処理失敗:', e)
      setFlash('error', `入場処理に失敗しました: ${e.response?.data?.detail ?? e.message}`)
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
    reservations,
    loading,
    performances,
    eventDetail,
    flash,
    summary,
    loadPerformances,
    search,
    markPaid,
    checkIn,
    createWalkIn,
  }
}
