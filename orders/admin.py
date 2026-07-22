from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product_name", "unit_price", "quantity")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_id", "user", "status", "total", "total_quantity", "created_at")
    list_filter = ("status",)
    search_fields = ("order_id", "user__username", "user__phone_number")
    inlines = [OrderItemInline]
    readonly_fields = ("order_id", "subtotal", "total", "created_at", "updated_at")


admin.site.register(Cart)
admin.site.register(CartItem)
