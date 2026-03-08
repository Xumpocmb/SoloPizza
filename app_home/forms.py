from django import forms
from .models import VacancyApplication, Feedback


class FeedbackForm(forms.ModelForm):
    """Форма для вопросов и предложений"""
    
    class Meta:
        model = Feedback
        fields = ['name', 'phone', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите ваше имя'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '375XXXXXXXXXXXX (минимум 12 цифр)'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Введите ваш вопрос или предложение', 'rows': 5}),
        }
        
    def clean_phone(self):
        """Валидация номера телефона"""
        phone = self.cleaned_data.get('phone')
        
        # Удаляем все нецифровые символы
        phone = ''.join(c for c in phone if c.isdigit())
        
        # Проверяем длину номера
        if len(phone) < 12:
            raise forms.ValidationError("Номер телефона должен содержать не менее 12 цифр.")
            
        return phone


class VacancyApplicationForm(forms.ModelForm):
    """Форма для отклика на вакансию"""
    
    class Meta:
        model = VacancyApplication
        fields = ['name', 'age', 'phone', 'experience_years', 'work_experience']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите ваше ФИО'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Введите ваш возраст', 'min': '16', 'max': '100'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '375XXXXXXXXXXXX (минимум 12 цифр)'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Стаж работы в годах', 'min': '0', 'max': '50'}),
            'work_experience': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Опишите ваш опыт работы', 'rows': 5}),
        }
        
    def clean_phone(self):
        """Валидация номера телефона"""
        phone = self.cleaned_data.get('phone')
        
        # Удаляем все нецифровые символы
        phone = ''.join(c for c in phone if c.isdigit())
        
        # Проверяем длину номера
        if len(phone) < 12:
            raise forms.ValidationError("Номер телефона должен содержать не менее 12 цифр.")
            
        return phone
