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

// ---- Staff ----

export async function staffSearchReservations(performanceId, search, salesChannel) {
  if (USE_MOCK) return searchMockReservations(performanceId, search)
  const params = {}
  if (performanceId) params.performance = performanceId
  if (search) params.search = search
  if (salesChannel) params.sales_channel = salesChannel
  const { data } = await client.get('/staff/reservations/', { params })
  return data.results
}

export async function staffCancel(reservationId) {
  if (USE_MOCK) return { id: reservationId, status: 'cancelled' }
  const { data } = await client.post(`/staff/reservations/${reservationId}/cancel/`)
  return data
}

// ---- Applications（二次先行応募） ----

export async function createApplication(payload) {
  if (USE_MOCK) {
    console.log('mock createApplication', payload)
    return { id: 998, token: 'mock-app-998' }
  }
  const { data } = await client.post('/applications/', payload)
  return data
}

export async function staffListApplications(performanceId, search, fanclub) {
  if (USE_MOCK) return []
  const params = {}
  if (performanceId) params.performance = performanceId
  if (search) params.search = search
  if (fanclub) params.fanclub = fanclub
  const { data } = await client.get('/staff/applications/', { params })
  return data.results
}

export async function staffConfirmApplication(reservationId, assignedSeatTierId) {
  if (USE_MOCK) return { id: reservationId, status: 'confirmed' }
  const { data } = await client.post(`/staff/applications/${reservationId}/confirm/`, {
    assigned_seat_tier_id: assignedSeatTierId,
  })
  return data
}

export async function staffRejectApplication(reservationId) {
  if (USE_MOCK) return { id: reservationId, status: 'cancelled' }
  const { data } = await client.post(`/staff/applications/${reservationId}/reject/`)
  return data
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

export async function staffPerformanceSummary() {
  if (USE_MOCK) return []
  const { data } = await client.get('/staff/performance-summary/')
  return data.results
}
