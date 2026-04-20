import client from './client.js'

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

export async function fetchLink(token) {
  if (USE_MOCK) {
    return {
      token,
      mode: 'reservation',
      sales_channel: 'advance',
      label: 'mock link',
      is_active: true,
      performance: {
        id: 1,
        label: 'mock公演',
        starts_at: new Date().toISOString(),
        open_at: new Date().toISOString(),
        event_slug: 'mock',
        event_title: 'mock event',
        venue_name: 'mock venue',
        seat_tiers: [],
      },
    }
  }
  const { data } = await client.get(`/links/${token}/`)
  return data
}
