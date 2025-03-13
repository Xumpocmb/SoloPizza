from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import UserCreationForm

from app_user.models import CustomUser


class PhoneRegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('phone_number',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Настройка поля phone_number
        self.fields['phone_number'].widget.attrs.update({
            'placeholder': 'Введите номер телефона',
            'name': 'phone_number',
            'class': 'input-phone form-control',
        })

        # Настройка поля password1
        self.fields['password1'].widget.attrs.update({
            'type': 'password',
            'name': 'password1',
            'placeholder': 'Введите пароль',
            'class': 'input-password1 form-control',
        })

        # Настройка поля password2
        self.fields['password2'].widget.attrs.update({
            'type': 'password',
            'name': 'password2',
            'placeholder': 'Подтвердите пароль',
            'class': 'input-password2 form-control',
        })


class PhoneAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="Phone Number", max_length=15)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'placeholder': 'Введите номер телефона',
            'name': 'username',
            'class': 'input-username form-control',
        })
        self.fields['password'].widget.attrs.update({
            'type': 'password',
            'name': 'password',
            'placeholder': 'Введите пароль',
            'class': 'input-password form-control',
        })
