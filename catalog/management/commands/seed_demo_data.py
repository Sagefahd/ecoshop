from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import User
from catalog.models import Category, Product, Promo


class Command(BaseCommand):
    help = "Seeds the database with demo categories, products, and a promo for local development."

    def handle(self, *args, **options):
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@example.com", "admin12345")
            self.stdout.write(self.style.SUCCESS("Created superuser: admin / admin12345"))

        # A vendor-role account — shares the same shop dashboard as any other vendor account.
        vendor_user, _ = User.objects.get_or_create(
            username="233241234567",
            defaults={"phone_number": "233241234567", "is_vendor": True, "phone_verified": True},
        )
        vendor_user.is_vendor = True
        vendor_user.save()

        cat1, _ = Category.objects.get_or_create(name="Electronics")
        cat2, _ = Category.objects.get_or_create(name="Fashion")
        cat3, _ = Category.objects.get_or_create(name="Groceries")

        p1, _ = Product.objects.get_or_create(
            category=cat1, name="Bluetooth Headphones",
            defaults={"price": 250, "stock_quantity": 20,
                      "description": "Wireless over-ear headphones with noise cancellation."},
        )
        Product.objects.get_or_create(
            category=cat2, name="Kente Print Shirt",
            defaults={"price": 180, "stock_quantity": 4,
                      "description": "Locally made shirt with kente-inspired print."},
        )
        Product.objects.get_or_create(
            category=cat3, name="5kg Rice Bag",
            defaults={"price": 90, "stock_quantity": 50, "description": "Premium long grain rice."},
        )

        promo, _ = Promo.objects.get_or_create(
            name="Launch Sale",
            defaults={
                "discount_type": "percentage", "discount_value": 15,
                "start_date": timezone.now() - timedelta(days=1),
                "end_date": timezone.now() + timedelta(days=30),
            },
        )
        promo.products.add(p1)

        self.stdout.write(self.style.SUCCESS("Demo data seeded."))
        self.stdout.write("Admin login: admin / admin12345")
        self.stdout.write("Vendor login (OTP): 0241234567 (check console for code in dev mode)")
