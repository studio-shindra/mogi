import client from './client.js'
import { mockEvents, mockEventDetail } from '../mock/events.js'

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

export async function fetchEvents() {
  if (USE_MOCK) return mockEvents
  const { data } = await client.get('/events/')
  return data.results ?? data
}

export async function fetchEventDetail(slug) {
  if (USE_MOCK) return mockEventDetail
  const { data } = await client.get(`/events/${slug}/`)
  return data
}
