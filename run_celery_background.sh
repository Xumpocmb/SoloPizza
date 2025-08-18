#!/bin/bash

# Запуск Celery worker и beat в фоновом режиме
echo "Запуск Celery worker в фоновом режиме..."
nohup celery -A SoloPizza worker -l info > celery_worker.log 2>&1 &
worker_pid=$!
echo "Celery worker запущен с PID: $worker_pid"

echo "Запуск Celery beat в фоновом режиме..."
nohup celery -A SoloPizza beat -l info > celery_beat.log 2>&1 &
beat_pid=$!
echo "Celery beat запущен с PID: $beat_pid"

echo "Все процессы Celery запущены в фоновом режиме"
echo "Логи сохраняются в файлы celery_worker.log и celery_beat.log"