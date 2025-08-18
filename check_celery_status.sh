#!/bin/bash

# Проверка статуса процессов Celery
echo "Проверка статуса процессов Celery..."

# Проверка worker
worker_count=$(pgrep -f "celery -A SoloPizza worker" | wc -l)
if [ $worker_count -gt 0 ]; then
    echo "Celery worker запущен. Найдено процессов: $worker_count"
    pgrep -f "celery -A SoloPizza worker" | while read pid; do
        echo "PID: $pid"
    done
else
    echo "Celery worker не запущен"
fi

# Проверка beat
beat_count=$(pgrep -f "celery -A SoloPizza beat" | wc -l)
if [ $beat_count -gt 0 ]; then
    echo "Celery beat запущен. Найдено процессов: $beat_count"
    pgrep -f "celery -A SoloPizza beat" | while read pid; do
        echo "PID: $pid"
    done
else
    echo "Celery beat не запущен"
fi