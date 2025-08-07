from django import forms
from .models import VacancyApplication


class VacancyApplicationForm(forms.ModelForm):
    """Форма для отклика на вакансию"""
    
    class Meta:
        model = VacancyApplication
        fields = ['name', 'age', 'phone', 'experience_years', 'work_experience']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите ваше ФИО'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Введите ваш возраст', 'min': '16', 'max': '100'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+375XXXXXXXXX'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Стаж работы в годах', 'min': '0', 'max': '50'}),
            'work_experience': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Опишите ваш опыт работы', 'rows': 5}),
        }
        
    def clean_phone(self):
        """Валидация номера телефона"""
        phone = self.cleaned_data.get('phone')
        
        # Удаляем все нецифровые символы, кроме +
        phone = ''.join(c for c in phone if c.isdigit() or c == '+')
        
        # Если номер начинается с 8, заменяем на +7
        if phone.startswith('8'):
            phone = '+7' + phone[1:]
        
        # Если номер начинается с 7, добавляем +
        elif phone.startswith('7') and not phone.startswith('+'):
            phone = '+' + phone
            
        # Если номер не начинается с +, добавляем +7
        elif not phone.startswith('+'):
            phone = '+7' + phone
            
        return phone
