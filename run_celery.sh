#!/bin/bash

# Скрипт для запуска Celery worker и Celery Beat

# Переходим в директорию проекта
cd "$(dirname "$0")"

# Активируем виртуальное окружение, если оно используется
# Раскомментируйте следующие строки, если используете virtualenv
# source venv/bin/activate

# Запускаем Celery worker и Celery Beat в фоновом режиме
echo "Запуск Celery worker..."
celery -A SoloPizza worker --loglevel=info --detach

echo "Запуск Celery Beat..."
celery -A SoloPizza beat --loglevel=info