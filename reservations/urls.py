from django.urls import path

from . import views

urlpatterns = [
    # Public (認証不要)
    path("reservations/", views.reservation_create, name="reservation-create"),
    path("reservations/<str:token>/", views.reservation_by_token, name="reservation-detail"),
    path("reservations/<str:token>/checkin/", views.reservation_checkin, name="reservation-checkin"),
    path("reservations/<str:token>/checkout/", views.reservation_checkout, name="reservation-checkout"),
    # Staff (認証必須)
    path("staff/reservations/", views.staff_reservation_list, name="staff-reservation-list"),
    path("staff/reservations/walk-in/", views.staff_walk_in, name="staff-walk-in"),
    path("staff/reservations/<int:pk>/mark-paid/", views.staff_mark_paid, name="staff-mark-paid"),
    path("staff/reservations/<int:pk>/check-in/", views.staff_check_in, name="staff-check-in"),
]
