#!/bin/bash

# Запуск только Celery beat
celery -A SoloPizza beat -l info