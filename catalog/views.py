from django.db.models import Q
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404

from .models import Product, Category


def product_list(request):
    products = Product.objects.filter(is_active=True).select_related("category", "vendor")

    query = request.GET.get("q", "").strip()
    category_slug = request.GET.get("category", "").strip()

    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    if category_slug:
        products = products.filter(category__slug=category_slug)

    paginator = Paginator(products, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    categories = Category.objects.filter(is_active=True)

    context = {
        "page_obj": page_obj,
        "products": page_obj.object_list,
        "categories": categories,
        "query": query,
        "active_category": category_slug,
    }
    template = "catalog/_product_grid.html" if request.htmx else "catalog/product_list.html"
    return render(request, template, context)


def product_detail(request, slug):
    product = get_object_or_404(Product.objects.select_related("category", "vendor"), slug=slug, is_active=True)
    related = Product.objects.filter(category=product.category, is_active=True).exclude(pk=product.pk)[:4]
    return render(request, "catalog/product_detail.html", {"product": product, "related": related})
