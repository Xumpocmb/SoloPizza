#!/bin/bash

# Скрипт для проверки и запуска Celery на хостинге

# Переходим в директорию проекта
cd "$(dirname "$0")"

# Устанавливаем переменную окружения DJANGO_SETTINGS_MODULE
export DJANGO_SETTINGS_MODULE="SoloPizza.settings"

# Проверяем, установлена ли переменная окружения DJANGO_SETTINGS_MODULE
if [ -z "$DJANGO_SETTINGS_MODULE" ]; then
    echo "✗ Переменная окружения DJANGO_SETTINGS_MODULE не установлена!"
    echo "Устанавливаем DJANGO_SETTINGS_MODULE=SoloPizza.settings"
    export DJANGO_SETTINGS_MODULE="SoloPizza.settings"
else
    echo "✓ DJANGO_SETTINGS_MODULE установлена: $DJANGO_SETTINGS_MODULE"
fi

# Активируем виртуальное окружение
if [ -d "venv" ]; then
    echo "✓ Активация локального виртуального окружения..."
    source venv/bin/activate
elif [ -d "/home/solopizzaadmin/SoloPizza/venv" ]; then
    echo "✓ Активация виртуального окружения на сервере..."
    source /home/solopizzaadmin/SoloPizza/venv/bin/activate
else
    echo "✗ ВНИМАНИЕ: Виртуальное окружение не найдено!"
    echo "  Celery может работать некорректно без активации виртуального окружения."
fi

# Проверяем, запущены ли процессы Celery
celery_worker_running=$(pgrep -f "celery -A SoloPizza worker")
celery_beat_running=$(pgrep -f "celery -A SoloPizza beat")

# Выводим текущее состояние
echo "Проверка состояния Celery:"
echo "----------------------------"

if [ -n "$celery_worker_running" ]; then
    echo "✓ Celery worker запущен (PID: $celery_worker_running)"
else
    echo "✗ Celery worker не запущен"
fi

if [ -n "$celery_beat_running" ]; then
    echo "✓ Celery beat запущен (PID: $celery_beat_running)"
else
    echo "✗ Celery beat не запущен"
fi

echo "----------------------------"

# Проверяем доступность Redis
redis_status=$(redis-cli ping 2>/dev/null)
if [ "$redis_status" = "PONG" ]; then
    echo "✓ Redis доступен"
else
    echo "✗ Redis недоступен! Celery не сможет работать без Redis."
    echo "Проверьте настройки Redis в settings.py и убедитесь, что Redis запущен."
    exit 1
fi

# Проверяем настройки часового пояса
echo "Текущее время сервера: $(date)"
echo "Часовой пояс в Django: $(python -c "import django; django.setup(); from django.conf import settings; print(settings.TIME_ZONE)")"

# Спрашиваем, нужно ли запустить Celery
if [ -z "$celery_worker_running" ] || [ -z "$celery_beat_running" ]; then
    echo ""
    echo "Некоторые компоненты Celery не запущены. Что вы хотите сделать?"
    echo "1. Запустить Celery worker и beat"
    echo "2. Запустить только Celery worker"
    echo "3. Запустить только Celery beat"
    echo "4. Выйти без запуска"
    read -p "Выберите действие (1-4): " choice
    
    case $choice in
        1)
            echo "Запуск Celery worker и beat..."
            # Останавливаем существующие процессы, если они есть
            if [ -n "$celery_worker_running" ]; then
                kill $celery_worker_running
                echo "Остановлен существующий Celery worker"
            fi
            if [ -n "$celery_beat_running" ]; then
                kill $celery_beat_running
                echo "Остановлен существующий Celery beat"
            fi
            
            # Запускаем Celery worker в фоновом режиме
            celery -A SoloPizza worker --loglevel=info --detach
            echo "Celery worker запущен"
            
            # Запускаем Celery beat в фоновом режиме с использованием nohup
            nohup celery -A SoloPizza beat --loglevel=info > celery_beat.log 2>&1 &
            echo "Celery beat запущен (логи в celery_beat.log)"
            ;;
        2)
            echo "Запуск только Celery worker..."
            if [ -n "$celery_worker_running" ]; then
                kill $celery_worker_running
                echo "Остановлен существующий Celery worker"
            fi
            celery -A SoloPizza worker --loglevel=info --detach
            echo "Celery worker запущен"
            ;;
        3)
            echo "Запуск только Celery beat..."
            if [ -n "$celery_beat_running" ]; then
                kill $celery_beat_running
                echo "Остановлен существующий Celery beat"
            fi
            nohup celery -A SoloPizza beat --loglevel=info > celery_beat.log 2>&1 &
            echo "Celery beat запущен (логи в celery_beat.log)"
            ;;
        4)
            echo "Выход без запуска Celery"
            ;;
        *)
            echo "Неверный выбор"
            ;;
    esac
else
    echo ""
    echo "Все компоненты Celery уже запущены."
    echo "Если вы хотите перезапустить Celery, сначала остановите его с помощью ./stop_celery.sh"
fi

# Проверяем задачи в расписании
echo ""
echo "Проверка задач в расписании Celery Beat:"
echo "----------------------------"

# Проверяем, запущены ли уже компоненты Celery
if [ -n "$celery_worker_running" ] && [ -n "$celery_beat_running" ]; then
    echo "Celery уже запущен, пропускаем проверку задач для избежания ошибок импорта Django"
    echo "Для просмотра задач используйте Django admin или запустите скрипт, когда Celery не запущен"
else
    # Выполняем проверку задач только если Celery не запущен
    python -c "import django; django.setup(); from django_celery_beat.models import PeriodicTask; print('\n'.join([f'{task.name} - {task.enabled}' for task in PeriodicTask.objects.all()]))" 2>/dev/null || echo "Не удалось получить список задач. Возможно, проблема с импортом Django."

echo ""
echo "Для просмотра логов Celery beat используйте: tail -f celery_beat.log"
echo "Для остановки всех процессов Celery используйте: ./stop_celery.sh"