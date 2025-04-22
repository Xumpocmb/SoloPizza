from django import forms

from app_catalog.models import Item, ItemParams, BoardParams, AddonParams, PizzaSauce
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


class AddToOrderForm(forms.Form):
    item = forms.ModelChoiceField(
        queryset=Item.objects.all(),
        label="Товар",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    size = forms.ModelChoiceField(
        queryset=ItemParams.objects.none(),
        label="Размер",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        label="Количество",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    board = forms.ModelChoiceField(
        queryset=BoardParams.objects.all(),
        required=False,
        label="Борт",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    sauce = forms.ModelChoiceField(
        queryset=PizzaSauce.objects.all(),
        required=False,
        label="Соус",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    addons = forms.ModelMultipleChoiceField(
        queryset=AddonParams.objects.none(),
        required=False,
        label="Добавки",
        widget=forms.CheckboxSelectMultiple
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'item' in self.data:
            try:
                item_id = int(self.data.get('item'))
                self.fields['size'].queryset = ItemParams.objects.filter(item_id=item_id)
            except (ValueError, TypeError):
                pass
