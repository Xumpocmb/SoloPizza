#!/bin/bash

# Скрипт для запуска Celery Beat (планировщик задач)

# Переходим в директорию проекта
cd "$(dirname "$0")"

# Устанавливаем переменную окружения DJANGO_SETTINGS_MODULE
export DJANGO_SETTINGS_MODULE="SoloPizza.settings"

# Активируем виртуальное окружение
if [ -d "venv" ]; then
    echo "Активация виртуального окружения..."
    source venv/bin/activate
elif [ -d "/home/solopizzaadmin/SoloPizza/venv" ]; then
    echo "Активация виртуального окружения на сервере..."
    source /home/solopizzaadmin/SoloPizza/venv/bin/activate
else
    echo "ВНИМАНИЕ: Виртуальное окружение не найдено!"
    echo "Celery может работать некорректно без активации виртуального окружения."
fi

# Запускаем Celery Beat
celery -A SoloPizza beat --loglevel=info