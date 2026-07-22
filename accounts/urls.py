from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.request_otp, name="request_otp"),
    path("verify/", views.verify_otp, name="verify_otp"),
    path("resend/", views.resend_otp, name="resend_otp"),
    path("addresses/", views.address_list, name="address_list"),
    path("addresses/<str:address_type>/", views.address_edit, name="address_edit"),
]
