from django import forms
from django.utils.translation import gettext_lazy as _
from .models import VacancyApplication, Feedback


class FeedbackForm(forms.ModelForm):
    """Форма для вопросов и предложений"""
    
    class Meta:
        model = Feedback
        fields = ['name', 'phone', 'message']
        labels = {
            'name': _('Имя'),
            'phone': _('Номер телефона'),
            'message': _('Сообщение'),
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Введите ваше имя')}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('375XXXXXXXXXXXX (минимум 12 цифр)')}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'placeholder': _('Введите ваш вопрос или предложение'), 'rows': 5}),
        }
        
    def clean_phone(self):
        """Валидация номера телефона"""
        phone = self.cleaned_data.get('phone')
        
        # Удаляем все нецифровые символы
        phone = ''.join(c for c in phone if c.isdigit())
        
        # Проверяем длину номера
        if len(phone) < 12:
            raise forms.ValidationError(_("Номер телефона должен содержать не менее 12 цифр."))
            
        return phone


class VacancyApplicationForm(forms.ModelForm):
    """Форма для отклика на вакансию"""
    
    class Meta:
        model = VacancyApplication
        fields = ['name', 'age', 'phone', 'experience_years', 'work_experience']
        labels = {
            'name': _('ФИО'),
            'age': _('Возраст'),
            'phone': _('Номер телефона'),
            'experience_years': _('Стаж работы (лет)'),
            'work_experience': _('Опыт работы'),
        }
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Введите ваше ФИО')}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('Введите ваш возраст'), 'min': '16', 'max': '100'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('375XXXXXXXXXXXX (минимум 12 цифр)')}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': _('Стаж работы в годах'), 'min': '0', 'max': '50'}),
            'work_experience': forms.Textarea(attrs={'class': 'form-control', 'placeholder': _('Опишите ваш опыт работы'), 'rows': 5}),
        }
        
    def clean_phone(self):
        """Валидация номера телефона"""
        phone = self.cleaned_data.get('phone')
        
        # Удаляем все нецифровые символы
        phone = ''.join(c for c in phone if c.isdigit())
        
        # Проверяем длину номера
        if len(phone) < 12:
            raise forms.ValidationError(_("Номер телефона должен содержать не менее 12 цифр."))
            
        return phone
