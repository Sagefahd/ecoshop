import uuid

from django.db import models

from orders.models import Order


class Payment(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("successful", "Successful"),
        ("failed", "Failed"),
    ]
    METHOD_CHOICES = [
        ("nalo_mtn", "MTN Mobile Money (Nalo)"),
        ("nalo_vodafone", "Vodafone Cash (Nalo)"),
        ("nalo_airteltigo", "AirtelTigo Money (Nalo)"),
        ("cash_on_delivery", "Cash on Delivery"),
    ]
    NETWORK_BY_METHOD = {
        "nalo_mtn": "MTN",
        "nalo_vodafone": "VODAFONE",
        "nalo_airteltigo": "AIRTELTIGO",
    }

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    reference = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default="nalo_mtn")
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="pending")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    gateway_response = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reference} - {self.get_status_display()}"
