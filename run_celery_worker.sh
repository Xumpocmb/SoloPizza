#!/bin/bash

# Запуск только Celery worker
celery -A SoloPizza worker -l info