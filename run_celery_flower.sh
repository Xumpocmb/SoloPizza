#!/bin/bash

# Скрипт для запуска Flower - веб-мониторинга задач Celery

# Переходим в директорию проекта
cd "$(dirname "$0")"

# Активируем виртуальное окружение, если оно используется
# Раскомментируйте следующие строки, если используете virtualenv
# source venv/bin/activate

# Проверяем, установлен ли Flower
if ! pip list | grep -q "flower"; then
    echo "Flower не установлен. Устанавливаем..."
    pip install flower
fi

# Запускаем Flower на порту 5555 (по умолчанию)
echo "Запуск Flower для мониторинга задач Celery..."
celery -A SoloPizza flower --port=5555