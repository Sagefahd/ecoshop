import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from orders.models import Order
from .models import Payment
from .services import request_momo_payment, parse_payment_callback, NETWORK_CHOICES


@login_required
def initiate_payment(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)

    if request.method == "POST":
        method = request.POST.get("method", "nalo_mtn")

        payment = Payment.objects.create(order=order, method=method, amount=order.total, status="pending")

        if method == "cash_on_delivery":
            messages.success(request, "Order placed! You'll pay on delivery.")
            return redirect("orders:order_status", order_id=order.order_id)

        network = Payment.NETWORK_BY_METHOD.get(method)
        callback_url = request.build_absolute_uri(reverse("payments:callback"))
        try:
            result = request_momo_payment(
                amount=order.total,
                phone_number=order.delivery_address.phone_number,
                customer_name=order.delivery_address.full_name,
                order_id=order.order_id,
                network=network,
                callback_url=callback_url,
            )
            payment.gateway_response = result
            payment.save(update_fields=["gateway_response"])
            messages.info(request, "Check your phone — approve the Mobile Money prompt to complete payment.")
            return redirect("payments:pending", reference=payment.reference)
        except Exception:
            payment.status = "failed"
            payment.save()
            messages.error(request, "Could not start payment. Please try again.")
            return redirect("payments:initiate", order_id=order.order_id)

    return render(request, "payments/initiate.html", {"order": order, "network_choices": NETWORK_CHOICES})


@login_required
def payment_pending(request, reference):
    """Shown right after the MoMo prompt is sent, while we wait for Nalo's callback."""
    payment = get_object_or_404(Payment, reference=reference, order__user=request.user)
    return render(request, "payments/pending.html", {"payment": payment})


@login_required
def payment_status(request, reference):
    """Polled by the pending page to check whether the callback has arrived yet."""
    payment = get_object_or_404(Payment, reference=reference, order__user=request.user)
    return JsonResponse({"status": payment.status, "order_id": payment.order.order_id})


@csrf_exempt
def payment_callback(request):
    """Webhook Nalo POSTs to once the customer approves/declines the MoMo prompt."""
    try:
        callback_data = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        callback_data = request.POST.dict()

    order_id = callback_data.get("order_id") or callback_data.get("Order_id")
    payment = Payment.objects.filter(order__order_id=order_id).order_by("-created_at").first()
    if not payment:
        return JsonResponse({"received": True}, status=200)

    result = parse_payment_callback(callback_data)
    payment.status = result["status"]
    payment.gateway_response = result["raw"]
    payment.save(update_fields=["status", "gateway_response", "updated_at"])

    return JsonResponse({"received": True})
