#!/bin/bash

# Запуск только Celery worker в фоновом режиме
echo "Запуск Celery worker в фоновом режиме..."
nohup celery -A SoloPizza worker -l info > celery_worker.log 2>&1 &
worker_pid=$!
echo "Celery worker запущен с PID: $worker_pid"
echo "Логи сохраняются в файл celery_worker.log"