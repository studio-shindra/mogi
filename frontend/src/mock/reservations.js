// card 決済済み — チェックイン可能
export const mockReservationCard = {
  id: 1,
  token: 'abc123def456',
  guest_name: '山田太郎',
  guest_email: 'yamada@example.com',
  guest_phone: '090-1234-5678',
  performance: {
    id: 1,
    label: '5/21(金) 18:00 ソワレ',
    starts_at: '2026-05-21T18:00:00+09:00',
    event_title: 'パラダイスエフェクト〖第一回単独公演〗',
    venue_name: '新生館スタジオ',
  },
  seat_tier: { id: 2, name: '前方席', code: 'front' },
  quantity: 2,
  reservation_type: 'card',
  status: 'confirmed',
  payment_status: 'paid',
  checked_in: false,
  memo: '',
}

// cash 未払い
export const mockReservationCash = {
  id: 2,
  token: 'cash999xyz',
  guest_name: '佐藤花子',
  guest_email: '',
  guest_phone: '080-9876-5432',
  performance: {
    id: 1,
    label: '5/21(金) 18:00 ソワレ',
    starts_at: '2026-05-21T18:00:00+09:00',
    event_title: 'パラダイスエフェクト〖第一回単独公演〗',
    venue_name: '新生館スタジオ',
  },
  seat_tier: { id: 3, name: '中央席', code: 'center' },
  quantity: 1,
  reservation_type: 'cash',
  status: 'confirmed',
  payment_status: 'unpaid',
  checked_in: false,
  memo: '',
}

// チェックイン済み
export const mockReservationCheckedIn = {
  id: 3,
  token: 'checked111',
  guest_name: '鈴木一郎',
  guest_email: 'suzuki@example.com',
  guest_phone: '',
  performance: {
    id: 2,
    label: '5/22(土) 13:00 マチネ',
    starts_at: '2026-05-22T13:00:00+09:00',
    event_title: 'パラダイスエフェクト〖第一回単独公演〗',
    venue_name: '新生館スタジオ',
  },
  seat_tier: { id: 5, name: '最前席', code: 'front_row' },
  quantity: 1,
  reservation_type: 'card',
  status: 'confirmed',
  payment_status: 'paid',
  checked_in: true,
  memo: '',
}

// 招待
const mockReservationInvite = {
  id: 4,
  token: 'invite444',
  guest_name: '田中監督',
  guest_email: '',
  guest_phone: '',
  performance: {
    id: 1,
    label: '5/21(金) 18:00 ソワレ',
    starts_at: '2026-05-21T18:00:00+09:00',
    event_title: 'パラダイスエフェクト〖第一回単独公演〗',
    venue_name: '新生館スタジオ',
  },
  seat_tier: { id: 4, name: '後方席', code: 'rear' },
  quantity: 2,
  reservation_type: 'invite',
  status: 'confirmed',
  payment_status: 'paid',
  checked_in: false,
  memo: '関係者招待',
}

// card pending（Stripe 未決済）
const mockReservationPending = {
  id: 5,
  token: 'pending555',
  guest_name: '高橋次郎',
  guest_email: 'takahashi@example.com',
  guest_phone: '070-1111-2222',
  performance: {
    id: 1,
    label: '5/21(金) 18:00 ソワレ',
    starts_at: '2026-05-21T18:00:00+09:00',
    event_title: 'パラダイスエフェクト〖第一回単独公演〗',
    venue_name: '新生館スタジオ',
  },
  seat_tier: { id: 3, name: '中央席', code: 'center' },
  quantity: 1,
  reservation_type: 'card',
  status: 'pending',
  payment_status: 'unpaid',
  checked_in: false,
  memo: '',
}

// cash 支払い済み（入場待ち）
const mockReservationCashPaid = {
  id: 6,
  token: 'cashpaid666',
  guest_name: '渡辺美咲',
  guest_email: 'watanabe@example.com',
  guest_phone: '090-3333-4444',
  performance: {
    id: 2,
    label: '5/22(土) 13:00 マチネ',
    starts_at: '2026-05-22T13:00:00+09:00',
    event_title: 'パラダイスエフェクト〖第一回単独公演〗',
    venue_name: '新生館スタジオ',
  },
  seat_tier: { id: 6, name: '前方席', code: 'front' },
  quantity: 1,
  reservation_type: 'cash',
  status: 'confirmed',
  payment_status: 'paid',
  checked_in: false,
  memo: '',
}

// 全 mock 予約
export const mockAllReservations = [
  mockReservationCard,
  mockReservationCash,
  mockReservationCheckedIn,
  mockReservationInvite,
  mockReservationPending,
  mockReservationCashPaid,
]

// token → mock 引き当て用（確認ページ / チェックイン用）
export function findMockReservation(token) {
  const r = mockAllReservations.find((r) => r.token === token)
  if (!r) return mockReservationCard
  // 確認ページ用フィールドを補完
  return {
    ...r,
    can_self_checkin:
      !r.checked_in &&
      r.reservation_type !== 'cash' &&
      r.status === 'confirmed' &&
      r.payment_status === 'paid',
    checkin_opens_at: r.performance.starts_at.replace('T18:', 'T17:').replace('T13:', 'T12:'),
  }
}

// 受付検索用（公演フィルタ + テキスト検索）
export function searchMockReservations(performanceId, query) {
  let results = mockAllReservations
  if (performanceId) {
    results = results.filter((r) => r.performance.id === performanceId)
  }
  if (query) {
    const q = query.toLowerCase()
    results = results.filter(
      (r) =>
        r.guest_name.toLowerCase().includes(q) ||
        r.guest_email.toLowerCase().includes(q) ||
        r.guest_phone.includes(q) ||
        r.token.includes(q),
    )
  }
  return results
}

// mock 公演リスト（受付の公演フィルタ用）
export const mockPerformanceOptions = [
  { id: 1, label: '5/21(金) 18:00 ソワレ' },
  { id: 2, label: '5/22(土) 13:00 マチネ' },
  { id: 3, label: '5/22(土) 18:00 ソワレ' },
  { id: 4, label: '5/23(日) 13:00 マチネ' },
  { id: 5, label: '5/24(日) 18:00 ソワレ' },
]
