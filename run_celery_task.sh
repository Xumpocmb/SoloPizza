#!/bin/bash

# Запуск конкретной задачи
if [ -z "$1" ]; then
    echo "Укажите имя задачи. Например: ./run_celery_task.sh app_order.tasks.clear_orders"
    exit 1
fi

celery -A SoloPizza call $1