#!/bin/sh

set -e

echo "Waiting for Redis to start..."
while ! nc -z redis 6379; do
  sleep 1
done
echo "Redis started"

echo "Applying migrations..."
python manage.py migrate --noinput
python manage.py migrate django_celery_beat --noinput
python manage.py migrate django_celery_results --noinput

echo "Starting server..."
exec "$@"