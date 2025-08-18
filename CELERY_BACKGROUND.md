# Запуск Celery в фоновом режиме

Этот документ содержит инструкции по запуску задач Celery в фоновом режиме на удаленном сервере, чтобы они продолжали работать после отключения SSH-сессии.

## Доступные скрипты

### Запуск в фоновом режиме

- `run_celery_background.sh` - запускает и worker, и beat в фоновом режиме
- `run_celery_worker_background.sh` - запускает только worker в фоновом режиме
- `run_celery_beat_background.sh` - запускает только beat в фоновом режиме

### Управление процессами

- `check_celery_status.sh` - проверяет статус запущенных процессов Celery
- `stop_celery_background.sh` - останавливает все процессы Celery

## Использование

### Запуск всех процессов в фоновом режиме

```bash
./run_celery_background.sh
```

Эта команда запустит и worker, и beat в фоновом режиме. Логи будут сохраняться в файлы `celery_worker.log` и `celery_beat.log`.

### Запуск только worker в фоновом режиме

```bash
./run_celery_worker_background.sh
```

### Запуск только beat в фоновом режиме

```bash
./run_celery_beat_background.sh
```

### Проверка статуса процессов

```bash
./check_celery_status.sh
```

### Остановка всех процессов

```bash
./stop_celery_background.sh
```

## Логи

Логи сохраняются в следующие файлы:

- `celery_worker.log` - логи worker
- `celery_beat.log` - логи beat

Для просмотра логов в реальном времени можно использовать команду:

```bash
tail -f celery_worker.log
```

или

```bash
tail -f celery_beat.log
```

## Альтернативные способы запуска в фоновом режиме

### Использование screen

Вместо nohup можно использовать screen:

```bash
screen -S celery_worker
celery -A SoloPizza worker -l info
# Нажмите Ctrl+A, затем D для отключения от сессии
```

Для повторного подключения к сессии:

```bash
screen -r celery_worker
```

### Использование tmux

Аналогично можно использовать tmux:

```bash
tmux new -s celery_worker
celery -A SoloPizza worker -l info
# Нажмите Ctrl+B, затем D для отключения от сессии
```

Для повторного подключения к сессии:

```bash
tmux attach -t celery_worker
```

### Использование systemd (для продакшн)

Для продакшн-окружения рекомендуется настроить systemd-сервисы для автоматического запуска Celery при старте системы и перезапуска при сбоях.