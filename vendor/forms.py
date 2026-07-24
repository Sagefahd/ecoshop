from django import forms

from catalog.models import Product, Category, Promo


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "category", "description", "price", "stock_quantity", "thumbnail", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input", "placeholder": "Product name"}),
            "category": forms.Select(attrs={"class": "input"}),
            "description": forms.Textarea(attrs={"class": "input", "rows": 4, "placeholder": "Short description shown on the product page"}),
            "price": forms.NumberInput(attrs={"class": "input", "step": "0.01", "placeholder": "0.00"}),
            "stock_quantity": forms.NumberInput(attrs={"class": "input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "checkbox"}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name", "description", "image", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input", "placeholder": "e.g. Electronics"}),
            "description": forms.Textarea(attrs={"class": "input", "rows": 3, "placeholder": "Optional short description"}),
            "is_active": forms.CheckboxInput(attrs={"class": "checkbox"}),
        }


class PromoForm(forms.ModelForm):
    class Meta:
        model = Promo
        fields = ["name", "products", "discount_type", "discount_value", "start_date", "end_date", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input", "placeholder": "e.g. Launch Sale"}),
            "products": forms.SelectMultiple(attrs={"class": "input", "size": 8}),
            "discount_type": forms.Select(attrs={"class": "input"}),
            "discount_value": forms.NumberInput(attrs={"class": "input", "step": "0.01"}),
            "start_date": forms.DateTimeInput(attrs={"class": "input", "type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "end_date": forms.DateTimeInput(attrs={"class": "input", "type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "is_active": forms.CheckboxInput(attrs={"class": "checkbox"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["start_date"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["end_date"].input_formats = ["%Y-%m-%dT%H:%M"]
