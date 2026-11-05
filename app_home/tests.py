import tempfile
from datetime import date, datetime, time
from unittest import mock

from django.contrib.auth.models import AnonymousUser, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template import Context, Template
from django.templatetags.static import static
from django.test import TestCase, Client, RequestFactory, override_settings
from django.urls import reverse
from django.contrib.messages import get_messages
from django.utils import timezone

from app_home.context_processors import canonical_context
from app_home.forms import FeedbackForm, VacancyApplicationForm
from app_home.models import CafeBranch, Feedback, Vacancy, VacancyApplication, InfoPage, SiteSettings, Announcement, WorkingHours
from app_home.templatetags.static_version import static_v
from app_home.working_hours import (
    get_current_shift,
    is_order_time_allowed,
    order_time_restriction_message,
)


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


class OfferViewTests(TestCase):
    """Тесты для публичной оферты"""

    def setUp(self):
        self.client = Client()
        self.url = reverse('app_home:offer')

    def test_offer_view_get(self):
        """Тест GET-запроса к странице публичной оферты"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app_home/offer.html')
        self.assertEqual(response.context['title'], 'Публичная оферта')
        self.assertContains(response, '1. Предмет оферты')


class SeoCanonicalTests(TestCase):
    """Канонические URL и правила для поисковых роботов."""

    def test_canonical_url_ignores_query_string(self):
        request = RequestFactory().get("/catalog/item/picca/?size=1&utm_source=yandex")
        with override_settings(DOMAIN_NAME="https://solo-pizza.by"):
            canonical_url = canonical_context(request)["canonical_url"]

        self.assertEqual(canonical_url, "https://solo-pizza.by/catalog/item/picca/")

    def test_robots_txt_has_clean_param_directives(self):
        response = self.client.get("/robots.txt")

        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        self.assertIn("Clean-param:", content)
        self.assertIn("utm_source", content)
        self.assertIn("size /catalog/item/", content)


class InfoPageModelTests(TestCase):
    """Тесты модели контента страницы «Информация»."""

    def test_get_solo_returns_singleton(self):
        """Единая запись контента создаётся один раз и переиспользуется."""
        first = InfoPage.get_solo()
        second = InfoPage.get_solo()

        self.assertEqual(first.pk, second.pk)
        self.assertEqual(InfoPage.objects.count(), 1)

    def test_get_solo_creates_default_record(self):
        """При первом обращении создаётся запись с настройками по умолчанию."""
        InfoPage.objects.all().delete()
        info = InfoPage.get_solo()

        self.assertTrue(InfoPage.objects.filter(pk=info.pk).exists())


class InfoViewTests(TestCase):
    """Тесты страницы информации о компании."""

    def setUp(self):
        self.url = reverse("app_home:info")

    def test_info_view_get(self):
        """GET-запрос к странице информации о компании."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "app_home/info.html")
        self.assertIn("info", response.context)

    def test_info_content_rendered_from_db(self):
        """Текст страницы берётся из модели InfoPage, а не из шаблона."""
        info = InfoPage.objects.create(
            promo_heading="О компании Solo Pizza",
            promo_description="Описание компании из базы",
            philosophy_title="Наша философия",
            philosophy_text="Миссия компании из базы",
            quality_title="Контроль качества",
            quality_text="Текст о качестве из базы",
            quality_training_text="Текст об обучении из базы",
            delivery_title="Доставка",
            delivery_text="Текст о доставке из базы",
            delivery_app_text="Текст об приложении из базы",
            address_title="Наш адрес",
            address_text="Текст об адресе из базы",
            steps_title="Оформление заказа",
            step_1_text="Шаг 1 из базы",
            step_2_text="Шаг 2 из базы",
            step_3_text="Шаг 3 из базы",
            contacts_title="Связаться с нами",
            contacts_text="Текст связи из базы",
            contacts_text_2="Дополнительный текст связи из базы",
        )
        branch = CafeBranch.objects.create(name="Тестовый филиал", address="ул. Тестовая, 1")

        response = self.client.get(self.url)

        self.assertContains(response, "Описание компании из базы")
        self.assertContains(response, "Миссия компании из базы")
        self.assertContains(response, "Текст о качестве из базы")
        self.assertContains(response, "Текст об обучении из базы")
        self.assertContains(response, "Текст о доставке из базы")
        self.assertContains(response, "Текст об приложении из базы")
        self.assertContains(response, "Текст об адресе из базы")
        self.assertContains(response, "Шаг 1 из базы")
        self.assertContains(response, "Шаг 3 из базы")
        self.assertContains(response, "Текст связи из базы")
        self.assertContains(response, "Дополнительный текст связи из базы")


class SiteSettingsTests(TestCase):
    """Тесты настроек сайта: логотип в шапке и доступность заказов."""

    def setUp(self):
        self.client = Client()
        self.home_url = reverse("app_home:home")

    def test_get_solo_returns_singleton(self):
        first = SiteSettings.get_solo()
        second = SiteSettings.get_solo()

        self.assertEqual(first.pk, second.pk)
        self.assertEqual(SiteSettings.objects.count(), 1)

    def test_header_uses_default_logo_without_upload(self):
        SiteSettings.objects.all().delete()

        response = self.client.get(self.home_url)

        self.assertContains(response, "static/img/sp.png")

    def test_header_uses_uploaded_logo(self):
        image = SimpleUploadedFile(
            "logo.png",
            b"\x89PNG\r\n\x1a\n" + b"0" * 64,
            content_type="image/png",
        )

        with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
            settings_obj = SiteSettings.get_solo()
            settings_obj.logo = image
            settings_obj.logo_alt = "Логотип Solo Pizza"
            settings_obj.save()

            response = self.client.get(self.home_url)

            self.assertContains(response, settings_obj.logo.url)
            self.assertContains(response, 'alt="Логотип Solo Pizza"')
            self.assertNotContains(response, "static/img/sp.png")

    def test_orders_are_available_by_default(self):
        self.assertTrue(SiteSettings.is_orders_available())

    def test_orders_can_be_disabled_through_site_settings(self):
        settings_obj = SiteSettings.get_solo()
        settings_obj.orders_available = False
        settings_obj.save()

        self.assertFalse(SiteSettings.is_orders_available())

    def test_staff_and_superuser_can_order_when_orders_disabled(self):
        settings_obj = SiteSettings.get_solo()
        settings_obj.orders_available = False
        settings_obj.save()
        staff = User.objects.create_user(username="staff", password="Sup3r-secret", is_staff=True)
        superuser = User.objects.create_superuser(username="admin", password="Sup3r-secret")
        regular = User.objects.create_user(username="regular", password="Sup3r-secret")

        self.assertTrue(SiteSettings.is_orders_available(staff))
        self.assertTrue(SiteSettings.is_orders_available(superuser))
        self.assertFalse(SiteSettings.is_orders_available(regular))

    def test_cart_blocks_checkout_when_orders_disabled(self):
        settings_obj = SiteSettings.get_solo()
        settings_obj.orders_available = False
        settings_obj.save()

        response = self.client.get(reverse("app_cart:view_cart"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "В настоящий момент оформление новых заказов недоступно")

    def test_cart_allows_checkout_when_orders_enabled(self):
        SiteSettings.get_solo()

        response = self.client.get(reverse("app_cart:view_cart"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "В настоящий момент оформление новых заказов недоступно")

    def test_cart_does_not_block_staff_when_orders_disabled(self):
        settings_obj = SiteSettings.get_solo()
        settings_obj.orders_available = False
        settings_obj.save()
        staff = User.objects.create_user(username="staff", password="Sup3r-secret", is_staff=True)
        self.client.force_login(staff)

        response = self.client.get(reverse("app_cart:view_cart"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "В настоящий момент оформление новых заказов недоступно")

    def test_snow_disabled_by_default(self):
        self.assertFalse(SiteSettings.get_solo().snow_enabled)

    def test_snow_script_absent_when_disabled(self):
        response = self.client.get(self.home_url)

        self.assertNotContains(response, "js/snow.js")

    def test_snow_script_included_when_enabled(self):
        settings_obj = SiteSettings.get_solo()
        settings_obj.snow_enabled = True
        settings_obj.save()

        response = self.client.get(self.home_url)

        self.assertContains(response, "js/snow.js")


class StaticVersionTests(TestCase):
    """Тесты версионирования статики для сброса кеша браузера."""

    def test_static_v_adds_version_from_mtime(self):
        with tempfile.NamedTemporaryFile(suffix=".css") as tmp:
            with mock.patch(
                "app_home.templatetags.static_version.finders.find",
                return_value=tmp.name,
            ):
                rendered = static_v("css/styles.css")

        self.assertTrue(rendered.startswith(static("css/styles.css") + "?v="))
        self.assertRegex(rendered, r"\?v=\d+$")

    def test_static_v_falls_back_when_file_missing(self):
        with mock.patch(
            "app_home.templatetags.static_version.finders.find",
            return_value=None,
        ), override_settings(STATIC_ROOT=None):
            rendered = static_v("css/styles.css")

        self.assertEqual(rendered, static("css/styles.css"))

    def test_base_template_uses_versioned_stylesheet(self):
        response = self.client.get(reverse("app_home:home"))

        self.assertEqual(response.status_code, 200)
        self.assertRegex(
            response.content.decode(),
            r'href="(?:/)?static/css/styles\.css\?v=\d+"',
        )


class AnnouncementTests(TestCase):
    """Блок объявлений на главной странице."""

    def test_home_shows_only_active_announcements(self):
        Announcement.objects.create(text="Активное объявление", is_active=True)
        Announcement.objects.create(text="Скрытое объявление", is_active=False)

        response = self.client.get(reverse("app_home:home"))

        self.assertContains(response, "Активное объявление")
        self.assertNotContains(response, "Скрытое объявление")


class WorkingHoursTests(TestCase):
    """Приём заказов по графику филиала с отсечкой за 30 минут до закрытия."""

    THURSDAY = date(2026, 11, 5)
    FRIDAY = date(2026, 11, 6)

    def setUp(self):
        self.branch = CafeBranch.objects.create(name="Центральный", address="ул. Ленина, 1")
        self.other_branch = CafeBranch.objects.create(name="Северный", address="ул. Мира, 2")

    def add_schedule(self, branch, opening, closing, day_of_week=4, is_closed=False):
        return WorkingHours.objects.create(
            branch=branch,
            day_of_week=day_of_week,
            opening_time=opening,
            closing_time=closing,
            is_closed=is_closed,
        )

    def at(self, day, hour, minute=0):
        return timezone.make_aware(datetime.combine(day, time(hour, minute)))

    def test_orders_stop_thirty_minutes_before_closing(self):
        self.add_schedule(self.branch, time(11), time(23))

        self.assertTrue(is_order_time_allowed(self.branch, at=self.at(self.THURSDAY, 22, 29)))
        self.assertFalse(is_order_time_allowed(self.branch, at=self.at(self.THURSDAY, 22, 30)))
        self.assertFalse(is_order_time_allowed(self.branch, at=self.at(self.THURSDAY, 23, 0)))

    def test_orders_start_at_opening_time(self):
        self.add_schedule(self.branch, time(11), time(23))

        self.assertFalse(is_order_time_allowed(self.branch, at=self.at(self.THURSDAY, 10, 59)))
        self.assertTrue(is_order_time_allowed(self.branch, at=self.at(self.THURSDAY, 11, 0)))

    def test_closed_day_blocks_orders(self):
        self.add_schedule(self.branch, time(11), time(23), is_closed=True)

        self.assertFalse(is_order_time_allowed(self.branch, at=self.at(self.THURSDAY, 12, 0)))

    def test_day_without_schedule_blocks_orders(self):
        self.assertFalse(is_order_time_allowed(self.branch, at=self.at(self.THURSDAY, 12, 0)))

    def test_staff_and_superuser_can_order_at_any_time(self):
        self.add_schedule(self.branch, time(11), time(23), is_closed=True)
        late = self.at(self.THURSDAY, 23, 30)
        staff = User.objects.create_user(username="staff", password="Sup3r-secret", is_staff=True)
        superuser = User.objects.create_superuser(username="admin", password="Sup3r-secret")

        self.assertTrue(is_order_time_allowed(self.branch, staff, at=late))
        self.assertTrue(is_order_time_allowed(self.branch, superuser, at=late))

    def test_each_branch_uses_its_own_schedule(self):
        self.add_schedule(self.branch, time(11), time(23))
        self.add_schedule(self.other_branch, time(11), time(20))
        moment = self.at(self.THURSDAY, 20, 30)

        self.assertTrue(is_order_time_allowed(self.branch, at=moment))
        self.assertFalse(is_order_time_allowed(self.other_branch, at=moment))

    def test_overnight_shift_uses_previous_day_schedule(self):
        self.add_schedule(self.branch, time(22), time(2))

        self.assertFalse(is_order_time_allowed(self.branch, at=self.at(self.THURSDAY, 21, 59)))
        self.assertTrue(is_order_time_allowed(self.branch, at=self.at(self.FRIDAY, 1, 29)))
        self.assertFalse(is_order_time_allowed(self.branch, at=self.at(self.FRIDAY, 1, 30)))

    def test_current_shift_is_found_after_midnight(self):
        schedule = self.add_schedule(self.branch, time(22), time(2))

        shift = get_current_shift(self.branch, at=self.at(self.FRIDAY, 1, 0))

        self.assertIsNotNone(shift)
        self.assertEqual(shift.schedule, schedule)
        self.assertEqual(shift.closes_at, self.at(self.FRIDAY, 2, 0))

    def test_restriction_message_explains_cutoff(self):
        self.add_schedule(self.branch, time(11), time(23))

        message = order_time_restriction_message(self.branch, at=self.at(self.THURSDAY, 22, 45))

        self.assertIn("11:00", message)
        self.assertIn("23:00", message)
        self.assertIn("за 30 минут", message)


class OrderAvailabilityTagTests(TestCase):
    """Шаблонный тег учитывает график выбранного филиала и роль пользователя."""

    THURSDAY = date(2026, 11, 5)

    def setUp(self):
        self.branch = CafeBranch.objects.create(name="Центральный", address="ул. Ленина, 1")
        WorkingHours.objects.create(
            branch=self.branch,
            day_of_week=4,
            opening_time=time(11),
            closing_time=time(23),
        )
        self.template = Template(
            "{% load order_availability %}{% are_orders_available as available %}{{ available }}"
        )

    def render_tag(self, at, user=None):
        request = RequestFactory().get("/")
        request.user = user or AnonymousUser()
        with mock.patch("app_home.working_hours._now", return_value=at):
            return self.template.render(Context({"request": request, "selected_branch": self.branch}))

    def at(self, hour, minute=0):
        return timezone.make_aware(datetime.combine(self.THURSDAY, time(hour, minute)))

    def test_tag_allows_checkout_during_working_hours(self):
        self.assertEqual(self.render_tag(self.at(12, 0)), "True")

    def test_tag_disables_checkout_during_last_thirty_minutes(self):
        self.assertEqual(self.render_tag(self.at(22, 45)), "False")

    def test_tag_allows_staff_outside_working_hours(self):
        staff = User.objects.create_user(username="staff", password="Sup3r-secret", is_staff=True)

        self.assertEqual(self.render_tag(self.at(23, 30), user=staff), "True")

    def test_tag_allows_staff_when_site_orders_disabled(self):
        settings_obj = SiteSettings.get_solo()
        settings_obj.orders_available = False
        settings_obj.save()
        staff = User.objects.create_user(username="staff", password="Sup3r-secret", is_staff=True)

        self.assertEqual(self.render_tag(self.at(12, 0), user=staff), "True")

    def test_tag_blocks_regular_user_when_site_orders_disabled(self):
        settings_obj = SiteSettings.get_solo()
        settings_obj.orders_available = False
        settings_obj.save()
        regular = User.objects.create_user(username="regular", password="Sup3r-secret")

        self.assertEqual(self.render_tag(self.at(12, 0), user=regular), "False")
