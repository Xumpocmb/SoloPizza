#!/bin/bash

# Скрипт для запуска Celery Beat (планировщик задач)

# Переходим в директорию проекта
cd "$(dirname "$0")"

# Устанавливаем переменную окружения DJANGO_SETTINGS_MODULE
export DJANGO_SETTINGS_MODULE="SoloPizza.settings"

# Активируем виртуальное окружение, если оно используется
# Раскомментируйте следующие строки, если используете virtualenv
# source venv/bin/activate

# Запускаем Celery Beat
celery -A SoloPizza beat --loglevel=info