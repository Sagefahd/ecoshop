from django.shortcuts import render

from catalog.models import Product, Category


def home(request):
    featured = Product.objects.filter(is_active=True).select_related("category")[:8]
    categories = Category.objects.filter(is_active=True)
    return render(request, "core/home.html", {"featured": featured, "categories": categories})
