#!/bin/bash

# Остановка всех процессов Celery
pkill -f 'celery worker'
pkill -f 'celery beat'

echo "Все процессы Celery остановлены"