"""
Minimal Paystack integration (https://paystack.com/docs).
Set PAYSTACK_SECRET_KEY in your environment / .env file.
"""
import requests
from django.conf import settings

PAYSTACK_BASE_URL = "https://api.paystack.co"


def _headers():
    return {
        "Authorization": f"Bearer {getattr(settings, 'PAYSTACK_SECRET_KEY', '')}",
        "Content-Type": "application/json",
    }


def initialize_transaction(email: str, amount_ghs, reference: str, callback_url: str) -> dict:
    """Amount must be converted to pesewas (amount * 100) per Paystack's API."""
    payload = {
        "email": email,
        "amount": int(float(amount_ghs) * 100),
        "reference": reference,
        "callback_url": callback_url,
        "currency": "GHS",
    }
    response = requests.post(f"{PAYSTACK_BASE_URL}/transaction/initialize",
                              json=payload, headers=_headers(), timeout=15)
    response.raise_for_status()
    return response.json()


def verify_transaction(reference: str) -> dict:
    response = requests.get(f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}",
                             headers=_headers(), timeout=15)
    response.raise_for_status()
    return response.json()
