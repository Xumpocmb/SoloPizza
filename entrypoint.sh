#!/bin/sh

set -e

echo "Waiting for PostgreSQL to start..."
while ! nc -z db 5432; do
  sleep 1
done
echo "PostgreSQL started"

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Starting server..."
exec "$@"