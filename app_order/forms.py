from django import forms

from app_catalog.models import ProductVariant, BoardParams
from app_order.models import Order, OrderItem


class CheckoutForm(forms.Form):
    DELIVERY_CHOICES = [
        ('pickup', 'Самовывоз'),
        ('delivery', 'Доставка'),
    ]

    PAYMENT_CHOICES = [
        ('cash', 'Наличные'),
        ('card', 'Карта'),
    ]

    name = forms.CharField(
        label='Ваше имя',
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Иван Иванов'
        })
    )

    phone = forms.CharField(
        label='Телефон',
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '+7 (999) 123-45-67'
        })
    )

    address = forms.CharField(
        label='Адрес доставки',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'ул. Ленина, д. 1, кв. 1'
        })
    )

    delivery_type = forms.ChoiceField(
        label='Способ получения',
        choices=DELIVERY_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'delivery-options'})
    )

    payment_method = forms.ChoiceField(
        label='Способ оплаты',
        choices=PAYMENT_CHOICES,
        widget=forms.RadioSelect(),
        initial='cash'
    )

    comment = forms.CharField(
        label='Комментарий к заказу',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-textarea',
            'placeholder': 'Ваши пожелания...',
            'rows': 3
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        delivery_type = cleaned_data.get('delivery_type')
        payment_method = cleaned_data.get('payment_method')
        address = cleaned_data.get('address')

        if delivery_type == 'delivery' and not address:
            self.add_error('address', 'Укажите адрес для доставки')

        return cleaned_data


class OrderEditForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            'delivery_type',
            'payment_method',
            'payment_status',
            'customer_name',
            'phone_number',
            'address',
            'comment'
        ]
        widgets = {
            'delivery_type': forms.RadioSelect(attrs={'class': 'delivery-options'}),
            'payment_method': forms.RadioSelect(attrs={'class': 'payment-options'}),
            'payment_status': forms.CheckboxInput(attrs={'class': 'payment-status'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-input'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input'}),
            'comment': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': 'Ваши пожелания...'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'ул. Ленина, д. 1, кв. 1',
                'id': 'id_address'
            }),
        }
        labels = {
            'customer_name': 'Имя заказчика',
            'phone_number': 'Телефон',
            'comment': 'Комментарий',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['payment_status'].label = "Заказ оплачен"

        # Устанавливаем начальное значение для адреса при самовывозе
        if self.instance.delivery_type == 'pickup' and not self.instance.address:
            self.instance.address = 'Самовывоз'

        self.fields['address'].required = False
        if self.initial.get('delivery_type') == 'delivery':
            self.fields['address'].required = True

    def clean(self):
        cleaned_data = super().clean()
        delivery_type = cleaned_data.get('delivery_type')
        address = cleaned_data.get('address')

        if delivery_type == 'delivery' and not address:
            self.add_error('address', 'Укажите адрес для доставки')
        elif delivery_type == 'pickup':
            cleaned_data['address'] = 'Самовывоз'

        return cleaned_data


class OrderItemEditForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['variant', 'quantity', 'board', 'sauce']
        widgets = {
            'variant': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 1,
                'max': 20
            }),
            'board': forms.Select(attrs={'class': 'form-select'}),
            'sauce': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Фильтруем варианты только для этого товара
        if self.instance:
            self.fields['variant'].queryset = ProductVariant.objects.filter(
                product=self.instance.product
            )
            # Фильтруем борты по размеру
            if self.instance.variant.size:
                self.fields['board'].queryset = BoardParams.objects.filter(
                    size=self.instance.variant.size
                )