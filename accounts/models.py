import random
from datetime import timedelta

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from .regions import GHANA_REGIONS


class User(AbstractUser):
    """
    Custom user. Phone number is the primary login credential (used for OTP),
    but we keep username/email for Google/Apple social login compatibility.
    """
    phone_number = models.CharField(max_length=15, unique=True, null=True, blank=True,
                                     help_text="Format: 233XXXXXXXXX")
    phone_verified = models.BooleanField(default=False)
    is_vendor = models.BooleanField(default=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.phone_number or self.username or self.email


class OTP(models.Model):
    """One-time passcode for phone authentication."""
    PURPOSE_CHOICES = [
        ("login", "Login/Signup"),
        ("verify", "Verify Phone"),
    ]

    phone_number = models.CharField(max_length=15, db_index=True)
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=10, choices=PURPOSE_CHOICES, default="login")
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    @classmethod
    def generate(cls, phone_number, purpose="login", ttl_minutes=5):
        code = f"{random.randint(0, 999999):06d}"
        return cls.objects.create(
            phone_number=phone_number,
            code=code,
            purpose=purpose,
            expires_at=timezone.now() + timedelta(minutes=ttl_minutes),
        )

    def is_valid(self):
        return not self.is_used and timezone.now() <= self.expires_at and self.attempts < 5

    def __str__(self):
        return f"{self.phone_number} - {self.code} ({self.purpose})"


class Address(models.Model):
    """
    A flexible address book: a user can save any number of addresses
    (home, office, a relative's place, etc.), give each a short label, and
    mark one as the default used to pre-fill checkout.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField(max_length=40, blank=True,
                              help_text="Optional short label, e.g. 'Home', 'Office'")
    full_name = models.CharField(max_length=120)
    phone_number = models.CharField(max_length=15, help_text="Active phone number for this address")
    region = models.CharField(max_length=30, choices=GHANA_REGIONS)
    city_town = models.CharField(max_length=120)
    street_address = models.CharField(max_length=255)
    digital_address = models.CharField(max_length=20, blank=True, help_text="Ghana Post GPS (optional)")
    landmark = models.CharField(max_length=255, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_default", "-created_at"]
        verbose_name_plural = "Addresses"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_default:
            # Only one default per user — unset any others.
            Address.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        elif not Address.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).exists():
            # Every user needs exactly one default once they have any address.
            Address.objects.filter(pk=self.pk).update(is_default=True)

    def __str__(self):
        label = self.label or self.get_region_display()
        return f"{label} - {self.full_name} ({self.get_region_display()})"
