from django.urls import path
from . import views

app_name = "vendor"

urlpatterns = [
    path("", views.dashboard_home, name="dashboard_home"),

    path("orders/", views.order_checklist, name="order_checklist"),
    path("orders/<str:order_id>/", views.order_detail, name="order_detail"),

    path("payments/", views.payments_tab, name="payments_tab"),
    path("analytics/", views.analytics, name="analytics"),
    path("customers/", views.customer_list, name="customer_list"),

    path("products/", views.product_list, name="product_list"),
    path("products/new/", views.product_create, name="product_create"),
    path("products/<int:pk>/edit/", views.product_edit, name="product_edit"),
    path("products/<int:pk>/delete/", views.product_delete, name="product_delete"),
    path("products/<int:pk>/toggle/", views.product_toggle_active, name="product_toggle_active"),

    path("categories/", views.category_list, name="category_list"),
    path("categories/new/", views.category_create, name="category_create"),
    path("categories/<int:pk>/edit/", views.category_edit, name="category_edit"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"),

    path("promos/", views.promo_list, name="promo_list"),
    path("promos/new/", views.promo_create, name="promo_create"),
    path("promos/<int:pk>/edit/", views.promo_edit, name="promo_edit"),
    path("promos/<int:pk>/delete/", views.promo_delete, name="promo_delete"),
]
