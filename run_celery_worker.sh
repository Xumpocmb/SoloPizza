#!/bin/bash

# Скрипт для запуска Celery worker

# Переходим в директорию проекта
cd "$(dirname "$0")"

# Активируем виртуальное окружение, если оно используется
# Раскомментируйте следующие строки, если используете virtualenv
# source venv/bin/activate

# Запускаем Celery worker
celery -A SoloPizza worker --loglevel=info