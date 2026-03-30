import { createRouter, createWebHistory } from 'vue-router'

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
    path: '/staff',
    name: 'staff-dashboard',
    component: () => import('../views/StaffDashboardView.vue'),
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
    component: () => import('../views/CheckinView.vue'),
    props: true,
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
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('../views/NotFoundView.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
