from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from accounts.models import Address
from catalog.models import Product
from .models import Cart, CartItem, Order, OrderItem


def _get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart
    return None


@require_POST
def cart_add(request, product_id):
    """Anyone can add to cart — auth is only required at checkout."""
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    quantity = int(request.POST.get("quantity", 1))

    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={"quantity": quantity})
        if not created:
            item.quantity += quantity
            item.save()
    else:
        # Session-based cart for anonymous browsing
        session_cart = request.session.get("cart", {})
        session_cart[str(product_id)] = session_cart.get(str(product_id), 0) + quantity
        request.session["cart"] = session_cart

    messages.success(request, f"Added {product.name} to cart.")
    next_url = request.POST.get("next") or "catalog:product_list"
    return redirect(next_url)


@login_required
@require_POST
def cart_update(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    quantity = int(request.POST.get("quantity", 1))
    if quantity <= 0:
        item.delete()
    else:
        item.quantity = quantity
        item.save()
    return redirect("orders:cart_detail")


@login_required
def cart_remove(request, item_id):
    CartItem.objects.filter(pk=item_id, cart__user=request.user).delete()
    messages.info(request, "Item removed from cart.")
    return redirect("orders:cart_detail")


def cart_detail(request):
    cart = _get_or_create_cart(request)
    return render(request, "orders/cart_detail.html", {"cart": cart})


def _checkout_errors(request, cart, address):
    """
    Check-all validation: run every check before letting an order through,
    rather than failing partway. Returns a list of human-readable problems —
    empty list means everything is in order.
    """
    errors = []

    if not cart or not cart.items.exists():
        errors.append("Your cart is empty.")
        return errors  # nothing else to check without a cart

    if not address:
        errors.append("Please add a delivery address before checking out.")

    if not request.user.phone_number or not request.user.phone_verified:
        errors.append("Please verify an active phone number on your account before checking out.")

    for cart_item in cart.items.select_related("product"):
        product = cart_item.product
        if not product.is_active:
            errors.append(f"\"{product.name}\" is no longer available and was removed from checkout.")
        elif cart_item.quantity > product.stock_quantity:
            errors.append(
                f"Only {product.stock_quantity} of \"{product.name}\" left in stock "
                f"(you have {cart_item.quantity} in your cart)."
            )

    return errors


@login_required
def checkout(request):
    cart = _get_or_create_cart(request)
    address = (
        Address.objects.filter(user=request.user, pk=request.POST.get("address_id")).first()
        if request.method == "POST" else None
    ) or request.user.addresses.filter(is_default=True).first()
    addresses = request.user.addresses.all()

    if request.method == "POST":
        errors = _checkout_errors(request, cart, address)
        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect("orders:cart_detail" if not cart or not cart.items.exists() else "orders:checkout")

        note = request.POST.get("note_to_seller", "").strip()

        order = Order.objects.create(
            user=request.user,
            delivery_address=address,
            note_to_seller=note,
            subtotal=cart.total,
            delivery_fee=Decimal("0.00"),
            total=cart.total,
        )
        for cart_item in cart.items.select_related("product"):
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                product_name=cart_item.product.name,
                unit_price=cart_item.product.display_price,
                quantity=cart_item.quantity,
            )
            cart_item.product.stock_quantity = F("stock_quantity") - cart_item.quantity
            cart_item.product.save(update_fields=["stock_quantity"])
        cart.items.all().delete()

        return redirect("payments:initiate", order_id=order.order_id)

    if not cart or not cart.items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect("orders:cart_detail")

    return render(request, "orders/checkout.html", {
        "cart": cart, "address": address, "addresses": addresses,
    })


@login_required
def order_list(request):
    orders = request.user.orders.all()
    return render(request, "orders/order_list.html", {"orders": orders})


@login_required
def order_status(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    return render(request, "orders/order_status.html", {"order": order})
