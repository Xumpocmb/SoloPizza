#!/bin/bash

# Очистка Redis
docker exec -it solopizza-redis-1 redis-cli flushall
echo "Redis cache cleared"

# Перезапуск веб-сервера
docker restart solopizza-web-1
echo "Web server restarted"