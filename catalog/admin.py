from django.contrib import admin
from .models import Category, Product, ProductImage, Promo


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "stock_quantity", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("name", "sku")
    inlines = [ProductImageInline]


@admin.register(Promo)
class PromoAdmin(admin.ModelAdmin):
    list_display = ("name", "discount_type", "discount_value", "start_date", "end_date", "is_active")
    filter_horizontal = ("products",)
