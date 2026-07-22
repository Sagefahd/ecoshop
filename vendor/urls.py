from django.urls import path
from . import views

app_name = "vendor"

urlpatterns = [
    path("", views.dashboard_home, name="dashboard_home"),
    path("orders/", views.order_checklist, name="order_checklist"),
    path("orders/<str:order_id>/", views.order_detail, name="order_detail"),
    path("payments/", views.payments_tab, name="payments_tab"),
    path("analytics/", views.analytics, name="analytics"),
    path("products/", views.product_list, name="product_list"),
    path("products/new/", views.product_create, name="product_create"),
    path("products/<int:pk>/edit/", views.product_edit, name="product_edit"),
    path("products/<int:pk>/delete/", views.product_delete, name="product_delete"),
    path("products/<int:pk>/toggle/", views.product_toggle_active, name="product_toggle_active"),
    path("promos/", views.promo_list, name="promo_list"),
]
