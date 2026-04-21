import client from './client.js'

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

export async function fetchLink(token) {
  if (USE_MOCK) {
    return {
      token,
      mode: 'reservation',
      sales_channel: 'advance',
      label: 'mock link',
      header_image_url: '',
      is_active: true,
      event: {
        id: 1,
        slug: 'mock',
        title: 'mock event',
        venue_name: 'mock venue',
        flyer_image_url: '',
        performances: [
          {
            id: 1,
            label: 'mock公演',
            starts_at: new Date().toISOString(),
            open_at: new Date().toISOString(),
            seat_tiers: [],
          },
        ],
      },
    }
  }
  const { data } = await client.get(`/links/${token}/`)
  return data
}
