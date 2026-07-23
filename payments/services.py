"""
Mobile Money payment via Nalo Solutions (https://nalosolutions.com), using the
`nunyakata` client library. Set NALO_PAYMENT_USERNAME, NALO_PAYMENT_PASSWORD,
and NALO_MERCHANT_ID in your environment / .env file.

Unlike Paystack's redirect-based checkout, Nalo pushes a MoMo prompt directly
to the customer's phone (they approve with their MoMo PIN) and then POSTs the
result to our callback_url — there's no authorization_url to redirect to.
"""
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

NETWORK_CHOICES = ["MTN", "VODAFONE", "AIRTELTIGO"]


def _nalo_client():
    from nunyakata import NaloSolutions

    return NaloSolutions(
        payment_username=getattr(settings, "NALO_PAYMENT_USERNAME", ""),
        payment_password=getattr(settings, "NALO_PAYMENT_PASSWORD", ""),
        payment_merchant_id=getattr(settings, "NALO_MERCHANT_ID", ""),
    )


def request_momo_payment(*, amount, phone_number: str, customer_name: str,
                          order_id: str, network: str, callback_url: str) -> dict:
    """
    Triggers a Mobile Money prompt on the customer's phone. Returns Nalo's
    immediate acknowledgement (not the final payment result — that arrives
    later via the callback).
    """
    if not getattr(settings, "NALO_PAYMENT_USERNAME", ""):
        # Dev fallback: no real Nalo account configured.
        logger.warning("[DEV PAYMENT] No NALO_PAYMENT_USERNAME set. Simulating request for order %s", order_id)
        print(f"[DEV PAYMENT] MoMo request for order {order_id}: GHS {amount} to {phone_number} via {network}")
        return {"status": "sent"}

    client = _nalo_client()
    return client.make_payment(
        amount=float(amount),
        customer_number=phone_number,
        customer_name=customer_name,
        item_desc=f"EcoShop order {order_id}",
        order_id=order_id,
        payby=network,
        callback_url=callback_url,
    )


def parse_payment_callback(callback_data: dict) -> dict:
    """
    Normalizes Nalo's callback payload into {'status': 'successful'|'failed'|'pending', 'raw': ...}.

    Nalo's callback carries the outcome in a `Status` field (PAID/ACCEPTED = paid,
    FAILED = failed) alongside Timestamp/InvoiceNo/Order_id — there's no separate
    success/fail flag returned by the client library itself, so we read it directly.
    """
    status_raw = str(callback_data.get("Status") or callback_data.get("status") or "").upper()
    if status_raw in ("PAID", "ACCEPTED", "SUCCESS", "SUCCESSFUL"):
        status = "successful"
    elif status_raw in ("FAILED", "DECLINED", "CANCELLED"):
        status = "failed"
    else:
        status = "pending"
    return {"status": status, "raw": callback_data}
