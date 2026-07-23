from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from .forms import PhoneNumberForm, OTPVerifyForm, AddressForm
from .models import OTP, Address
from .services import send_otp_sms

User = get_user_model()


def request_otp(request):
    """Step 1: user enters phone number, we text them a 6-digit code."""
    next_url = request.GET.get("next") or request.POST.get("next")
    if next_url:
        request.session["next_url"] = next_url

    if request.method == "POST":
        form = PhoneNumberForm(request.POST)
        if form.is_valid():
            phone_number = form.cleaned_data["phone_number"]
            otp = OTP.generate(phone_number, purpose="login")
            sent = send_otp_sms(phone_number, otp.code)
            if not sent:
                messages.error(request, "Couldn't send the code. Please try again.")
            else:
                request.session["otp_phone"] = phone_number
                return redirect("accounts:verify_otp")
    else:
        form = PhoneNumberForm()
    return render(request, "accounts/request_otp.html", {"form": form, "next_url": next_url})


def verify_otp(request):
    """Step 2: user enters the code they received."""
    phone_number = request.session.get("otp_phone")
    if not phone_number:
        return redirect("accounts:request_otp")

    if request.method == "POST":
        form = OTPVerifyForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data["code"]
            otp = OTP.objects.filter(phone_number=phone_number, purpose="login").first()

            if not otp or not otp.is_valid():
                messages.error(request, "This code has expired. Please request a new one.")
                return redirect("accounts:request_otp")

            otp.attempts += 1
            otp.save(update_fields=["attempts"])

            if otp.code != code:
                messages.error(request, "Incorrect code. Please try again.")
            else:
                otp.is_used = True
                otp.save(update_fields=["is_used"])

                user, created = User.objects.get_or_create(
                    phone_number=phone_number,
                    defaults={"username": phone_number, "phone_verified": True},
                )
                if not created and not user.phone_verified:
                    user.phone_verified = True
                    user.save(update_fields=["phone_verified"])

                login(request, user, backend="django.contrib.auth.backends.ModelBackend")
                del request.session["otp_phone"]

                next_url = request.session.pop("next_url", None)
                messages.success(request, "You're logged in!")
                return redirect(next_url or "core:home")
    else:
        form = OTPVerifyForm()

    return render(request, "accounts/verify_otp.html", {"form": form, "phone_number": phone_number})


def resend_otp(request):
    phone_number = request.session.get("otp_phone")
    if phone_number:
        otp = OTP.generate(phone_number, purpose="login")
        send_otp_sms(phone_number, otp.code)
        messages.info(request, "A new code has been sent.")
    return redirect("accounts:verify_otp")


@login_required
def address_list(request):
    addresses = request.user.addresses.all()
    return render(request, "accounts/address_list.html", {"addresses": addresses})


@login_required
def address_create(request):
    """Add a new address to the user's address book."""
    next_url = request.GET.get("next")
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, "Address saved.")
            return redirect(request.POST.get("next") or "accounts:address_list")
    else:
        form = AddressForm(initial={"is_default": not request.user.addresses.exists()})

    return render(request, "accounts/address_form.html", {
        "form": form, "mode": "create", "next_url": next_url,
    })


@login_required
def address_edit(request, pk):
    """Edit one address from the user's address book."""
    instance = get_object_or_404(Address, pk=pk, user=request.user)
    next_url = request.GET.get("next")

    if request.method == "POST":
        form = AddressForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, "Address updated.")
            return redirect(request.POST.get("next") or "accounts:address_list")
    else:
        form = AddressForm(instance=instance)

    return render(request, "accounts/address_form.html", {
        "form": form, "mode": "edit", "address": instance, "next_url": next_url,
    })


@login_required
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == "POST":
        was_default = address.is_default
        address.delete()
        if was_default:
            fallback = request.user.addresses.first()
            if fallback:
                fallback.is_default = True
                fallback.save(update_fields=["is_default"])
        messages.info(request, "Address removed.")
        return redirect("accounts:address_list")
    return render(request, "accounts/address_confirm_delete.html", {"address": address})


@login_required
def address_set_default(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == "POST":
        address.is_default = True
        address.save()  # save() handles unsetting the previous default
        messages.success(request, "Default address updated.")
    return redirect("accounts:address_list")
