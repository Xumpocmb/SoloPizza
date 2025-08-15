#!/bin/bash

# Скрипт для остановки запущенных процессов Celery

echo "Остановка процессов Celery..."

# Находим и останавливаем процессы Celery worker
celery_pids=$(pgrep -f "celery -A SoloPizza worker")
if [ -n "$celery_pids" ]; then
    echo "Останавливаем Celery worker (PID: $celery_pids)..."
    kill $celery_pids
    echo "Celery worker остановлен"
else
    echo "Celery worker не запущен"
fi

# Находим и останавливаем процессы Celery beat
beat_pids=$(pgrep -f "celery -A SoloPizza beat")
if [ -n "$beat_pids" ]; then
    echo "Останавливаем Celery beat (PID: $beat_pids)..."
    kill $beat_pids
    echo "Celery beat остановлен"
else
    echo "Celery beat не запущен"
fi

echo "Все процессы Celery остановлены"