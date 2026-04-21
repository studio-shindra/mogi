from django.urls import path

from . import views

urlpatterns = [
    # Auth (管理画面ログイン)
    path("auth/login/", views.auth_login, name="auth-login"),
    path("auth/logout/", views.auth_logout, name="auth-logout"),
    path("auth/me/", views.auth_me, name="auth-me"),
    # Public (認証不要)
    path("reservations/", views.reservation_create, name="reservation-create"),
    path("reservations/<str:token>/", views.reservation_by_token, name="reservation-detail"),
    path("reservations/<str:token>/complete/", views.reservation_complete, name="reservation-complete"),
    path("reservations/<str:token>/checkin/", views.reservation_checkin, name="reservation-checkin"),
    path("reservations/<str:token>/checkout/", views.reservation_checkout, name="reservation-checkout"),
    # Staff (認証必須)
    path("staff/reservations/", views.staff_reservation_list, name="staff-reservation-list"),
    path("staff/reservations/walk-in/", views.staff_walk_in, name="staff-walk-in"),
    path("staff/performance-summary/", views.staff_performance_summary, name="staff-performance-summary"),
    path("staff/reservations/<int:pk>/mark-paid/", views.staff_mark_paid, name="staff-mark-paid"),
    path("staff/reservations/<int:pk>/check-in/", views.staff_check_in, name="staff-check-in"),
    path("staff/reservations/<int:pk>/cancel/", views.staff_cancel, name="staff-cancel"),
    # Applications（二次先行応募）
    path("applications/", views.application_create, name="application-create"),
    path("staff/applications/", views.staff_application_list, name="staff-application-list"),
    path("staff/applications/<int:pk>/confirm/", views.staff_application_confirm, name="staff-application-confirm"),
    path("staff/applications/<int:pk>/reject/", views.staff_application_reject, name="staff-application-reject"),
    # AccessLink（限定URL）
    path("links/<str:token>/", views.link_detail, name="link-detail"),
]
