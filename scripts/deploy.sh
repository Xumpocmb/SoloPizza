#!/usr/bin/env bash
# Деплой SoloPizza на прод. Запускается по SSH из GitHub Actions (.github/workflows/ci-cd.yml).
# Требует на сервере: passwordless sudo для systemctl restart (см. /etc/sudoers.d/solopizzaadmin-deploy).
set -euo pipefail

APP_DIR="/home/solopizzaadmin/SoloPizza"
VENV="$APP_DIR/venv"

cd "$APP_DIR"

echo "==> Обновление кода"
git pull origin main

echo "==> Зависимости"
"$VENV/bin/pip" install -r requirements.txt

echo "==> Миграции"
"$VENV/bin/python" manage.py makemigrations
"$VENV/bin/python" manage.py migrate --noinput

echo "==> Статика"
"$VENV/bin/python" manage.py collectstatic --noinput

echo "==> Перезапуск сервисов"
sudo /usr/bin/systemctl restart gunicorn
sudo /usr/bin/systemctl restart celery-worker
sudo /usr/bin/systemctl restart celery-beat

echo "==> Деплой завершён: $(git rev-parse --short HEAD)"
