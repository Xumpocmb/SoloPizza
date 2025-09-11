# SoloPizza API Documentation

## Обзор

SoloPizza API предоставляет RESTful интерфейс для мобильного приложения доставки пиццы. API использует JWT аутентификацию и возвращает данные в формате JSON.

**Базовый URL:** `https://api.solo-pizza.by/api/`

**Версия API:** v1

**Документация Swagger:** `/api/swagger/`

**Документация ReDoc:** `/api/redoc/`

## Аутентификация

API использует JWT (JSON Web Token) для аутентификации. Для получения токена необходимо отправить POST запрос на эндпоинт `/auth/token/` с учетными данными пользователя.

### Получение токена

**Endpoint:** `POST /auth/token/`

**Тело запроса:**
```json
{
    "username": "your_username",
    "password": "your_password"
}
```

**Ответ:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Обновление токена

**Endpoint:** `POST /auth/token/refresh/`

**Тело запроса:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Ответ:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Проверка токена

**Endpoint:** `POST /auth/token/verify/`

**Тело запроса:**
```json
{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Ответ:** `200 OK` если токен валиден, `401 Unauthorized` если нет.

## Пользователи

### Регистрация пользователя

**Endpoint:** `POST /auth/register/`

**Тело запроса:**
```json
{
    "phone": "+375291234567",
    "password": "your_password",
    "password2": "your_password"
}
```

**Ответ:**
```json
{
    "id": 1,
    "username": "user_a1b2c3d4",
    "email": "user_a1b2c3d4@example.com",
    "first_name": "Пользователь",
    "last_name": "12345",
    "phone": "+375291234567",
    "address": null
}
```

### Авторизация пользователя

**Endpoint:** `POST /auth/login/`

**Тело запроса:**
```json
{
    "phone": "+375291234567",
    "password": "your_password"
}
```

**Ответ:**
```json
{
    "user": {
        "id": 1,
        "username": "user_a1b2c3d4",
        "phone": "+375291234567"
    },
    "message": "Авторизация прошла успешно"
}
```

### Получение профиля пользователя

**Endpoint:** `GET /auth/profile/`

**Заголовки:**
- `Authorization: Bearer <access_token>`

**Ответ:**
```json
{
    "id": 1,
    "username": "user_a1b2c3d4",
    "email": "user_a1b2c3d4@example.com",
    "first_name": "Пользователь",
    "last_name": "12345",
    "phone": "+375291234567",
    "address": "г. Минск, ул. Примерная, 1"
}
```

### Обновление профиля пользователя

**Endpoint:** `PUT /auth/profile/`

**Заголовки:**
- `Authorization: Bearer <access_token>`

**Тело запроса:**
```json
{
    "email": "newemail@example.com",
    "first_name": "Новое Имя",
    "last_name": "Новая Фамилия",
    "phone": "+375291234567",
    "address": "г. Минск, ул. Новая, 2"
}
```

**Ответ:**
```json
{
    "id": 1,
    "username": "user_a1b2c3d4",
    "email": "newemail@example.com",
    "first_name": "Новое Имя",
    "last_name": "Новая Фамилия",
    "phone": "+375291234567",
    "address": "г. Минск, ул. Новая, 2"
}
```

## Каталог

### Категории

#### Получение списка категорий

**Endpoint:** `GET /catalog/categories/`

**Параметры запроса:**
- `search`: поиск по названию категории

**Ответ:**
```json
[
    {
        "id": 1,
        "name": "Пицца",
        "slug": "pizza",
        "image": "https://api.solo-pizza.by/media/categories/pizza.jpg",
        "is_active": true
    },
    {
        "id": 2,
        "name": "Напитки",
        "slug": "drinks",
        "image": "https://api.solo-pizza.by/media/categories/drinks.jpg",
        "is_active": true
    }
]
```

#### Получение детальной информации о категории

**Endpoint:** `GET /catalog/categories/{id}/`

**Ответ:**
```json
{
    "id": 1,
    "name": "Пицца",
    "slug": "pizza",
    "image": "https://api.solo-pizza.by/media/categories/pizza.jpg",
    "is_active": true
}
```

### Продукты

#### Получение списка продуктов

**Endpoint:** `GET /catalog/products/`

**Параметры запроса:**
- `category`: фильтр по ID категории
- `search`: поиск по названию и описанию
- `ordering`: сортировка (name, created_at, price)

**Ответ:**
```json
[
    {
        "id": 1,
        "name": "Маргарита",
        "slug": "margarita",
        "description": "Классическая пицца с томатным соусом и моцареллой",
        "image": "https://api.solo-pizza.by/media/products/margarita.jpg",
        "category": {
            "id": 1,
            "name": "Пицца",
            "slug": "pizza",
            "image": "https://api.solo-pizza.by/media/categories/pizza.jpg",
            "is_active": true
        },
        "is_active": true,
        "created_at": "2024-01-15T10:30:00Z",
        "variants": [
            {
                "id": 1,
                "product": 1,
                "size": {
                    "id": 1,
                    "name": "Маленькая"
                },
                "value": 25,
                "unit": "см",
                "price": "15.90"
            }
        ]
    }
]
```

#### Получение детальной информации о продукте

**Endpoint:** `GET /catalog/products/{id}/`

### Варианты продуктов

#### Получение списка вариантов

**Endpoint:** `GET /catalog/variants/`

#### Получение вариантов для конкретного продукта

**Endpoint:** `GET /catalog/product-variants/{product_id}/`

### Соусы

#### Получение списка соусов

**Endpoint:** `GET /catalog/sauces/`

**Ответ:**
```json
[
    {
        "id": 1,
        "name": "Томатный",
        "slug": "tomato",
        "is_active": true
    },
    {
        "id": 2,
        "name": "Белый",
        "slug": "white",
        "is_active": true
    }
]
```

### Борты

#### Получение списка бортов

**Endpoint:** `GET /catalog/boards/`

**Ответ:**
```json
[
    {
        "id": 1,
        "name": "Обычный",
        "slug": "regular",
        "is_active": true
    },
    {
        "id": 2,
        "name": "Сырный",
        "slug": "cheese",
        "is_active": true
    }
]
```

#### Получение бортов для размера

**Endpoint:** `GET /catalog/size-boards/{size_id}/`

**Ответ:**
```json
[
    {
        "id": 1,
        "board": {
            "id": 1,
            "name": "Обычный",
            "slug": "regular",
            "is_active": true
        },
        "size": {
            "id": 1,
            "name": "Маленькая"
        },
        "price": "0.00"
    }
]
```

### Добавки

#### Получение списка добавок

**Endpoint:** `GET /catalog/addons/`

**Ответ:**
```json
[
    {
        "id": 1,
        "name": "Моцарелла",
        "slug": "mozzarella",
        "is_active": true
    },
    {
        "id": 2,
        "name": "Пепперони",
        "slug": "pepperoni",
        "is_active": true
    }
]
```

#### Получение добавок для размера

**Endpoint:** `GET /catalog/size-addons/{size_id}/`

**Ответ:**
```json
[
    {
        "id": 1,
        "addon": {
            "id": 1,
            "name": "Моцарелла",
            "slug": "mozzarella",
            "is_active": true
        },
        "size": {
            "id": 1,
            "name": "Маленькая"
        },
        "price": "2.50"
    }
]
```

### Размеры

#### Получение списка размеров

**Endpoint:** `GET /catalog/sizes/`

**Ответ:**
```json
[
    {
        "id": 1,
        "name": "Маленькая"
    },
    {
        "id": 2,
        "name": "Средняя"
    },
    {
        "id": 3,
        "name": "Большая"
    }
]
```

## Корзина

### Получение товаров в корзине

**Endpoint:** `GET /cart/items/`

**Заголовки:**
- `Authorization: Bearer <access_token>`

**Ответ:**
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
                "name": "Маленькая"
            },
            "value": 25,
            "unit": "см",
            "price": "15.90"
        },
        "quantity": 2,
        "boards": [1],
        "addons": [1, 2],
        "sauce": 1,
        "drink": null,
        "total_price": "35.80"
    }
]
```

### Добавление товара в корзину

**Endpoint:** `POST /cart/items/`

**Заголовки:**
- `Authorization: Bearer <access_token>`

**Тело запроса:**
```json
{
    "product": 1,
    "variant": 1,
    "quantity": 2,
    "boards": [1],
    "addons": [1, 2],
    "sauce": 1,
    "drink": null
}
```

**Ответ:**
```json
{
    "id": 1,
    "product": 1,
    "variant": 1,
    "variant_details": {
        "id": 1,
        "product": 1,
        "size": {
            "id": 1,
            "name": "Маленькая"
        },
        "value": 25,
        "unit": "см",
        "price": "15.90"
    },
    "quantity": 2,
    "boards": [1],
    "addons": [1, 2],
    "sauce": 1,
    "drink": null,
    "total_price": "35.80"
}
```

### Обновление товара в корзине

**Endpoint:** `PUT /cart/items/{id}/`

**Заголовки:**
- `Authorization: Bearer <access_token>`

**Тело запроса:** те же поля, что и при добавлении

### Удаление товара из корзины

**Endpoint:** `DELETE /cart/items/{id}/`

**Заголовки:**
- `Authorization: Bearer <access_token>`

**Ответ:** `204 No Content`

### Сводная информация о корзине

**Endpoint:** `GET /cart/summary/`

**Заголовки:**
- `Authorization: Bearer <access_token>`

**Ответ:**
```json
{
    "items_count": 3,
    "total_price": "45.50",
    "items": [
        {
            "id": 1,
            "product": 1,
            "variant": 1,
            "variant_details": {
                "id": 1,
                "product": 1,
                "size": {
                    "id": 1,
                    "name": "Маленькая"
                },
                "value": 25,
                "unit": "см",
                "price": "15.90"
            },
            "quantity": 2,
            "boards": [1],
            "addons": [1, 2],
            "sauce": 1,
            "drink": null,
            "total_price": "35.80"
        }
    ]
}
```

## Заказы

### Список заказов пользователя

**Endpoint:** `GET /order/`

**Заголовки:**
- `Authorization: Bearer <access_token>`

**Ответ:**
```json
[
    {
        "id": 1,
        "order_number": "ORD-001",
        "status": "pending",
        "status_display": "В обработке",
        "payment": "cash",
        "payment_display": "Наличными",
        "delivery_type": "delivery",
        "delivery_type_display": "Доставка",
        "delivery_cost": "3.00",
        "total_price": "28.00",
        "customer_name": "Иван Иванов",
        "customer_phone": "+375291234567",
        "address": "г. Минск, ул. Примерная, 1",
        "delivery_time": "2023-12-01T18:30:00Z",
        "delivery_by": null,
        "comment": "Без лука",
        "created_at": "2023-12-01T17:00:00Z",
        "updated_at": "2023-12-01T17:00:00Z",
        "items": [
            {
                "id": 1,
                "product_name": "Маргарита",
                "variant_name": "Маленькая",
                "variant": 1,
                "variant_details": {
                    "id": 1,
                    "product": 1,
                    "size": {
                        "id": 1,
                        "name": "Маленькая"
                    },
                    "value": 25,
                    "unit": "см",
                    "price": "15.90"
                },
                "quantity": 2,
                "price": "15.90",
                "total_price": "31.80",
                "boards": [1],
                "addons": [2],
                "sauce": 1,
                "drink": null
            }
        ]
    }
]
```

### Получение детальной информации о заказе

**Endpoint:** `GET /order/{id}/`

**Заголовки:**
- `Authorization: Bearer <access_token>`

**Ответ:** аналогичен элементу из списка заказов

### Создание заказа

**Endpoint:** `POST /order/create/`

**Заголовки:**
- `Authorization: Bearer <access_token>`

**Тело запроса:**
```json
{
    "branch": 1,
    "customer_name": "Иван Иванов",
    "customer_phone": "+375291234567",
    "delivery_type": "delivery",
    "address": "г. Минск, ул. Примерная, 1",
    "payment": "cash",
    "comment": "Без лука"
}
```

**Параметры:**
- `branch`: ID филиала
- `customer_name`: имя клиента
- `customer_phone`: телефон клиента
- `delivery_type`: тип доставки (delivery/pickup)
- `address`: адрес доставки (для delivery)
- `payment`: способ оплаты (cash/card/online)
- `comment`: комментарий к заказу (опционально)

**Ответ:**
```json
{
    "id": 1,
    "order_number": "ORD-001",
    "status": "pending",
    "total_price": "28.00",
    "message": "Заказ успешно создан"
}
```

### Получение статуса заказа

**Endpoint:** `GET /order/{id}/status/`

**Заголовки:**
- `Authorization: Bearer <access_token>`

**Ответ:**
```json
{
    "id": 1,
    "order_number": "ORD-001",
    "status": "in_progress",
    "status_display": "Готовится",
    "created_at": "2023-12-01T17:00:00Z",
    "updated_at": "2023-12-01T17:15:00Z"
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