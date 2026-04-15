from django.urls import path

from . import views

urlpatterns = [
    path("stripe/webhook/", views.stripe_webhook, name="stripe-webhook"),
    path("square/webhook/", views.square_webhook, name="square-webhook"),
]
