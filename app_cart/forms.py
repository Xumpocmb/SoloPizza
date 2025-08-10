from django import forms

from app_catalog.models import AddonParams


class AddToCartForm(forms.Form):
    variant_id = forms.IntegerField(widget=forms.HiddenInput())
    quantity = forms.IntegerField(
        min_value=1,
        max_value=10,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    # Поля для пиццы / кальцоне
    sauce_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    board1_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    board2_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    addons = forms.MultipleChoiceField(required=False, widget=forms.CheckboxSelectMultiple())

    def __init__(self, *args, **kwargs):
        self.product = kwargs.pop('product', None)
        self.variant = kwargs.pop('variant', None)
        super().__init__(*args, **kwargs)

        # Если это не пицца, кальцоне или комбо — скрываем все специфичные поля
        if not (self.product and (self.product.category.name in ["Пицца", "Кальцоне"] or 
                                (self.product.category.name == "Комбо" and self.product.is_combo))):
            for field in ['sauce_id', 'board1_id', 'board2_id', 'addons']:
                if field in self.fields:
                    del self.fields[field]
        else:
            # Для пиццы и комбо-наборов с пиццей добавляем опции
            if self.product.category.name in ["Пицца", "Кальцоне"]:
                # Для пиццы добавляем опции для addons
                self.fields['addons'].choices = [
                    (addon.id, f"{addon.addon.name} (+{addon.price} руб.)")
                    for addon in AddonParams.objects.filter(size=self.variant.size)
                ]
            elif self.product.category.name == "Комбо" and self.product.is_combo:
                # Для комбо оставляем только поля для бортов
                if 'sauce_id' in self.fields:
                    del self.fields['sauce_id']
                if 'addons' in self.fields:
                    del self.fields['addons']
