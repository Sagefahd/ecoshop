"""
SMS OTP delivery via Arkesel (https://arkesel.com).
Set ARKESEL_API_KEY and ARKESEL_SENDER_ID in your environment / .env file.

In DEBUG mode, if no API key is configured, OTPs are just printed to the
console so you can develop without an Arkesel account.
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

ARKESEL_SMS_URL = "https://sms.arkesel.com/api/v2/sms/send"


def send_otp_sms(phone_number: str, code: str) -> bool:
    message = f"Your EcoShop verification code is {code}. It expires in 5 minutes. Do not share this code."

    api_key = getattr(settings, "ARKESEL_API_KEY", "")
    if not api_key:
        # Dev fallback: log instead of sending, so local dev doesn't need a real account.
        logger.warning("[DEV OTP] No ARKESEL_API_KEY set. OTP for %s is %s", phone_number, code)
        print(f"[DEV OTP] {phone_number}: {code}")
        return True

    payload = {
        "sender": getattr(settings, "ARKESEL_SENDER_ID", "EcoShop"),
        "message": message,
        "recipients": [phone_number],
    }
    headers = {"api-key": api_key, "Content-Type": "application/json"}

    try:
        response = requests.post(ARKESEL_SMS_URL, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("code") == "ok"
    except requests.RequestException:
        logger.exception("Failed to send OTP SMS to %s", phone_number)
        return False
