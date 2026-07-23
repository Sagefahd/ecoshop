from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, OTP, Address


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("username", "phone_number", "email", "is_vendor", "phone_verified", "is_staff")
    list_filter = ("is_vendor", "phone_verified", "is_staff")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("EcoShop", {"fields": ("phone_number", "phone_verified", "is_vendor")}),
    )


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "code", "purpose", "created_at", "expires_at", "is_used")
    list_filter = ("purpose", "is_used")
    search_fields = ("phone_number",)


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("user", "label", "full_name", "region", "city_town", "is_default")
    list_filter = ("region", "is_default")
    search_fields = ("full_name", "user__username", "phone_number")
