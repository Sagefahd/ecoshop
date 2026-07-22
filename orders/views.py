from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
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


@login_required
def checkout(request):
    cart = _get_or_create_cart(request)
    if not cart or not cart.items.exists():
        messages.warning(request, "Your cart is empty.")
        return redirect("orders:cart_detail")

    primary = Address.objects.filter(user=request.user, address_type="primary").first()
    secondary = Address.objects.filter(user=request.user, address_type="secondary").first()

    if not primary or not secondary:
        messages.warning(request, "Please add both a primary and secondary address before checking out.")
        return redirect("accounts:address_list")

    if request.method == "POST":
        note = request.POST.get("note_to_seller", "").strip()

        order = Order.objects.create(
            user=request.user,
            primary_address=primary,
            secondary_address=secondary,
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
        cart.items.all().delete()

        return redirect("payments:initiate", order_id=order.order_id)

    return render(request, "orders/checkout.html", {
        "cart": cart, "primary": primary, "secondary": secondary,
    })


@login_required
def order_list(request):
    orders = request.user.orders.all()
    return render(request, "orders/order_list.html", {"orders": orders})


@login_required
def order_status(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    return render(request, "orders/order_status.html", {"order": order})
