from django import forms
from django.utils import timezone
from app_order.models import Order
from app_home.models import Discount


class CheckoutForm(forms.ModelForm):
    DELIVERY_CHOICES = Order.DELIVERY_CHOICES
    PAYMENT_CHOICES = Order.PAYMENT_CHOICES

    name = forms.CharField(label="Ваше имя", max_length=100,
                           widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "Иван Иванов"}))

    phone = forms.CharField(label="Телефон", max_length=20,
                            widget=forms.TextInput(attrs={"class": "form-input", "placeholder": "+375 (99) 123-45-67"}))

    address = forms.CharField(label="Адрес доставки", required=False, widget=forms.TextInput(
        attrs={"class": "form-input", "placeholder": "ул. Ленина, д. 1, кв. 1"}))

    delivery_type = forms.ChoiceField(
        label="Способ получения",
        choices=DELIVERY_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "delivery-options"}),
        initial="pickup"
    )

    payment_method = forms.ChoiceField(label="Способ оплаты", choices=PAYMENT_CHOICES, widget=forms.RadioSelect(),
                                       initial="cash")

    is_partner = forms.BooleanField(label="Партнёр", required=False, 
                                  widget=forms.CheckboxInput(attrs={"class": "partner-checkbox"}))
    
    # Получаем процент скидки из модели Discount
    try:
        partner_discount = Discount.objects.filter(slug='partner').first()
        partner_discount_initial = partner_discount.percent if partner_discount else 10
    except:
        partner_discount_initial = 10
        
    partner_discount_percent = forms.IntegerField(label="Процент скидки", required=False, initial=partner_discount_initial,
                                               widget=forms.NumberInput(attrs={"class": "form-input partner-discount", 
                                                                          "min": "1", "max": "100"}))

    comment = forms.CharField(label="Комментарий к заказу", required=False, widget=forms.Textarea(
        attrs={"class": "form-textarea", "placeholder": "Ваши пожелания...", "rows": 3}))
        
    ready_by = forms.DateTimeField(label="Готов к", required=False, 
                                 widget=forms.DateTimeInput(attrs={"class": "form-input", "type": "datetime-local", "format": "%Y-%m-%dT%H:%M"}))
    
    delivery_by = forms.DateTimeField(label="Доставка к", required=False, 
                                    widget=forms.DateTimeInput(attrs={"class": "form-input", "type": "datetime-local", "format": "%Y-%m-%dT%H:%M"}))

    class Meta:
        model = Order
        fields = ["customer_name", "phone_number", "address", "delivery_type", "payment_method", 
                 "is_partner", "partner_discount_percent", "ready_by", "delivery_by", "comment"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["customer_name"].widget = self.fields["name"].widget
        self.fields["phone_number"].widget = self.fields["phone"].widget
        del self.fields["name"]
        del self.fields["phone"]

    def clean(self):
        cleaned_data = super().clean()
        delivery_type = cleaned_data.get("delivery_type")
        address = cleaned_data.get("address")
        phone = cleaned_data.get("phone_number")

        if delivery_type == "delivery" and not address:
            self.add_error("address", "Укажите адрес для доставки")
            
        # Делаем поле телефона необязательным для заказов "на месте"
        if delivery_type == "cafe" and not phone:
            # Если телефон не указан для заказа "на месте", это допустимо
            pass
        elif not phone:
            # Для других типов доставки телефон обязателен
            self.add_error("phone_number", "Укажите номер телефона")

        return cleaned_data

    def save(self, commit=True, user=None, session_key=None):
        order = super().save(commit=False)
        if session_key:
            order.session_key = session_key
        if user:
            order.payment_status = True if user.is_staff else False
            order.status = "new"
        
        # Автозаполнение поля delivery_by на основе ready_by
        ready_by = order.ready_by
        delivery_by = order.delivery_by
        if ready_by and not delivery_by:
            order.ready_by = ready_by
            order.delivery_by = ready_by + timezone.timedelta(minutes=20)

        if commit:
            order.save()
        return order


class OrderEditForm(forms.ModelForm):
    # Split payment fields
    cash_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-input", "step": "0.01"}),
        label="Сумма наличными"
    )
    card_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-input", "step": "0.01"}),
        label="Сумма картой"
    )
    noname_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-input", "step": "0.01"}),
        label="Сумма безналично"
    )

    class Meta:
        model = Order
        fields = ["delivery_type", "payment_method", "payment_status", "customer_name", "phone_number", "address",
                  "ready_by", "delivery_by", "comment", "is_partner", "partner_discount_percent",
                  "cash_amount", "card_amount", "noname_amount"]
        widgets = {
            "delivery_type": forms.RadioSelect(attrs={"class": "custom-radio-list"}),  # Просто указываете класс списка
            "payment_method": forms.RadioSelect(attrs={"class": "custom-radio-list"}),
            "payment_status": forms.CheckboxInput(attrs={"class": "custom-checkbox-list"}),
            "customer_name": forms.TextInput(attrs={"class": "form-input"}),
            "phone_number": forms.TextInput(attrs={"class": "form-input"}),
            "ready_by": forms.DateTimeInput(attrs={"class": "form-input", "type": "datetime-local"}, format='%Y-%m-%dT%H:%M'),
            "delivery_by": forms.DateTimeInput(attrs={"class": "form-input", "type": "datetime-local"}, format='%Y-%m-%dT%H:%M'),
            "comment": forms.Textarea(attrs={"class": "form-textarea", "rows": 3, "placeholder": "Ваши пожелания..."}),
            "address": forms.TextInput(
                attrs={"class": "form-input", "placeholder": "ул. Ленина, д. 1, кв. 1", "id": "id_address"}),
            "is_partner": forms.CheckboxInput(attrs={"class": "partner-checkbox"}),
            "partner_discount_percent": forms.NumberInput(attrs={"class": "form-input partner-discount", "min": "1", "max": "100"}),
        }
        labels = {
            "customer_name": "Имя заказчика",
            "phone_number": "Телефон",
            "comment": "Комментарий",
            "is_partner": "Партнёр",
            "partner_discount_percent": "Процент скидки",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["payment_status"].label = "Заказ оплачен"

        # Устанавливаем начальное значение для адреса при самовывозе
        if self.instance and self.instance.delivery_type == "pickup" and not self.instance.address:
            self.instance.address = "Самовывоз"

        # Устанавливаем начальные значения для полей раздельной оплаты
        if self.instance:
            self.fields['cash_amount'].initial = self.instance.cash_amount
            self.fields['card_amount'].initial = self.instance.card_amount
            self.fields['noname_amount'].initial = self.instance.noname_amount



    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get("payment_method")
        total_price = self.instance.total_price if self.instance else 0

        if payment_method == 'split':
            cash_amount = cleaned_data.get('cash_amount', 0) or 0
            card_amount = cleaned_data.get('card_amount', 0) or 0
            noname_amount = cleaned_data.get('noname_amount', 0) or 0

            split_total = cash_amount + card_amount + noname_amount

            # Check if the split payment total matches the order total
            if abs(split_total - total_price) >= 0.01:
                raise forms.ValidationError(
                    f'Сумма раздельной оплаты ({split_total:.2f} руб.) '
                    f'не совпадает с итоговой суммой заказа ({total_price:.2f} руб.).'
                )

        return cleaned_data

    def save(self, commit=True):
        order = super().save(commit=False)

        # Save split payment amounts
        order.cash_amount = self.cleaned_data.get('cash_amount', 0) or 0
        order.card_amount = self.cleaned_data.get('card_amount', 0) or 0
        order.noname_amount = self.cleaned_data.get('noname_amount', 0) or 0

        # Автозаполнение поля delivery_by на основе ready_by
        ready_by = order.ready_by
        delivery_by = order.delivery_by
        if ready_by and not delivery_by:
            order.ready_by = ready_by
            order.delivery_by = ready_by + timezone.timedelta(minutes=30)

        if commit:
            order.save()
        return order

    def clean(self):
        cleaned_data = super().clean()
        delivery_type = cleaned_data.get("delivery_type")
        address = cleaned_data.get("address")
        phone = cleaned_data.get("phone_number")

        if delivery_type == "delivery" and not address:
            self.add_error("address", "Укажите адрес для доставки")
        elif delivery_type == "pickup":
            cleaned_data["address"] = "Самовывоз"
            
        # Делаем поле телефона необязательным для заказов "на месте"
        if delivery_type == "cafe" and not phone:
            # Если телефон не указан для заказа "на месте", это допустимо
            pass
        elif not phone:
            # Для других типов доставки телефон обязателен
            self.add_error("phone_number", "Укажите номер телефона")

        return cleaned_data



