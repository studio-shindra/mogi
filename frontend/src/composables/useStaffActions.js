import { ref, computed } from 'vue'
import {
  staffSearchReservations,
  staffMarkPaid,
  staffCheckIn,
  staffWalkIn,
} from '../api/reservations.js'

export function useStaffActions() {
  const searchQuery = ref('')
  const selectedPerformanceId = ref(null)
  const reservations = ref([])
  const loading = ref(false)

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
    await staffMarkPaid(reservation.id)
    reservation.payment_status = 'paid'
  }

  // --- 入場処理 ---
  async function checkIn(reservation) {
    await staffCheckIn(reservation.id)
    reservation.checked_in = true
  }

  // --- 当日券作成 ---
  async function createWalkIn(data) {
    const created = await staffWalkIn({
      performance_id: data.performanceId,
      seat_tier_id: data.seatTierId,
      quantity: data.quantity,
      guest_name: data.guestName,
      guest_phone: data.guestPhone || '',
      memo: data.memo || '',
    })
    reservations.value.unshift(created)
    return created
  }

  return {
    searchQuery,
    selectedPerformanceId,
    reservations,
    loading,
    summary,
    search,
    markPaid,
    checkIn,
    createWalkIn,
  }
}
