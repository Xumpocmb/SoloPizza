# SoloPizza API Documentation

## Обзор

API SoloPizza предоставляет доступ к функциональности сайта через RESTful интерфейс. API позволяет мобильным приложениям взаимодействовать с сайтом, получать информацию о товарах, управлять корзиной и заказами, а также работать с профилем пользователя.

## Аутентификация

API использует JWT (JSON Web Tokens) для аутентификации. Для доступа к защищенным эндпоинтам необходимо получить токен доступа.

### Получение токена

```
POST /api/auth/token/
```

Параметры запроса:
- `username`: имя пользователя
- `password`: пароль пользователя

Ответ:
```json
{
  "access": "access_token",
  "refresh": "refresh_token"
}
```

### Обновление токена

```
POST /api/auth/token/refresh/
```

Параметры запроса:
- `refresh`: refresh токен

Ответ:
```json
{
  "access": "new_access_token"
}
```

### Проверка токена

```
POST /api/auth/token/verify/
```

Параметры запроса:
- `token`: access токен

## Пользователи

### Регистрация пользователя

```
POST /api/auth/register/
```

Параметры запроса:
- `username`: имя пользователя
- `password`: пароль
- `password2`: подтверждение пароля
- `email`: email пользователя
- `first_name`: имя
- `last_name`: фамилия

### Профиль пользователя

```
GET /api/auth/profile/
```

Ответ:
```json
{
  "id": 1,
  "username": "user",
  "email": "user@example.com",
  "first_name": "Имя",
  "last_name": "Фамилия",
  "phone": "+375291234567"
}
```

```
PUT /api/auth/profile/
```

Параметры запроса:
- `email`: email пользователя
- `first_name`: имя
- `last_name`: фамилия
- `phone`: телефон
- `address`: адрес пользователя

## Каталог

### Соусы для пиццы

```
GET /api/catalog/sauces/
```

Ответ:
```json
[
  {
    "id": 1,
    "name": "Томатный",
    "slug": "tomatnyj",
    "is_active": true
  },
  {
    "id": 2,
    "name": "Сливочный",
    "slug": "slivochnyj",
    "is_active": true
  }
]
```

### Борты для пиццы

```
GET /api/catalog/boards/
```

Ответ:
```json
[
  {
    "id": 1,
    "name": "Сырный",
    "slug": "syrnyj",
    "is_active": true
  },
  {
    "id": 2,
    "name": "Стандартный",
    "slug": "standartnyj",
    "is_active": true
  }
]
```

### Добавки для пиццы

```
GET /api/catalog/addons/
```

Ответ:
```json
[
  {
    "id": 1,
    "name": "Грибы",
    "slug": "griby",
    "is_active": true
  },
  {
    "id": 2,
    "name": "Бекон",
    "slug": "bekon",
    "is_active": true
  }
]
```

### Борты для размера пиццы

```
GET /api/catalog/size-boards/{size_id}/
```

Параметры запроса:
- `size_id`: ID размера пиццы

Ответ:
```json
[
  {
    "id": 1,
    "board": {
      "id": 1,
      "name": "Сырный"
    },
    "size": {
      "id": 1,
      "name": "32"
    },
    "price": "2.00"
  },
  {
    "id": 2,
    "board": {
      "id": 2,
      "name": "Стандартный"
    },
    "size": {
      "id": 1,
      "name": "32"
    },
    "price": "0.00"
  }
]
```

### Добавки для размера пиццы

```
GET /api/catalog/size-addons/{size_id}/
```

Параметры запроса:
- `size_id`: ID размера пиццы

Ответ:
```json
[
  {
    "id": 1,
    "addon": {
      "id": 1,
      "name": "Грибы"
    },
    "size": {
      "id": 1,
      "name": "32"
    },
    "price": "1.50"
  },
  {
    "id": 2,
    "addon": {
      "id": 2,
      "name": "Бекон"
    },
    "size": {
      "id": 1,
      "name": "32"
    },
    "price": "2.00"
  }
]
```

### Размеры пиццы

```
GET /api/catalog/sizes/
```

Ответ:
```json
[
  {
    "id": 1,
    "name": "32"
  },
  {
    "id": 2,
    "name": "42"
  }
]
```

### Категории

```
GET /api/catalog/categories/
```

Ответ:
```json
[
  {
    "id": 1,
    "name": "Пицца",
    "slug": "pizza",
    "description": "Вкусная пицца",
    "image": "http://example.com/media/categories/pizza.jpg",
    "parent": null,
    "is_active": true
  }
]
```

### Продукты

```
GET /api/catalog/products/
```

Параметры запроса:
- `category`: ID категории (фильтр)
- `is_new`: новинки (фильтр)
- `is_hit`: хиты (фильтр)
- `search`: поиск по названию или описанию
- `ordering`: сортировка (name, -name, created_at, -created_at, price, -price)

Ответ:
```json
{
  "count": 10,
  "next": "http://example.com/api/catalog/products/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Маргарита",
      "slug": "margarita",
      "description": "Классическая пицца",
      "image": "http://example.com/media/products/margarita.jpg",
      "category": {
        "id": 1,
        "name": "Пицца",
        "slug": "pizza"
      },
      "is_active": true,
      "is_new": false,
      "is_hit": true,
      "created_at": "2023-01-01T12:00:00Z",
      "updated_at": "2023-01-01T12:00:00Z",
      "variants": [
        {
          "id": 1,
          "product": 1,
          "size": {
            "id": 1,
            "name": "Маленькая",
            "diameter": 25
          },
          "value": null,
          "unit": "см",
          "price": "10.00",
          "old_price": null,
          "weight": 450
        }
      ]
    }
  ]
}
```

## Корзина

### Список товаров в корзине

```
GET /api/cart/items/
```

Ответ:
```json
[
  {
    "id": 1,
    "product": 1,
    "variant": 1,
    "variant_details": {
      "id": 1,
      "product": 1,
      "size": {
        "id": 1,
        "name": "Маленькая",
        "diameter": 25
      },
      "value": null,
      "unit": "см",
      "price": "10.00",
      "old_price": null,
      "weight": 450
    },
    "quantity": 1,
    "boards": [1],
    "addons": [2, 3],
    "sauce": 1,
    "drink": null,
    "total_price": "15.00"
  }
]
```

### Добавление товара в корзину

```
POST /api/cart/items/
```

Параметры запроса:
- `product`: ID продукта
- `variant`: ID варианта
- `quantity`: количество
- `boards`: список ID бортов (опционально)
- `addons`: список ID добавок (опционально)
- `sauce`: ID соуса (опционально)
- `drink`: ID напитка (опционально)

### Сводная информация о корзине

```
GET /api/cart/summary/
```

Ответ:
```json
{
  "items_count": 2,
  "total_price": "25.00",
  "items": [...]
}
```

## Заказы

### Список заказов

```
GET /api/order/
```

Ответ:
```json
[
  {
    "id": 1,
    "order_number": "ORD-2023-001",
    "status": "new",
    "status_display": "Новый",
    "payment": "cash",
    "payment_display": "Наличными",
    "delivery_type": "delivery",
    "delivery_type_display": "Доставка",
    "delivery_cost": "5.00",
    "total_price": "30.00",
    "customer_name": "Иван Иванов",
    "customer_phone": "+375291234567",
    "delivery_address": "ул. Примерная, 123, кв. 42",
    "delivery_time": "2023-01-01T15:00:00Z",
    "delivery_by": "Как можно скорее",
    "comment": "Позвонить перед доставкой",
    "created_at": "2023-01-01T12:00:00Z",
    "updated_at": "2023-01-01T12:00:00Z",
    "items": [...]
  }
]
```

### Создание заказа

```
POST /api/order/create/
```

Параметры запроса:
- `payment`: способ оплаты (cash, card, online)
- `delivery_type`: тип доставки (delivery, pickup)
- `customer_name`: имя клиента
- `customer_phone`: телефон клиента
- `delivery_address`: адрес доставки (для delivery)
- `delivery_time`: время доставки (опционально)
- `delivery_by`: пожелания по доставке (опционально)
- `comment`: комментарий к заказу (опционально)
- `branch`: ID филиала (для pickup)

### Статус заказа

```
GET /api/order/{id}/status/
```

Ответ:
```json
{
  "id": 1,
  "order_number": "ORD-2023-001",
  "status": "processing",
  "status_display": "В обработке",
  "created_at": "2023-01-01T12:00:00Z",
  "updated_at": "2023-01-01T12:05:00Z"
}
```

## Коды ошибок

- 400: Неверный запрос
- 401: Не авторизован
- 403: Доступ запрещен
- 404: Не найдено
- 500: Внутренняя ошибка сервера

## Ограничения

API имеет ограничение на количество запросов: 100 запросов в минуту для авторизованных пользователей и 20 запросов в минуту для неавторизованных пользователей.