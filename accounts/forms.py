import re

from django import forms

from .models import Address


PHONE_RE = re.compile(r"^233\d{9}$")


def normalize_gh_phone(raw: str) -> str:
    """Normalize Ghanaian numbers to 233XXXXXXXXX format."""
    digits = re.sub(r"\D", "", raw or "")
    if digits.startswith("0") and len(digits) == 10:
        digits = "233" + digits[1:]
    elif digits.startswith("233") and len(digits) == 12:
        pass
    return digits


class PhoneNumberForm(forms.Form):
    phone_number = forms.CharField(
        label="Phone number",
        widget=forms.TextInput(attrs={
            "placeholder": "024 XXX XXXX",
            "class": "input",
            "autocomplete": "tel",
        }),
    )

    def clean_phone_number(self):
        raw = self.cleaned_data["phone_number"]
        normalized = normalize_gh_phone(raw)
        if not PHONE_RE.match(normalized):
            raise forms.ValidationError("Enter a valid Ghanaian phone number, e.g. 024XXXXXXX.")
        return normalized


class OTPVerifyForm(forms.Form):
    code = forms.CharField(
        label="Verification code",
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            "placeholder": "000000",
            "class": "input tracking-widest text-center",
            "inputmode": "numeric",
            "autocomplete": "one-time-code",
        }),
    )


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            "full_name", "phone_number", "region", "city_town",
            "street_address", "digital_address", "landmark",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "input", "placeholder": "Full name"}),
            "phone_number": forms.TextInput(attrs={"class": "input", "placeholder": "Active phone number"}),
            "region": forms.Select(attrs={"class": "input"}),
            "city_town": forms.TextInput(attrs={"class": "input", "placeholder": "City / Town"}),
            "street_address": forms.TextInput(attrs={"class": "input", "placeholder": "Street address"}),
            "digital_address": forms.TextInput(attrs={"class": "input", "placeholder": "GA-123-4567 (optional)"}),
            "landmark": forms.TextInput(attrs={"class": "input", "placeholder": "Nearby landmark (optional)"}),
        }

    def clean_phone_number(self):
        raw = self.cleaned_data["phone_number"]
        normalized = normalize_gh_phone(raw)
        if not PHONE_RE.match(normalized):
            raise forms.ValidationError("Enter a valid Ghanaian phone number.")
        return normalized
