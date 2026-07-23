from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.request_otp, name="request_otp"),
    path("verify/", views.verify_otp, name="verify_otp"),
    path("resend/", views.resend_otp, name="resend_otp"),
    path("addresses/", views.address_list, name="address_list"),
    path("addresses/add/", views.address_create, name="address_create"),
    path("addresses/<int:pk>/edit/", views.address_edit, name="address_edit"),
    path("addresses/<int:pk>/delete/", views.address_delete, name="address_delete"),
    path("addresses/<int:pk>/set-default/", views.address_set_default, name="address_set_default"),
]
