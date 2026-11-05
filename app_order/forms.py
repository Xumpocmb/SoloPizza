from decimal import Decimal

from django import forms
from django.utils import timezone
from app_order.models import Order
from app_home.models import Discount


def validate_delivery_requirements(form):
    """Общие для оформления и правки правила: адрес при доставке, телефон везде, кроме зала."""
    delivery_type = form.cleaned_data.get("delivery_type")

    if delivery_type == "delivery" and not form.cleaned_data.get("address"):
        form.add_error("address", "Укажите адрес для доставки")

    if delivery_type != "cafe" and not form.cleaned_data.get("phone_number"):
        form.add_error("phone_number", "Укажите номер телефона")


class DeliveryValidationMixin:
    """Подмешивает общие правила доставки/телефона в clean() формы."""

    def clean(self):
        cleaned_data = super().clean()
        validate_delivery_requirements(self)
        return cleaned_data


class CheckoutForm(DeliveryValidationMixin, forms.ModelForm):
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

    consent = forms.BooleanField(
        label="Согласие на обработку персональных данных",
        required=True,
        widget=forms.CheckboxInput(attrs={"class": "consent-checkbox"}),
    )

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
        validate_delivery_requirements(self)

        if not cleaned_data.get("consent"):
            self.add_error("consent", "Необходимо дать согласие на обработку персональных данных")

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


class OrderEditForm(DeliveryValidationMixin, forms.ModelForm):
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
        cleaned_data = super().clean()  # включает validate_delivery_requirements

        if cleaned_data.get("delivery_type") == "pickup":
            cleaned_data["address"] = "Самовывоз"

        # Суммы раздельной оплаты сверяются с новым итогом заказа:
        # delivery_type и партнёрские поля меняют сумму после пересчёта
        if self.instance.pk and cleaned_data.get("payment_method") == "split":
            split_total = sum(
                (cleaned_data.get(field) or Decimal("0.00") for field in ("cash_amount", "card_amount", "noname_amount")),
                Decimal("0.00"),
            )

            for field in ("delivery_type", "is_partner", "partner_discount_percent"):
                value = cleaned_data.get(field)
                if value is not None:
                    setattr(self.instance, field, value)

            total_price = Order.objects.get_order_totals(self.instance)["total_price"]

            if abs(split_total - total_price) >= Order.SPLIT_PAYMENT_TOLERANCE:
                self.add_error(
                    None,
                    f"Сумма раздельной оплаты ({split_total:.2f} руб.) "
                    f"не совпадает с итоговой суммой заказа ({total_price:.2f} руб.).",
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
