import re

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser


def clean_phone_number(phone_number):
    """
    Очищает номер телефона от всех символов, кроме цифр.
    """
    return re.sub(r'[^0-9]', '', phone_number)


class PhoneRegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Настройка поля username (номер телефона)
        self.fields['username'].widget.attrs.update({
            'placeholder': 'Введите номер телефона (только цифры)',
            'name': 'username',
            'class': 'input-phone form-control',
        })

        self.fields['password1'].widget.attrs.update({
            'type': 'password',
            'name': 'password1',
            'placeholder': 'Введите пароль',
            'class': 'input-password1 form-control',
        })

        self.fields['password2'].widget.attrs.update({
            'type': 'password',
            'name': 'password2',
            'placeholder': 'Подтвердите пароль',
            'class': 'input-password2 form-control',
        })

    def clean_username(self):
        """
        Валидация: username должен содержать только цифры.
        """
        username = clean_phone_number(self.cleaned_data.get('username'))
        if not username.isdigit():
            raise forms.ValidationError("Номер телефона должен содержать только цифры.")
        return username


class PhoneAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Номер телефона",
        max_length=15,
        widget=forms.TextInput(attrs={
            'placeholder': 'Введите номер телефона (только цифры)',
            'name': 'username',
            'class': 'input-phone form-control',
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Настройка поля password
        self.fields['password'].widget.attrs.update({
            'type': 'password',
            'name': 'password',
            'placeholder': 'Введите пароль',
            'class': 'input-password form-control',
        })

    def clean_username(self):
        """
        Валидация: username должен содержать только цифры.
        """
        username = clean_phone_number(self.cleaned_data.get('username'))
        if not username.isdigit():
            raise forms.ValidationError("Номер телефона должен содержать только цифры.")
        return username
