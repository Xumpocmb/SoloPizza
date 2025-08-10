from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages

from app_home.forms import FeedbackForm, VacancyApplicationForm
from app_home.models import Feedback, Vacancy, VacancyApplication


class VacancyApplyViewTests(TestCase):
    """Тесты для представления отклика на вакансию"""
    
    def setUp(self):
        self.client = Client()
        # Создаем тестовую вакансию
        self.vacancy = Vacancy.objects.create(
            title="Тестовая вакансия",
            description="Описание тестовой вакансии",
            salary="от 1000 BYN",
            is_active=True
        )
        self.url = reverse('app_home:vacancy_apply', args=[self.vacancy.id])
        
    def test_vacancy_apply_view_get(self):
        """Тест GET-запроса к странице отклика на вакансию"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_home/vacancy_apply.html')
        self.assertIsInstance(response.context['form'], VacancyApplicationForm)
        self.assertEqual(response.context['vacancy'], self.vacancy)
        
    def test_vacancy_apply_view_post_valid(self):
        """Тест отправки валидной формы отклика"""
        form_data = {
            'name': 'Тестовый Кандидат',
            'age': 25,
            'phone': '375291234567',
            'experience_years': 3,
            'work_experience': 'Опыт работы тестового кандидата'
        }
        response = self.client.post(self.url, form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что запись создана в базе данных
        self.assertEqual(VacancyApplication.objects.count(), 1)
        application = VacancyApplication.objects.first()
        self.assertEqual(application.name, 'Тестовый Кандидат')
        self.assertEqual(application.age, 25)
        self.assertEqual(application.phone, '375291234567')
        self.assertEqual(application.experience_years, 3)
        self.assertEqual(application.work_experience, 'Опыт работы тестового кандидата')
        self.assertEqual(application.vacancy, self.vacancy)
        
        # Проверяем, что отображается сообщение об успехе
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Ваш отклик успешно отправлен! Мы свяжемся с вами в ближайшее время.')
        
    def test_vacancy_apply_view_post_invalid(self):
        """Тест отправки невалидной формы отклика"""
        # Отправляем форму без обязательных полей
        form_data = {
            'name': '',
            'age': '',
            'phone': '',
            'experience_years': '',
            'work_experience': ''
        }
        response = self.client.post(self.url, form_data)
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что запись не создана в базе данных
        self.assertEqual(VacancyApplication.objects.count(), 0)
        
        # Проверяем, что форма содержит ошибки
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('phone', form.errors)
        
        # Проверяем, что отображается сообщение об ошибке
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Пожалуйста, исправьте ошибки в форме.')
        
    def test_vacancy_apply_view_post_invalid_phone(self):
        """Тест отправки формы с невалидным номером телефона"""
        form_data = {
            'name': 'Тестовый Кандидат',
            'age': 25,
            'phone': '123', # Слишком короткий номер
            'experience_years': 3,
            'work_experience': 'Опыт работы тестового кандидата'
        }
        response = self.client.post(self.url, form_data)
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что запись не создана в базе данных
        self.assertEqual(VacancyApplication.objects.count(), 0)
        
        # Проверяем, что форма содержит ошибки
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)
        
        # Проверяем, что отображается сообщение об ошибке
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Пожалуйста, исправьте ошибки в форме.')
        
    def test_vacancy_apply_nonexistent_vacancy(self):
        """Тест отклика на несуществующую вакансию"""
        url = reverse('app_home:vacancy_apply', args=[999])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class FeedbackFormTests(TestCase):
    """Тесты для формы обратной связи"""
    
    def test_valid_phone_number(self):
        """Тест валидного номера телефона"""
        form_data = {
            'name': 'Тестовый Пользователь',
            'phone': '375291234567',
            'message': 'Тестовое сообщение'
        }
        form = FeedbackForm(data=form_data)
        self.assertTrue(form.is_valid())
        
    def test_phone_number_with_plus(self):
        """Тест номера телефона с плюсом"""
        form_data = {
            'name': 'Тестовый Пользователь',
            'phone': '+375291234567',
            'message': 'Тестовое сообщение'
        }
        form = FeedbackForm(data=form_data)
        self.assertTrue(form.is_valid())
        # Проверяем, что плюс был удален
        self.assertEqual(form.cleaned_data['phone'], '375291234567')
        
    def test_phone_number_with_spaces(self):
        """Тест номера телефона с пробелами"""
        form_data = {
            'name': 'Тестовый Пользователь',
            'phone': '375 29 123 45 67',
            'message': 'Тестовое сообщение'
        }
        form = FeedbackForm(data=form_data)
        self.assertTrue(form.is_valid())
        # Проверяем, что пробелы были удалены
        self.assertEqual(form.cleaned_data['phone'], '375291234567')
        
    def test_phone_number_with_dashes(self):
        """Тест номера телефона с дефисами"""
        form_data = {
            'name': 'Тестовый Пользователь',
            'phone': '375-29-123-45-67',
            'message': 'Тестовое сообщение'
        }
        form = FeedbackForm(data=form_data)
        self.assertTrue(form.is_valid())
        # Проверяем, что дефисы были удалены
        self.assertEqual(form.cleaned_data['phone'], '375291234567')
        
    def test_phone_number_with_parentheses(self):
        """Тест номера телефона со скобками"""
        form_data = {
            'name': 'Тестовый Пользователь',
            'phone': '+375(29)1234567',
            'message': 'Тестовое сообщение'
        }
        form = FeedbackForm(data=form_data)
        self.assertTrue(form.is_valid())
        # Проверяем, что скобки и плюс были удалены
        self.assertEqual(form.cleaned_data['phone'], '375291234567')
        
    def test_phone_number_too_short(self):
        """Тест слишком короткого номера телефона"""
        form_data = {
            'name': 'Тестовый Пользователь',
            'phone': '12345',
            'message': 'Тестовое сообщение'
        }
        form = FeedbackForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)
        
    def test_phone_number_with_letters(self):
        """Тест номера телефона с буквами, но достаточной длины после удаления букв"""
        form_data = {
            'name': 'Тестовый Пользователь',
            'phone': '375abc123456789',
            'message': 'Тестовое сообщение'
        }
        form = FeedbackForm(data=form_data)
        # Форма должна быть валидной, так как буквы будут удалены, а оставшиеся цифры >= 12
        self.assertTrue(form.is_valid())
        # Проверяем, что буквы были удалены
        self.assertEqual(form.cleaned_data['phone'], '375123456789')
        
    def test_phone_number_with_letters_too_short(self):
        """Тест номера телефона с буквами, который становится слишком коротким после удаления букв"""
        form_data = {
            'name': 'Тестовый Пользователь',
            'phone': '375abcdef123',
            'message': 'Тестовое сообщение'
        }
        form = FeedbackForm(data=form_data)
        # Форма не должна быть валидной, так как после удаления букв длина < 12
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)
        
    def test_phone_number_with_special_chars(self):
        """Тест номера телефона со специальными символами, но достаточной длины после их удаления"""
        form_data = {
            'name': 'Тестовый Пользователь',
            'phone': '375@#$123456789',
            'message': 'Тестовое сообщение'
        }
        form = FeedbackForm(data=form_data)
        # Выводим ошибки формы для отладки
        is_valid = form.is_valid()
        if not is_valid:
            print(f"Ошибки формы: {form.errors}")
        # Форма должна быть валидной, так как специальные символы будут удалены, а оставшиеся цифры >= 12
        self.assertTrue(is_valid)
        # Проверяем, что специальные символы были удалены
        self.assertEqual(form.cleaned_data['phone'], '375123456789')
        

class VacancyApplicationFormTests(TestCase):
    """Тесты для формы отклика на вакансию"""
    
    def setUp(self):
        # Создаем тестовую вакансию
        self.vacancy = Vacancy.objects.create(
            title="Тестовая вакансия",
            description="Описание тестовой вакансии",
            salary="от 1000 BYN",
            is_active=True
        )
    
    def test_valid_phone_number(self):
        """Тест валидного номера телефона"""
        form_data = {
            'name': 'Тестовый Кандидат',
            'age': 25,
            'phone': '375291234567',
            'experience_years': 3,
            'work_experience': 'Опыт работы тестового кандидата'
        }
        form = VacancyApplicationForm(data=form_data)
        self.assertTrue(form.is_valid())
        
    def test_phone_number_with_plus(self):
        """Тест номера телефона с плюсом"""
        form_data = {
            'name': 'Тестовый Кандидат',
            'age': 25,
            'phone': '+375291234567',
            'experience_years': 3,
            'work_experience': 'Опыт работы тестового кандидата'
        }
        form = VacancyApplicationForm(data=form_data)
        self.assertTrue(form.is_valid())
        # Проверяем, что плюс был удален
        self.assertEqual(form.cleaned_data['phone'], '375291234567')
        
    def test_phone_number_with_spaces(self):
        """Тест номера телефона с пробелами"""
        form_data = {
            'name': 'Тестовый Кандидат',
            'age': 25,
            'phone': '375 29 123 45 67',
            'experience_years': 3,
            'work_experience': 'Опыт работы тестового кандидата'
        }
        form = VacancyApplicationForm(data=form_data)
        self.assertTrue(form.is_valid())
        # Проверяем, что пробелы были удалены
        self.assertEqual(form.cleaned_data['phone'], '375291234567')
        
    def test_phone_number_with_dashes(self):
        """Тест номера телефона с дефисами"""
        form_data = {
            'name': 'Тестовый Кандидат',
            'age': 25,
            'phone': '375-29-123-45-67',
            'experience_years': 3,
            'work_experience': 'Опыт работы тестового кандидата'
        }
        form = VacancyApplicationForm(data=form_data)
        self.assertTrue(form.is_valid())
        # Проверяем, что дефисы были удалены
        self.assertEqual(form.cleaned_data['phone'], '375291234567')
        
    def test_phone_number_with_parentheses(self):
        """Тест номера телефона со скобками"""
        form_data = {
            'name': 'Тестовый Кандидат',
            'age': 25,
            'phone': '+375(29)1234567',
            'experience_years': 3,
            'work_experience': 'Опыт работы тестового кандидата'
        }
        form = VacancyApplicationForm(data=form_data)
        self.assertTrue(form.is_valid())
        # Проверяем, что скобки и плюс были удалены
        self.assertEqual(form.cleaned_data['phone'], '375291234567')
        
    def test_phone_number_too_short(self):
        """Тест слишком короткого номера телефона"""
        form_data = {
            'name': 'Тестовый Кандидат',
            'age': 25,
            'phone': '12345',
            'experience_years': 3,
            'work_experience': 'Опыт работы тестового кандидата'
        }
        form = VacancyApplicationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)
        
    def test_phone_number_with_letters(self):
        """Тест номера телефона с буквами, но достаточной длины после удаления букв"""
        form_data = {
            'name': 'Тестовый Кандидат',
            'age': 25,
            'phone': '375abc123456789',
            'experience_years': 3,
            'work_experience': 'Опыт работы тестового кандидата'
        }
        form = VacancyApplicationForm(data=form_data)
        # Форма должна быть валидной, так как буквы будут удалены, а оставшиеся цифры >= 12
        self.assertTrue(form.is_valid())
        # Проверяем, что буквы были удалены
        self.assertEqual(form.cleaned_data['phone'], '375123456789')
        
    def test_phone_number_with_letters_too_short(self):
        """Тест номера телефона с буквами, который становится слишком коротким после удаления букв"""
        form_data = {
            'name': 'Тестовый Кандидат',
            'age': 25,
            'phone': '375abcdef123',
            'experience_years': 3,
            'work_experience': 'Опыт работы тестового кандидата'
        }
        form = VacancyApplicationForm(data=form_data)
        # Форма не должна быть валидной, так как после удаления букв длина < 12
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)
        
    def test_phone_number_with_special_chars(self):
        """Тест номера телефона со специальными символами, но достаточной длины после их удаления"""
        form_data = {
            'vacancy': self.vacancy.id,
            'name': 'Тестовый Кандидат',
            'age': 25,
            'phone': '375@#$123456789',
            'experience_years': 3,
            'work_experience': 'Опыт работы тестового кандидата'
        }
        form = VacancyApplicationForm(data=form_data)
        # Выводим ошибки формы для отладки
        is_valid = form.is_valid()
        if not is_valid:
            print(f"Ошибки формы: {form.errors}")
        # Форма должна быть валидной, так как специальные символы будут удалены, а оставшиеся цифры >= 12
        self.assertTrue(is_valid)
        # Проверяем, что специальные символы были удалены
        self.assertEqual(form.cleaned_data['phone'], '375123456789')


class FeedbackViewTests(TestCase):
    """Тесты для представления обратной связи"""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse('app_home:feedback')
        
    def test_feedback_view_get(self):
        """Тест GET-запроса к странице обратной связи"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_home/feedback.html')
        self.assertIsInstance(response.context['form'], FeedbackForm)
        
    def test_feedback_view_post_valid(self):
        """Тест отправки валидной формы"""
        form_data = {
            'name': 'Тестовый Пользователь',
            'phone': '375291234567',
            'message': 'Тестовое сообщение'
        }
        response = self.client.post(self.url, form_data, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что запись создана в базе данных
        self.assertEqual(Feedback.objects.count(), 1)
        feedback = Feedback.objects.first()
        self.assertEqual(feedback.name, 'Тестовый Пользователь')
        self.assertEqual(feedback.phone, '375291234567')
        self.assertEqual(feedback.message, 'Тестовое сообщение')
        
        # Проверяем, что отображается сообщение об успехе
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Ваш вопрос/предложение успешно отправлено! Мы свяжемся с вами в ближайшее время.')
        
    def test_feedback_view_post_invalid(self):
        """Тест отправки невалидной формы"""
        # Отправляем форму без обязательных полей
        form_data = {
            'name': '',
            'phone': '',
            'message': ''
        }
        response = self.client.post(self.url, form_data)
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что запись не создана в базе данных
        self.assertEqual(Feedback.objects.count(), 0)
        
        # Проверяем, что форма содержит ошибки
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('phone', form.errors)
        self.assertIn('message', form.errors)
        
        # Проверяем, что отображается сообщение об ошибке
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Пожалуйста, исправьте ошибки в форме.')
        
    def test_feedback_view_post_invalid_phone(self):
        """Тест отправки формы с невалидным номером телефона"""
        form_data = {
            'name': 'Тестовый Пользователь',
            'phone': '123', # Слишком короткий номер
            'message': 'Тестовое сообщение'
        }
        response = self.client.post(self.url, form_data)
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что запись не создана в базе данных
        self.assertEqual(Feedback.objects.count(), 0)
        
        # Проверяем, что форма содержит ошибки
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('phone', form.errors)
        
        # Проверяем, что отображается сообщение об ошибке
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'Пожалуйста, исправьте ошибки в форме.')
