from django.conf import settings


def site_settings(request):
    """Makes the WhatsApp support number available in every template."""
    number = getattr(settings, "WHATSAPP_SUPPORT_NUMBER", "")
    return {
        "WHATSAPP_SUPPORT_NUMBER": number,
        "WHATSAPP_SUPPORT_LINK": f"https://wa.me/{number}" if number else "",
    }


def cart_count(request):
    """
    Total item count for the cart badge in the header — works for both
    logged-in users (Cart model) and anonymous browsers (session cart).
    """
    if getattr(request, "user", None) and request.user.is_authenticated:
        from django.db.models import Sum
        from orders.models import Cart

        cart = Cart.objects.filter(user=request.user).first()
        total = cart.items.aggregate(total=Sum("quantity"))["total"] if cart else None
        return {"cart_count": total or 0}

    session_cart = request.session.get("cart", {})
    return {"cart_count": sum(session_cart.values())}
