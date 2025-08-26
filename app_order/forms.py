from django import forms
from django.forms import inlineformset_factory
from django.contrib import messages
from django.utils import timezone
from app_catalog.models import AddonParams, PizzaSauce, ProductVariant, BoardParams, Product
from app_order.models import Order, OrderItem
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

    def save(self, commit=True, user=None):
        order = super().save(commit=False)
        if user:
            order.user = user
            order.payment_status = True if user.is_staff else False
            order.status = "new"
        
        # Автозаполнение поля delivery_by на основе ready_by
        ready_by = order.ready_by
        delivery_by = order.delivery_by
        if ready_by and not delivery_by:
            order.ready_by = ready_by
            order.delivery_by = ready_by + timezone.timedelta(minutes=30)

        if commit:
            order.save()
        return order


class OrderEditForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["delivery_type", "payment_method", "payment_status", "customer_name", "phone_number", "address",
                  "ready_by", "delivery_by", "comment", "is_partner", "partner_discount_percent"]
        widgets = {
            "delivery_type": forms.RadioSelect(attrs={"class": "custom-radio-list"}),  # Просто указываете класс списка
            "payment_method": forms.RadioSelect(attrs={"class": "custom-radio-list"}),
            "payment_status": forms.CheckboxInput(attrs={"class": "custom-checkbox-list"}),
            "customer_name": forms.TextInput(attrs={"class": "form-input"}),
            "phone_number": forms.TextInput(attrs={"class": "form-input"}),
            "ready_by": forms.DateTimeInput(attrs={"class": "form-input", "type": "datetime-local", "format": "%Y-%m-%dT%H:%M"}),
            "delivery_by": forms.DateTimeInput(attrs={"class": "form-input", "type": "datetime-local", "format": "%Y-%m-%dT%H:%M"}),
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
        
    def save(self, commit=True):
        order = super().save(commit=False)
        
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


class OrderItemEditForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ["variant", "quantity", "board1", "board2", "sauce", "addons"]
        widgets = {
            "variant": forms.Select(attrs={"class": "form-select"}),
            "quantity": forms.NumberInput(attrs={"class": "form-input quantity-edit", "min": 1, "max": 20}),
            "board1": forms.Select(attrs={"class": "form-select board1-edit"}),
            "board2": forms.Select(attrs={"class": "form-select board2-edit"}),
            "sauce": forms.Select(attrs={"class": "form-select sauce-edit"}),
            "addons": forms.SelectMultiple(attrs={"class": "form-select multiple-select"}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)  # Получаем request из kwargs
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, "product"):
            self._initialize_form_fields()

    def _initialize_form_fields(self):
        """Инициализирует все поля формы на основе продукта"""
        product = self.instance.product
        self.fields["variant"].queryset = ProductVariant.objects.filter(product=product)

        # Для пицц и кальцоне
        if product.category.name in ["Пицца", "Кальцоне"]:
            self.fields["sauce"].queryset = PizzaSauce.objects.filter(is_active=True)
            self._update_size_dependent_fields()
        else:
            self._hide_pizza_specific_fields()

    def _update_size_dependent_fields(self):
        """Обновляет поля, зависящие от размера (борты и добавки)"""
        size = self.instance.variant.size if self.instance.variant else None
        if size:
            self.fields["board1"].queryset = BoardParams.objects.filter(size=size)
            self.fields["board2"].queryset = BoardParams.objects.filter(size=size)
            self.fields["addons"].queryset = AddonParams.objects.filter(addon__is_active=True,
                                                                        size=size).select_related("addon")
        else:
            self.fields["board1"].queryset = BoardParams.objects.none()
            self.fields["board2"].queryset = BoardParams.objects.none()
            self.fields["addons"].queryset = AddonParams.objects.none()

    def _hide_pizza_specific_fields(self):
        """Скрывает поля, специфичные для пиццы"""
        for field in ["sauce", "board1", "board2", "addons"]:
            self.fields[field].queryset = self.fields[field].queryset.model.objects.none()
            self.fields[field].widget = forms.HiddenInput()

    def _find_board_replacement(self, original_board, new_size):
        """Находит борт того же типа для нового размера"""
        if not original_board or not new_size:
            return None
        return BoardParams.objects.filter(
            board__name=original_board.board.name,
            size=new_size
        ).first()

    def _find_addon_replacement(self, original_addon, new_size):
        """Находит добавку того же типа для нового размера"""
        if not original_addon or not new_size:
            return None
        return AddonParams.objects.filter(
            addon__name=original_addon.addon.name,
            size=new_size
        ).first()

    def clean(self):
        cleaned_data = super().clean()
        variant = cleaned_data.get("variant")

        if variant and hasattr(variant, 'size'):
            if self.instance.variant and (variant.size != self.instance.variant.size):
                new_size = variant.size

                cleaned_data["board1"] = self._find_board_replacement(
                    self.instance.board1, new_size
                )
                cleaned_data["board2"] = self._find_board_replacement(
                    self.instance.board2, new_size
                )

                if self.instance.addons.exists():
                    new_addons = []
                    for addon in self.instance.addons.all():
                        replacement = self._find_addon_replacement(addon, new_size)
                        if replacement:
                            new_addons.append(replacement.id)

                    cleaned_data["addons"] = new_addons

                self.instance.variant = variant
                self._update_size_dependent_fields()

                # Добавляем сообщение
                if self.request:
                    messages.info(
                        self.request,
                        f"Борты и добавки автоматически изменены для размера {new_size.name}"
                    )

        return cleaned_data


OrderItemFormSet = inlineformset_factory(Order, OrderItem, form=OrderItemEditForm, extra=0, can_delete=False,
                                         fields=["variant", "quantity", "board1", "board2", "sauce", "addons"])


class AddToOrderForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Товар"
    )
    variant = forms.ModelChoiceField(
        queryset=ProductVariant.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Вариант"
    )
    quantity = forms.IntegerField(
        min_value=1,
        max_value=10,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        label="Количество"
    )
    
    # Поля для пиццы / кальцоне
    board1 = forms.ModelChoiceField(
        queryset=BoardParams.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Борт 1"
    )
    board2 = forms.ModelChoiceField(
        queryset=BoardParams.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Борт 2"
    )
    sauce = forms.ModelChoiceField(
        queryset=PizzaSauce.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Соус"
    )
    addons = forms.ModelMultipleChoiceField(
        queryset=AddonParams.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-select multiple-select'}),
        label="Добавки"
    )

    def __init__(self, *args, **kwargs):
        self.order = kwargs.pop('order', None)
        super().__init__(*args, **kwargs)
        
        # Добавляем атрибуты data-category для всех продуктов
        product_field = self.fields['product']
        product_field.widget.attrs['class'] = 'form-select'
        
        # Получаем все продукты и устанавливаем атрибуты data-category
        products = Product.objects.all()
        choices = []
        for product in products:
            option_attrs = {'data-category': product.category.name}
            choices.append((product.id, product.name))
            
        product_field.choices = choices
        
        # Добавляем JavaScript для установки атрибутов data-category
        import json
        self.product_categories = json.dumps({str(p.id): p.category.name for p in products})
        
        # Если форма уже заполнена и выбран продукт
        if args and 'product' in args[0]:
            product_id = args[0].get('product')
            try:
                product = Product.objects.get(id=product_id)
                self.fields['variant'].queryset = ProductVariant.objects.filter(product=product)
                
                # Если выбран вариант, настраиваем поля для пиццы
                if 'variant' in args[0]:
                    variant_id = args[0].get('variant')
                    try:
                        variant = ProductVariant.objects.get(id=variant_id)
                        if variant.size and product.category.name in ["Пицца", "Кальцоне"]:
                            self.fields['board1'].queryset = BoardParams.objects.filter(size=variant.size)
                            self.fields['board2'].queryset = BoardParams.objects.filter(size=variant.size)
                            self.fields['addons'].queryset = AddonParams.objects.filter(size=variant.size)
                    except ProductVariant.DoesNotExist:
                        pass
            except Product.DoesNotExist:
                pass

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        variant = cleaned_data.get('variant')
        board1 = cleaned_data.get('board1')
        board2 = cleaned_data.get('board2')
        
        # Проверка, что вариант принадлежит выбранному продукту
        if product and variant and variant.product != product:
            self.add_error('variant', 'Выбранный вариант не принадлежит выбранному товару')
        
        # Проверка на одинаковые борты
        if board1 and board2 and board1.id == board2.id:
            self.add_error('board2', 'Нельзя выбрать одинаковые борты')
            
        return cleaned_data
