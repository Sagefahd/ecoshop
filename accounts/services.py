"""
SMS OTP delivery via Nalo Solutions (https://nalosolutions.com), using the
`nunyakata` client library. Set NALO_SMS_USERNAME, NALO_SMS_PASSWORD, and
NALO_SMS_SENDER_ID in your environment / .env file.

In DEBUG mode, if no Nalo credentials are configured, OTPs are just printed
to the console so you can develop without a Nalo account.
"""
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def _nalo_client():
    from nunyakata import NaloSolutions

    return NaloSolutions(
        sms_username=getattr(settings, "NALO_SMS_USERNAME", ""),
        sms_password=getattr(settings, "NALO_SMS_PASSWORD", ""),
        sms_sender_id=getattr(settings, "NALO_SMS_SENDER_ID", "EcoShop"),
    )


def send_otp_sms(phone_number: str, code: str) -> bool:
    message = f"Your EcoShop verification code is {code}. It expires in 5 minutes. Do not share this code."

    username = getattr(settings, "NALO_SMS_USERNAME", "")
    if not username:
        # Dev fallback: log instead of sending, so local dev doesn't need a real Nalo account.
        logger.warning("[DEV OTP] No NALO_SMS_USERNAME set. OTP for %s is %s", phone_number, code)
        print(f"[DEV OTP] {phone_number}: {code}")
        return True

    try:
        client = _nalo_client()
        response = client.send_sms(phone_number=phone_number, message=message)
        return response.get("status") == "success"
    except Exception:
        logger.exception("Failed to send OTP SMS to %s via Nalo", phone_number)
        return False
