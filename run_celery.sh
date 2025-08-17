#!/bin/bash

# Запуск Celery worker и beat
celery -A SoloPizza worker -l info &
celery -A SoloPizza beat -l info &

echo "Celery worker и beat запущены"