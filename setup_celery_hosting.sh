#!/bin/bash

# Скрипт для настройки Celery на хостинге

# Переходим в директорию проекта
cd "$(dirname "$0")"

echo "Настройка Celery на хостинге"
echo "============================"

# Проверяем наличие supervisor
if ! command -v supervisorctl &> /dev/null; then
    echo "Supervisor не установлен. Рекомендуется установить supervisor для управления процессами Celery."
    echo "Установка: sudo apt-get install supervisor"
    echo ""
    echo "Продолжаем без supervisor..."
else
    echo "✓ Supervisor установлен"
fi

# Создаем конфигурационные файлы для supervisor
echo "Создание конфигурационных файлов для supervisor..."

# Путь к проекту
PROJECT_PATH=$(pwd)

# Определяем путь к виртуальному окружению
if [ -d "venv" ]; then
    VENV_PATH="$PROJECT_PATH/venv"
else
    VENV_PATH="$PROJECT_PATH/.venv"
    if [ ! -d "$VENV_PATH" ]; then
        read -p "Введите путь к виртуальному окружению: " VENV_PATH
    fi
fi

# Создаем конфигурацию для Celery worker
cat > celery_worker.conf << EOF
[program:solopizza_celery_worker]
command=$VENV_PATH/bin/celery -A SoloPizza worker --loglevel=info
directory=$PROJECT_PATH
user=$(whoami)
numprocs=1
stdout_logfile=$PROJECT_PATH/logs/celery_worker.log
stderr_logfile=$PROJECT_PATH/logs/celery_worker_error.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=600
priority=998
EOF

# Создаем конфигурацию для Celery beat
cat > celery_beat.conf << EOF
[program:solopizza_celery_beat]
command=$VENV_PATH/bin/celery -A SoloPizza beat --loglevel=info
directory=$PROJECT_PATH
user=$(whoami)
numprocs=1
stdout_logfile=$PROJECT_PATH/logs/celery_beat.log
stderr_logfile=$PROJECT_PATH/logs/celery_beat_error.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=10
priority=999
EOF

# Создаем директорию для логов
mkdir -p logs

echo "Конфигурационные файлы созданы:"
echo "- celery_worker.conf"
echo "- celery_beat.conf"

echo ""
echo "Инструкции по установке на хостинге:"
echo "============================"
echo "1. Скопируйте конфигурационные файлы в директорию supervisor:"
echo "   sudo cp celery_worker.conf /etc/supervisor/conf.d/solopizza_celery_worker.conf"
echo "   sudo cp celery_beat.conf /etc/supervisor/conf.d/solopizza_celery_beat.conf"
echo ""
echo "2. Перезагрузите конфигурацию supervisor:"
echo "   sudo supervisorctl reread"
echo "   sudo supervisorctl update"
echo ""
echo "3. Запустите процессы Celery:"
echo "   sudo supervisorctl start solopizza_celery_worker"
echo "   sudo supervisorctl start solopizza_celery_beat"
echo ""
echo "4. Проверьте статус процессов:"
echo "   sudo supervisorctl status"
echo ""
echo "5. Для просмотра логов:"
echo "   tail -f logs/celery_worker.log"
echo "   tail -f logs/celery_beat.log"
echo ""
echo "Примечание: Если вы не используете supervisor, вы можете запустить Celery вручную:"
echo "   ./check_and_run_celery.sh"