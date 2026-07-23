from decimal import Decimal

from django.contrib import messages
from django.db.models import Sum, Count, Q, F
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta

from catalog.models import Product, Category, Promo
from orders.models import Order, OrderItem
from payments.models import Payment
from .decorators import vendor_required
from .forms import ProductForm


@vendor_required
def dashboard_home(request):
    products = Product.objects.all()
    orders = Order.objects.all()

    today = timezone.now()
    last_30_days = today - timedelta(days=30)

    stats = {
        "total_products": products.count(),
        "active_products": products.filter(is_active=True).count(),
        "out_of_stock": products.filter(stock_quantity=0).count(),
        "pending_orders": orders.filter(status__in=["pending", "preparing"]).count(),
        "completed_orders": orders.filter(status="delivered").count(),
        "orders_last_30_days": orders.filter(created_at__gte=last_30_days).count(),
        "revenue_last_30_days": Payment.objects.filter(
            status="successful", created_at__gte=last_30_days
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00"),
    }

    recent_orders = orders.order_by("-created_at")[:8]

    return render(request, "vendor/dashboard_home.html", {
        "stats": stats, "recent_orders": recent_orders,
    })


@vendor_required
def order_checklist(request):
    status_filter = request.GET.get("status", "pending")
    orders = Order.objects.all()

    if status_filter == "pending":
        orders = orders.filter(status__in=["pending", "preparing", "shipped"])
    elif status_filter == "completed":
        orders = orders.filter(status="delivered")
    elif status_filter == "cancelled":
        orders = orders.filter(status="cancelled")

    orders = orders.order_by("-created_at")

    return render(request, "vendor/order_checklist.html", {
        "orders": orders, "status_filter": status_filter,
    })


@vendor_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)

    if request.method == "POST":
        new_status = request.POST.get("status")
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save(update_fields=["status"])
            messages.success(request, f"Order {order.order_id} marked as {order.get_status_display()}.")
            return redirect("vendor:order_detail", order_id=order.order_id)

    return render(request, "vendor/order_detail.html", {"order": order})


@vendor_required
def payments_tab(request):
    payments = Payment.objects.select_related("order").all()

    status_filter = request.GET.get("status")
    if status_filter in ("pending", "successful", "failed"):
        payments = payments.filter(status=status_filter)

    summary = payments.aggregate(
        successful=Count("id", filter=Q(status="successful")),
        pending=Count("id", filter=Q(status="pending")),
        failed=Count("id", filter=Q(status="failed")),
        total_received=Sum("amount", filter=Q(status="successful")),
    )

    return render(request, "vendor/payments_tab.html", {
        "payments": payments.order_by("-created_at"),
        "summary": summary,
        "status_filter": status_filter,
    })


@vendor_required
def analytics(request):
    top_products = (
        OrderItem.objects.all()
        .values("product__name")
        .annotate(units_sold=Sum("quantity"), revenue=Sum(F("unit_price") * F("quantity")))
        .order_by("-units_sold")[:10]
    )

    low_stock = Product.objects.filter(stock_quantity__lte=5, is_active=True)

    return render(request, "vendor/analytics.html", {
        "top_products": top_products,
        "low_stock": low_stock,
    })


@vendor_required
def product_list(request):
    products = Product.objects.all().order_by("-created_at")
    return render(request, "vendor/product_list.html", {"products": products})


@vendor_required
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, f"{product.name} added to the shop.")
            return redirect("vendor:product_list")
    else:
        form = ProductForm()
    return render(request, "vendor/product_form.html", {"form": form, "mode": "create"})


@vendor_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f"{product.name} updated.")
            return redirect("vendor:product_list")
    else:
        form = ProductForm(instance=product)
    return render(request, "vendor/product_form.html", {"form": form, "mode": "edit", "product": product})


@vendor_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        name = product.name
        product.delete()
        messages.success(request, f"{name} removed from the shop.")
        return redirect("vendor:product_list")
    return render(request, "vendor/product_confirm_delete.html", {"product": product})


@vendor_required
def product_toggle_active(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.is_active = not product.is_active
    product.save(update_fields=["is_active"])
    return redirect("vendor:product_list")


@vendor_required
def promo_list(request):
    promos = Promo.objects.all().distinct()
    return render(request, "vendor/promo_list.html", {"promos": promos})
