# EcoShop Ghana

A Django e-commerce platform for a Ghanaian marketplace: phone (OTP) and
Google/Apple sign-in, category + name search, promos, order tracking,
Paystack checkout, and a full vendor dashboard.

## Stack

- **Django 6** with server-rendered templates + [htmx](https://htmx.org) for
  the parts that benefit from partial page updates (product search/filter)
- **django-allauth** for Google / Apple sign-in
- **Arkesel** for SMS OTP delivery (Ghana-focused SMS gateway)
- **Paystack** for card / Mobile Money payments
- **SQLite** by default (swap `DATABASES` in `settings.py` for Postgres/MySQL
  in production)
- **Tailwind CDN** for styling — no build step required

## Project layout

```
accounts/    Custom User model, phone OTP, primary/secondary Address model
catalog/     Category, Vendor, Product, ProductImage, Promo, search/listing views
orders/      Cart, Order, OrderItem, checkout flow, order status tracking
payments/    Payment model, Paystack integration, payment verification
vendor/      Vendor dashboard: orders checklist, payments tab, analytics,
             product CRUD, promo overview
core/        Homepage, WhatsApp support link context processor
templates/   All templates, organized by app
```

## Setup

1. **Clone and create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate      # on WSL/Linux/macOS
   pip install -r requirements.txt
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Fill in `.env` with your own keys. You can leave `ARKESEL_API_KEY`,
   `PAYSTACK_SECRET_KEY`, `GOOGLE_CLIENT_ID`, etc. blank for local
   development — OTP codes will just print to your console instead of
   sending real SMS, and Paystack calls will fail gracefully with an error
   message on the checkout page until you add test keys.

3. **Run migrations**
   ```bash
   python manage.py migrate
   ```

4. **Seed demo data (optional but recommended)**
   ```bash
   python manage.py seed_demo_data
   ```
   This creates:
   - A superuser: `admin` / `admin12345`
   - A demo vendor account (phone `0241234567`, log in via OTP — the code
     will print to your terminal since no Arkesel key is set)
   - 3 sample products across 3 categories, with one active promo

5. **Run the server**
   ```bash
   python manage.py runserver
   ```
   Visit `http://127.0.0.1:8000/`.

## How the key features map to code

| Feature | Where |
|---|---|
| Phone OTP login | `accounts/views.py` (`request_otp`, `verify_otp`), `accounts/services.py` (Arkesel) |
| Google/Apple sign-in | `django-allauth`, configured in `settings.py` under `SOCIALACCOUNT_PROVIDERS` |
| Login-required checkout | `orders/views.py:checkout` uses `@login_required`; browsing/cart do not |
| Primary/secondary address + Ghana region dropdown | `accounts/models.py:Address`, `accounts/regions.py` |
| Category + name search | `catalog/views.py:product_list` (uses `Q` lookups + htmx partial reload) |
| Promo (price reduction) | `catalog/models.py:Promo`, `Product.display_price` |
| Order status / detailed view | `orders/views.py:order_status`, `templates/orders/order_status.html` |
| Checkout payment options | `payments/views.py`, `payments/services.py` (Paystack) |
| WhatsApp support icon | `core/context_processors.py` + floating button in `templates/base.html` |
| Note to seller at checkout | `orders/models.py:Order.note_to_seller`, captured in `checkout` view |
| Vendor orders checklist (pending/completed) | `vendor/views.py:order_checklist` |
| Vendor payments tab (failed/pending/successful) | `vendor/views.py:payments_tab` |
| Vendor analytics | `vendor/views.py:analytics` (top products, low stock) |
| Vendor product management (add/edit/remove) | `vendor/views.py:product_create/edit/delete/toggle_active` |

## Notes and next steps

- **Google/Apple credentials**: you'll need to register OAuth apps with
  Google Cloud Console and Apple Developer to get real `GOOGLE_CLIENT_ID`
  etc. Until then, those buttons will error — the phone OTP flow works
  fully without them.
- **Paystack webhooks**: the current flow verifies payment on redirect back
  from Paystack (`payments/views.py:verify_payment`). For production, also
  add a webhook endpoint so payments are confirmed even if the user closes
  the tab before redirecting back — Paystack's docs cover this at
  https://paystack.com/docs/payments/webhooks/.
- **Vendor sign-up**: there's currently no public "become a vendor" flow —
  vendor profiles (`catalog.Vendor`) are created via `/admin/`. Add a
  request-and-approve flow if you need vendors to self-register.
- **Static/media in production**: `DEBUG=True` serves media files directly;
  switch to whitenoise or a cloud storage backend (e.g. S3) before
  deploying.
