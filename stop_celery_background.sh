#!/bin/bash

# Остановка фоновых процессов Celery
echo "Остановка процессов Celery..."

# Остановка worker
worker_pids=$(pgrep -f "celery -A SoloPizza worker")
if [ -n "$worker_pids" ]; then
    echo "Останавливаем Celery worker процессы: $worker_pids"
    kill $worker_pids
    echo "Celery worker процессы остановлены"
else
    echo "Celery worker процессы не найдены"
fi

# Остановка beat
beat_pids=$(pgrep -f "celery -A SoloPizza beat")
if [ -n "$beat_pids" ]; then
    echo "Останавливаем Celery beat процессы: $beat_pids"
    kill $beat_pids
    echo "Celery beat процессы остановлены"
else
    echo "Celery beat процессы не найдены"
fi

echo "Все процессы Celery остановлены"