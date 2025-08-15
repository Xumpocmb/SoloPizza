#!/bin/bash

# Скрипт для запуска Celery Beat (планировщик задач)

# Переходим в директорию проекта
cd "$(dirname "$0")"

# Активируем виртуальное окружение, если оно используется
# Раскомментируйте следующие строки, если используете virtualenv
# source venv/bin/activate

# Запускаем Celery Beat
celery -A SoloPizza beat --loglevel=info