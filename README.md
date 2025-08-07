# SoloPizza

Проект веб-приложения для пиццерии Solo Pizza.

## Запуск проекта

### Разработка

```bash
docker-compose up -d
```

### Продакшн

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Обслуживание

### Очистка Redis и перезапуск веб-сервера

Для очистки кэша Redis и перезапуска веб-сервера используйте скрипт:

```bash
./restart_services.sh
```

Этот скрипт выполняет следующие действия:
1. Очищает кэш Redis с помощью команды `docker exec -it solopizza-redis-1 redis-cli flushall`
2. Перезапускает веб-сервер с помощью команды `docker restart solopizza-web-1`

## Структура проекта

- `app_catalog` - каталог товаров
- `app_cart` - корзина покупок
- `app_home` - главная страница и общие функции
- `app_order` - оформление и управление заказами
- `app_reviews` - отзывы пользователей
- `app_user` - управление пользователями