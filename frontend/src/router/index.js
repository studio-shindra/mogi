import { createRouter, createWebHistory } from 'vue-router'
import client from '../api/client.js'

const routes = [
  {
    path: '/',
    name: 'event-list',
    component: () => import('../views/EventListView.vue'),
  },
  {
    path: '/myticket',
    name: 'my-ticket',
    component: () => import('../views/MyTicketView.vue'),
  },
  {
    path: '/manage/login',
    name: 'manage-login',
    component: () => import('../views/ManageLoginView.vue'),
  },
  {
    path: '/manage',
    name: 'manage-dashboard',
    component: () => import('../views/StaffDashboardView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/manage/sales',
    name: 'manage-sales',
    component: () => import('../views/ManageSalesView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/manage/booking',
    name: 'manage-booking',
    component: () => import('../views/StaffBookingView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/reservation/:token',
    name: 'reservation-confirm',
    component: () => import('../views/ReservationConfirmView.vue'),
    props: true,
  },
  {
    path: '/reservation/:token/checkin',
    name: 'checkin',
    redirect: (to) => ({
      name: 'reservation-confirm',
      params: { token: to.params.token },
    }),
  },
  {
    path: '/:slug',
    name: 'event-detail',
    component: () => import('../views/EventDetailView.vue'),
    props: true,
  },
  {
    path: '/:slug/reserve/:performanceId',
    name: 'reserve',
    component: () => import('../views/ReserveView.vue'),
    props: true,
  },
  {
    path: '/apply/:slug/:performanceId',
    name: 'apply',
    component: () => import('../views/ApplyView.vue'),
    props: true,
  },
  {
    path: '/r/:token',
    name: 'link-entry',
    component: () => import('../views/LinkEntryView.vue'),
    props: true,
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('../views/NotFoundView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  if (!to.meta.requiresAuth) return true

  try {
    const res = await client.get('/auth/me/')
    if (res.data?.is_staff) return true
    return { name: 'manage-login', query: { next: to.fullPath } }
  } catch (e) {
    if (e.response?.status === 401 || e.response?.status === 403) {
      return { name: 'manage-login', query: { next: to.fullPath } }
    }
    return true
  }
})

export default router
