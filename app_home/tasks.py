from celery import shared_task
import requests
from django.conf import settings
from app_home.models import Feedback


@shared_task
def send_feedback_notification(feedback_id):
    """
    Отправляет уведомление о новом вопросе/предложении в Telegram
    """
    try:
        feedback = Feedback.objects.get(id=feedback_id)

        # Получаем токен и ID чата из настроек
        bot_token = getattr(settings, 'BOT_TOKEN', None)
        chat_id = getattr(settings, 'CHAT_ID', None)

        if not bot_token or not chat_id:
            return "Отсутствуют настройки для уведомлений в Telegram"

        # Формируем сообщение
        feedback_text = (
            f'НОВЫЙ ВОПРОС/ПРЕДЛОЖЕНИЕ\n\n'
            f'Имя: {feedback.name}\n'
            f'Телефон: {feedback.phone}\n'
            f'Сообщение: {feedback.message}\n'
            f'Дата отправки: {feedback.created_at.strftime("%d.%m.%Y %H:%M:%S")}\n'
        )

        # Отправляем сообщение в Telegram
        url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
        params = {
            'chat_id': chat_id,
            'text': feedback_text
        }

        try:
            response = requests.get(url=url, params=params)
        except requests.exceptions.RequestException as e:
            return f"Ошибка при отправке запроса в Telegram: {str(e)}"

        if response.status_code != 200:
            return f"Ошибка при отправке уведомления: {response.status_code} - {response.text}"

        return f"Уведомление о вопросе/предложении #{feedback_id} отправлено"

    except Feedback.DoesNotExist:
        return f"Объект Feedback с id {feedback_id} не найден"
    except Exception as e:
        return f"Ошибка при отправке уведомления: {str(e)}"
