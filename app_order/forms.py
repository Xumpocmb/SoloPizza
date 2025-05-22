from django import forms

from app_catalog.models import Item, ItemParams, BoardParams, AddonParams, PizzaSauce, ItemSizes
from .models import OrderItem


class OrderItemForm(forms.ModelForm):
    sauce = forms.ModelChoiceField(
        queryset=PizzaSauce.objects.filter(is_active=True),
        required=False,
        label='Соус',
        widget=forms.RadioSelect,
        empty_label="Без соуса"
    )

    class Meta:
        model = OrderItem
        fields = ['quantity', 'board', 'addons', 'sauce']
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': 1}),
            'board': forms.Select(),
            'addons': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.item_params:
            size_id = self.instance.item_params.size_id
            self.fields['board'].queryset = BoardParams.objects.filter(size_id=size_id)
            self.fields['addons'].queryset = AddonParams.objects.filter(size_id=size_id)

