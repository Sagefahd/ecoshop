from decimal import Decimal

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Vendor(models.Model):
    """A seller/store. Kept separate from User so one account could manage a store profile."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vendor_profile")
    store_name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    logo = models.ImageField(upload_to="vendors/", blank=True, null=True)
    whatsapp_number = models.CharField(max_length=15, blank=True,
                                        help_text="233XXXXXXXXX - shown to customers for support")
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.store_name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.store_name


class Product(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="products")
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    sku = models.CharField(max_length=50, unique=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Actual price in GHS")
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    thumbnail = models.ImageField(upload_to="products/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["name"])]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            self.slug = base_slug
            counter = 1
            while Product.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                counter += 1
                self.slug = f"{base_slug}-{counter}"
        if not self.sku:
            self.sku = f"SKU-{slugify(self.name)[:8].upper()}-{Product.objects.count() + 1}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def active_promo(self):
        now = timezone.now()
        return self.promos.filter(is_active=True, start_date__lte=now, end_date__gte=now).first()

    @property
    def display_price(self) -> Decimal:
        """Price after promo discount, if any."""
        promo = self.active_promo
        if promo:
            return promo.discounted_price(self.price)
        return self.price

    @property
    def in_stock(self):
        return self.stock_quantity > 0

    def get_absolute_url(self):
        return reverse("catalog:product_detail", kwargs={"slug": self.slug})


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/gallery/")
    alt_text = models.CharField(max_length=150, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order"]


class Promo(models.Model):
    """A promo/discount that can apply to one or more products."""
    DISCOUNT_TYPE = [
        ("percentage", "Percentage off"),
        ("flat", "Flat amount off (GHS)"),
    ]

    name = models.CharField(max_length=120)
    products = models.ManyToManyField(Product, related_name="promos")
    discount_type = models.CharField(max_length=12, choices=DISCOUNT_TYPE, default="percentage")
    discount_value = models.DecimalField(max_digits=8, decimal_places=2,
                                          help_text="e.g. 15 for 15% or 15 for GHS 15 off")
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def discounted_price(self, original_price: Decimal) -> Decimal:
        if self.discount_type == "percentage":
            discount = original_price * (self.discount_value / Decimal("100"))
        else:
            discount = self.discount_value
        result = original_price - discount
        return max(result, Decimal("0.00"))

    def __str__(self):
        return f"{self.name} ({self.discount_value}{'%' if self.discount_type == 'percentage' else ' GHS'})"
