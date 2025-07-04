from django import forms

from app_catalog.models import AddonParams


class AddToCartForm(forms.Form):
    variant_id = forms.IntegerField(widget=forms.HiddenInput())
    quantity = forms.IntegerField(min_value=1, max_value=20, initial=1,
                                  widget=forms.NumberInput(attrs={'class': 'form-control'}))

    # Поля для пиццы
    board_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    sauce_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    addons = forms.MultipleChoiceField(required=False, widget=forms.CheckboxSelectMultiple())

    def __init__(self, *args, **kwargs):
        product = kwargs.pop('product', None)
        variant = kwargs.pop('variant', None)
        super().__init__(*args, **kwargs)

        if product and product.category.name in ["Пицца", "Кальцоне"]:
            self.fields['addons'].choices = [
                (addon.id, f"{addon.addon.name} (+{addon.price} руб.)")
                for addon in AddonParams.objects.filter(size=variant.size)
            ]