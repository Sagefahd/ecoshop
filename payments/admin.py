from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("reference", "order", "method", "status", "amount", "created_at")
    list_filter = ("status", "method")
    search_fields = ("reference", "order__order_id")
