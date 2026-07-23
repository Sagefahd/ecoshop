from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("initiate/<str:order_id>/", views.initiate_payment, name="initiate"),
    path("pending/<str:reference>/", views.payment_pending, name="pending"),
    path("status/<str:reference>/", views.payment_status, name="status"),
    path("callback/", views.payment_callback, name="callback"),
]
