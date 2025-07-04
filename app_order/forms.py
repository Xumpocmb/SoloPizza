from django import forms

from app_order.models import Order


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
                'id': 'address-input'
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

    def clean(self):
        cleaned_data = super().clean()
        delivery_type = cleaned_data.get('delivery_type')
        address = cleaned_data.get('address')

        # Если выбрана доставка, адрес становится обязательным
        if delivery_type == 'delivery' and not address:
            self.add_error('address', 'Укажите адрес для доставки')

        return cleaned_data