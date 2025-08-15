# SoloPizza

Проект веб-приложения для пиццерии Solo Pizza - полнофункциональный интернет-магазин с каталогом товаров, корзиной, оформлением заказов, системой отзывов и личным кабинетом пользователя.

## Технологии

- **Backend**: Django 5.1.7
- **Аутентификация**: django-allauth (включая вход через Google)
- **Асинхронные задачи**: Celery 5.3.6 с Redis
- **Планировщик задач**: django-celery-beat
- **Мониторинг задач**: Flower
- **База данных**: SQLite (разработка), PostgreSQL (продакшн)
- **Деплой**: Gunicorn

## Структура проекта

- `SoloPizza/` - основной пакет Django проекта
  - `celery.py` - конфигурация Celery
  - `celerybeat_schedule.py` - расписание периодических задач
  - `settings.py` - настройки проекта
  - `urls.py` - маршрутизация URL
- `app_catalog/` - каталог товаров
  - Управление категориями и товарами
  - Периодические скидки и акции
- `app_cart/` - корзина покупок
  - Добавление/удаление товаров
  - Расчет стоимости
- `app_home/` - главная страница и общие функции
  - Контактная информация
  - Вакансии
  - Обратная связь
- `app_order/` - оформление и управление заказами
  - Создание и отслеживание заказов
  - История заказов пользователя
- `app_reviews/` - отзывы пользователей
  - Добавление и модерация отзывов
- `app_user/` - управление пользователями
  - Регистрация и авторизация
  - Личный кабинет

## Запуск проекта

### Разработка

```bash
# Клонирование репозитория
git clone https://github.com/username/SoloPizza.git
cd SoloPizza

# Создание и активация виртуального окружения
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt

# Запуск проекта
python manage.py migrate
python manage.py runserver
```

### Продакшн

```bash
# Запуск с помощью Gunicorn
gunicorn SoloPizza.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

## Celery и асинхронные задачи

### Доступные задачи

- **app_order**: Ежедневная очистка заказов
- **app_catalog**: Управление категорией "Комбо" по расписанию

### Запуск Celery

```bash
# Запуск воркера и планировщика
./run_celery.sh

# Запуск только воркера
./run_celery_worker.sh

# Запуск только планировщика
./run_celery_beat.sh

# Запуск конкретной задачи
./run_celery_task.sh app_catalog.tasks.activate_combo_category

# Запуск мониторинга Flower
./run_celery_flower.sh  # Доступен на http://localhost:5555

# Остановка всех процессов Celery
./stop_celery.sh
```

## Обслуживание

### Очистка Redis и перезапуск веб-сервера

Для очистки кэша Redis и перезапуска веб-сервера:

```bash
# Очистка кэша Redis
redis-cli flushall

# Перезапуск Gunicorn (если используется systemd)
sudo systemctl restart gunicorn

# Или перезапуск вручную
pkill -f gunicorn
gunicorn SoloPizza.wsgi:application --bind 0.0.0.0:8000 --workers 3
```