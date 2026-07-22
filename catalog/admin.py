from django.contrib import admin
from .models import Category, Vendor, Product, ProductImage, Promo


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ("store_name", "user", "whatsapp_number", "is_approved")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "vendor", "category", "price", "stock_quantity", "is_active")
    list_filter = ("category", "is_active", "vendor")
    search_fields = ("name", "sku")
    inlines = [ProductImageInline]


@admin.register(Promo)
class PromoAdmin(admin.ModelAdmin):
    list_display = ("name", "discount_type", "discount_value", "start_date", "end_date", "is_active")
    filter_horizontal = ("products",)
