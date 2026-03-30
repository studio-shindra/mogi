export const mockEventDetail = {
  id: 1,
  title: 'パラダイスエフェクト〖第一回単独公演〗',
  slug: 'paradise-effect',
  description:
    'コヤナギシンが語り紡ぐ、楽園へ向かうための小さな羽ばたき。' +
    '『ギャンブラーズ』『カギ』『世界にアンチ！』『売れ残り』の' +
    '４本からなるオムニバス短編集。',
  venue_name: '新生館スタジオ',
  venue_address: '東京都板橋区中板橋19-6 ダイアパレス中板橋B1',
  cast: 'コヤナギシン',
  performances: [
    {
      id: 1,
      label: '5/21(金) 18:00 ソワレ',
      starts_at: '2026-05-21T18:00:00+09:00',
      open_at: '2026-05-21T17:30:00+09:00',
      seat_tiers: [
        { id: 1, code: 'front_row', name: '最前席', capacity: 6, price_card: 4000, price_cash: 4500, sort_order: 0, remaining: 4 },
        { id: 2, code: 'front', name: '前方席', capacity: 12, price_card: 3500, price_cash: 4000, sort_order: 1, remaining: 8 },
        { id: 3, code: 'center', name: '中央席', capacity: 20, price_card: 3000, price_cash: 3500, sort_order: 2, remaining: 15 },
        { id: 4, code: 'rear', name: '後方席', capacity: 16, price_card: 2500, price_cash: 3000, sort_order: 3, remaining: 12 },
      ],
    },
    {
      id: 2,
      label: '5/22(土) 13:00 マチネ',
      starts_at: '2026-05-22T13:00:00+09:00',
      open_at: '2026-05-22T12:30:00+09:00',
      seat_tiers: [
        { id: 5, code: 'front_row', name: '最前席', capacity: 6, price_card: 4000, price_cash: 4500, sort_order: 0, remaining: 6 },
        { id: 6, code: 'front', name: '前方席', capacity: 12, price_card: 3500, price_cash: 4000, sort_order: 1, remaining: 12 },
        { id: 7, code: 'center', name: '中央席', capacity: 20, price_card: 3000, price_cash: 3500, sort_order: 2, remaining: 20 },
        { id: 8, code: 'rear', name: '後方席', capacity: 16, price_card: 2500, price_cash: 3000, sort_order: 3, remaining: 16 },
      ],
    },
    {
      id: 3,
      label: '5/22(土) 18:00 ソワレ',
      starts_at: '2026-05-22T18:00:00+09:00',
      open_at: '2026-05-22T17:30:00+09:00',
      seat_tiers: [
        { id: 9, code: 'front_row', name: '最前席', capacity: 6, price_card: 4000, price_cash: 4500, sort_order: 0, remaining: 3 },
        { id: 10, code: 'front', name: '前方席', capacity: 12, price_card: 3500, price_cash: 4000, sort_order: 1, remaining: 5 },
        { id: 11, code: 'center', name: '中央席', capacity: 20, price_card: 3000, price_cash: 3500, sort_order: 2, remaining: 10 },
        { id: 12, code: 'rear', name: '後方席', capacity: 16, price_card: 2500, price_cash: 3000, sort_order: 3, remaining: 14 },
      ],
    },
    {
      id: 4,
      label: '5/23(日) 13:00 マチネ',
      starts_at: '2026-05-23T13:00:00+09:00',
      open_at: '2026-05-23T12:30:00+09:00',
      seat_tiers: [
        { id: 13, code: 'front_row', name: '最前席', capacity: 6, price_card: 4000, price_cash: 4500, sort_order: 0, remaining: 6 },
        { id: 14, code: 'front', name: '前方席', capacity: 12, price_card: 3500, price_cash: 4000, sort_order: 1, remaining: 10 },
        { id: 15, code: 'center', name: '中央席', capacity: 20, price_card: 3000, price_cash: 3500, sort_order: 2, remaining: 18 },
        { id: 16, code: 'rear', name: '後方席', capacity: 16, price_card: 2500, price_cash: 3000, sort_order: 3, remaining: 16 },
      ],
    },
    {
      id: 5,
      label: '5/24(日) 18:00 ソワレ',
      starts_at: '2026-05-24T18:00:00+09:00',
      open_at: '2026-05-24T17:30:00+09:00',
      seat_tiers: [
        { id: 17, code: 'front_row', name: '最前席', capacity: 6, price_card: 4000, price_cash: 4500, sort_order: 0, remaining: 2 },
        { id: 18, code: 'front', name: '前方席', capacity: 12, price_card: 3500, price_cash: 4000, sort_order: 1, remaining: 7 },
        { id: 19, code: 'center', name: '中央席', capacity: 20, price_card: 3000, price_cash: 3500, sort_order: 2, remaining: 12 },
        { id: 20, code: 'rear', name: '後方席', capacity: 16, price_card: 2500, price_cash: 3000, sort_order: 3, remaining: 9 },
      ],
    },
  ],
}

export const mockEvents = [
  { id: 1, title: mockEventDetail.title, slug: mockEventDetail.slug },
]
