import client from './client.js'
import { findMockReservation, searchMockReservations } from '../mock/reservations.js'

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

// ---- Public ----

export async function createReservation(payload) {
  if (USE_MOCK) {
    console.log('mock createReservation', payload)
    return { id: 999, token: 'mock-token-999' }
  }
  const { data } = await client.post('/reservations/', payload)
  return data
}

export async function fetchReservation(token) {
  if (USE_MOCK) return findMockReservation(token)
  const { data } = await client.get(`/reservations/${token}/`)
  return data
}

export async function checkin(token) {
  if (USE_MOCK) return { checked_in: true, checked_in_at: new Date().toISOString() }
  const { data } = await client.post(`/reservations/${token}/checkin/`)
  return data
}

export async function completeReservation(token, payload) {
  if (USE_MOCK) {
    console.log('mock completeReservation', token, payload)
    return { status: 'pending', reservation_type: payload.reservation_type }
  }
  const { data } = await client.post(`/reservations/${token}/complete/`, payload)
  return data
}

export async function startCheckout(token) {
  if (USE_MOCK) {
    console.log('mock startCheckout', token)
    return { checkout_url: 'https://checkout.stripe.com/mock' }
  }
  const { data } = await client.post(`/reservations/${token}/checkout/`)
  return data
}

// ---- Staff ----

export async function staffSearchReservations(performanceId, search) {
  if (USE_MOCK) return searchMockReservations(performanceId, search)
  const params = {}
  if (performanceId) params.performance = performanceId
  if (search) params.search = search
  const { data } = await client.get('/staff/reservations/', { params })
  return data.results
}

export async function staffMarkPaid(reservationId) {
  if (USE_MOCK) return { id: reservationId, payment_status: 'paid' }
  const { data } = await client.post(`/staff/reservations/${reservationId}/mark-paid/`)
  return data
}

export async function staffCheckIn(reservationId) {
  if (USE_MOCK) return { id: reservationId, checked_in: true }
  const { data } = await client.post(`/staff/reservations/${reservationId}/check-in/`)
  return data
}

export async function staffWalkIn(payload) {
  if (USE_MOCK) {
    console.log('mock staffWalkIn', payload)
    return { id: Date.now(), token: 'mock-walkin', ...payload }
  }
  const { data } = await client.post('/staff/reservations/walk-in/', payload)
  return data
}
