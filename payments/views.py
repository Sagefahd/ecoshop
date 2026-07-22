from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from orders.models import Order
from .models import Payment
from .services import initialize_transaction, verify_transaction


@login_required
def initiate_payment(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)

    if request.method == "POST":
        method = request.POST.get("method", "paystack_card")

        payment = Payment.objects.create(order=order, method=method, amount=order.total, status="pending")

        if method == "cash_on_delivery":
            payment.status = "pending"
            payment.save()
            messages.success(request, "Order placed! You'll pay on delivery.")
            return redirect("orders:order_status", order_id=order.order_id)

        callback_url = request.build_absolute_uri(reverse("payments:verify", args=[payment.reference]))
        try:
            result = initialize_transaction(
                email=request.user.email or f"{request.user.phone_number}@ecoshop.gh",
                amount_ghs=order.total,
                reference=payment.reference,
                callback_url=callback_url,
            )
            auth_url = result["data"]["authorization_url"]
            return redirect(auth_url)
        except Exception:
            payment.status = "failed"
            payment.save()
            messages.error(request, "Could not start payment. Please try again.")
            return redirect("payments:initiate", order_id=order.order_id)

    return render(request, "payments/initiate.html", {"order": order})


def verify_payment(request, reference):
    payment = get_object_or_404(Payment, reference=reference)

    try:
        result = verify_transaction(reference)
        status = result["data"]["status"]
        payment.gateway_response = result
        payment.status = "successful" if status == "success" else "failed"
        payment.save()
        if payment.status == "successful":
            messages.success(request, "Payment successful!")
        else:
            messages.error(request, "Payment was not successful.")
    except Exception:
        payment.status = "failed"
        payment.save()
        messages.error(request, "Couldn't verify payment.")

    return redirect("orders:order_status", order_id=payment.order.order_id)
