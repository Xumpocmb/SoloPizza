#!/bin/bash

# Запуск только Celery beat в фоновом режиме
echo "Запуск Celery beat в фоновом режиме..."
nohup celery -A SoloPizza beat -l info > celery_beat.log 2>&1 &
beat_pid=$!
echo "Celery beat запущен с PID: $beat_pid"
echo "Логи сохраняются в файл celery_beat.log"