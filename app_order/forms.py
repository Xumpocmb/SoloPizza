from django import forms

from app_catalog.models import PizzaSauce
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
        fields = ['quantity', 'board', 'addons', 'sauce']  # Добавляем поле 'sauce'
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': 1}),
            'board': forms.Select(),
            'addons': forms.CheckboxSelectMultiple(),
        }