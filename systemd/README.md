# Настройка Celery как systemd-сервиса

Этот документ содержит инструкции по настройке Celery как systemd-сервиса для автоматического запуска при старте системы и перезапуска при сбоях.

## Подготовка файлов сервисов

1. Отредактируйте файлы `celery-worker.service` и `celery-beat.service`, заменив следующие параметры:
   - `/path/to/SoloPizza` - путь к директории проекта
   - `User` и `Group` - пользователь и группа, от имени которых будет запускаться сервис

## Установка сервисов

1. Скопируйте файлы сервисов в директорию systemd:

```bash
sudo cp celery-worker.service /etc/systemd/system/
sudo cp celery-beat.service /etc/systemd/system/
```

2. Перезагрузите конфигурацию systemd:

```bash
sudo systemctl daemon-reload
```

3. Включите сервисы для автозапуска при старте системы:

```bash
sudo systemctl enable celery-worker.service
sudo systemctl enable celery-beat.service
```

4. Запустите сервисы:

```bash
sudo systemctl start celery-worker.service
sudo systemctl start celery-beat.service
```

## Управление сервисами

### Проверка статуса

```bash
sudo systemctl status celery-worker.service
sudo systemctl status celery-beat.service
```

### Перезапуск сервисов

```bash
sudo systemctl restart celery-worker.service
sudo systemctl restart celery-beat.service
```

### Остановка сервисов

```bash
sudo systemctl stop celery-worker.service
sudo systemctl stop celery-beat.service
```

### Просмотр логов

```bash
sudo journalctl -u celery-worker.service
sudo journalctl -u celery-beat.service
```

Для просмотра логов в реальном времени:

```bash
sudo journalctl -u celery-worker.service -f
sudo journalctl -u celery-beat.service -f
```