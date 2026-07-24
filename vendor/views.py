from decimal import Decimal

from django.contrib import messages
from django.db.models import Sum, Count, Q, F
from django.db.models.functions import TruncDate
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta

from catalog.models import Product, Category, Promo
from orders.models import Order, OrderItem
from payments.models import Payment
from accounts.models import User
from .decorators import vendor_required
from .forms import ProductForm, CategoryForm, PromoForm


@vendor_required
def dashboard_home(request):
    products = Product.objects.all()
    orders = Order.objects.all()

    today = timezone.now()
    last_30_days = today - timedelta(days=30)
    last_7_days = today - timedelta(days=7)

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
        "customers_total": User.objects.filter(orders__isnull=False).distinct().count(),
    }

    recent_orders = orders.order_by("-created_at")[:6]

    # 7-day order trend for the mini bar chart on the overview page
    daily_counts = {
        row["day"]: row["count"]
        for row in orders.filter(created_at__gte=last_7_days)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(count=Count("id"))
    }
    trend = []
    max_count = 1
    for i in range(6, -1, -1):
        day = (today - timedelta(days=i)).date()
        count = daily_counts.get(day, 0)
        max_count = max(max_count, count)
        trend.append({"label": day.strftime("%a"), "count": count})
    for point in trend:
        point["pct"] = int((point["count"] / max_count) * 100) if max_count else 0

    return render(request, "vendor/dashboard_home.html", {
        "stats": stats, "recent_orders": recent_orders, "trend": trend,
    })


# ---------- Orders (checklist: pending / completed) ----------

@vendor_required
def order_checklist(request):
    status_filter = request.GET.get("status", "pending")
    query = request.GET.get("q", "").strip()
    orders = Order.objects.select_related("user", "delivery_address")

    if status_filter == "pending":
        orders = orders.filter(status__in=["pending", "preparing", "shipped"])
    elif status_filter == "completed":
        orders = orders.filter(status="delivered")
    elif status_filter == "cancelled":
        orders = orders.filter(status="cancelled")

    if query:
        orders = orders.filter(Q(order_id__icontains=query) | Q(user__phone_number__icontains=query))

    orders = orders.order_by("-created_at")

    return render(request, "vendor/order_checklist.html", {
        "orders": orders, "status_filter": status_filter, "query": query,
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


# ---------- Payments tab ----------

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


# ---------- Analytics ----------

@vendor_required
def analytics(request):
    top_products = (
        OrderItem.objects.all()
        .values("product__name")
        .annotate(units_sold=Sum("quantity"), revenue=Sum(F("unit_price") * F("quantity")))
        .order_by("-units_sold")[:10]
    )
    max_units = max([row["units_sold"] for row in top_products], default=1)
    for row in top_products:
        row["pct"] = int((row["units_sold"] / max_units) * 100) if max_units else 0

    low_stock = Product.objects.filter(stock_quantity__lte=5, is_active=True).order_by("stock_quantity")

    payment_method_split = list(
        Payment.objects.filter(status="successful")
        .values("method")
        .annotate(count=Count("id"), total=Sum("amount"))
        .order_by("-total")
    )
    method_labels = dict(Payment.METHOD_CHOICES)
    for row in payment_method_split:
        row["method_label"] = method_labels.get(row["method"], row["method"])

    return render(request, "vendor/analytics.html", {
        "top_products": top_products,
        "low_stock": low_stock,
        "payment_method_split": payment_method_split,
    })


# ---------- Customers ----------

@vendor_required
def customer_list(request):
    customers = (
        User.objects.filter(orders__isnull=False)
        .annotate(order_count=Count("orders", distinct=True), total_spent=Sum("orders__total"))
        .order_by("-total_spent")
    )
    return render(request, "vendor/customer_list.html", {"customers": customers})


# ---------- Product management ----------

@vendor_required
def product_list(request):
    query = request.GET.get("q", "").strip()
    products = Product.objects.select_related("category").order_by("-created_at")
    if query:
        products = products.filter(Q(name__icontains=query) | Q(sku__icontains=query))
    return render(request, "vendor/product_list.html", {"products": products, "query": query})


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


# ---------- Category management ----------

@vendor_required
def category_list(request):
    categories = Category.objects.annotate(product_count=Count("products")).order_by("name")
    return render(request, "vendor/category_list.html", {"categories": categories})


@vendor_required
def category_create(request):
    if request.method == "POST":
        form = CategoryForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save()
            messages.success(request, f"{category.name} category created.")
            return redirect("vendor:category_list")
    else:
        form = CategoryForm()
    return render(request, "vendor/category_form.html", {"form": form, "mode": "create"})


@vendor_required
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        form = CategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f"{category.name} updated.")
            return redirect("vendor:category_list")
    else:
        form = CategoryForm(instance=category)
    return render(request, "vendor/category_form.html", {"form": form, "mode": "edit", "category": category})


@vendor_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == "POST":
        name = category.name
        category.delete()
        messages.success(request, f"{name} category removed.")
        return redirect("vendor:category_list")
    return render(request, "vendor/category_confirm_delete.html", {"category": category})


# ---------- Promo management ----------

@vendor_required
def promo_list(request):
    promos = Promo.objects.all().distinct().order_by("-start_date")
    return render(request, "vendor/promo_list.html", {"promos": promos})


@vendor_required
def promo_create(request):
    if request.method == "POST":
        form = PromoForm(request.POST)
        if form.is_valid():
            promo = form.save()
            messages.success(request, f"{promo.name} promo created.")
            return redirect("vendor:promo_list")
    else:
        form = PromoForm(initial={"end_date": timezone.now() + timedelta(days=7)})
    return render(request, "vendor/promo_form.html", {"form": form, "mode": "create"})


@vendor_required
def promo_edit(request, pk):
    promo = get_object_or_404(Promo, pk=pk)
    if request.method == "POST":
        form = PromoForm(request.POST, instance=promo)
        if form.is_valid():
            form.save()
            messages.success(request, f"{promo.name} updated.")
            return redirect("vendor:promo_list")
    else:
        form = PromoForm(instance=promo)
    return render(request, "vendor/promo_form.html", {"form": form, "mode": "edit", "promo": promo})


@vendor_required
def promo_delete(request, pk):
    promo = get_object_or_404(Promo, pk=pk)
    if request.method == "POST":
        name = promo.name
        promo.delete()
        messages.success(request, f"{name} promo removed.")
        return redirect("vendor:promo_list")
    return render(request, "vendor/promo_confirm_delete.html", {"promo": promo})
