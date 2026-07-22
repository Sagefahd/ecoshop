from django import forms

from catalog.models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "category", "description", "price", "stock_quantity", "thumbnail", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input"}),
            "category": forms.Select(attrs={"class": "input"}),
            "description": forms.Textarea(attrs={"class": "input", "rows": 4}),
            "price": forms.NumberInput(attrs={"class": "input", "step": "0.01"}),
            "stock_quantity": forms.NumberInput(attrs={"class": "input"}),
        }
