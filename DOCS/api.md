# API

**URL (dev):** `http://127.0.0.1:5000`  
**Формат:** JSON, `Content-Type: application/json`  
**Auth:** сессия на cookie (`sessionid`). Логин — `POST /api/v1/login`  
**CSRF:** не нужен для API-ручек (используется `csrf_exempt`)

## Коды

| Код | Значение |
|---|---|
| 200 | Успех |
| 201 | Создано |
| 400 | Ошибка в данных / некорректный JSON |
| 401 | Не авторизован |
| 403 | Нет прав |
| 404 | Не найдено |
| 405 | Метод не разрешён |
| 409 | Конфликт: объект уже существует |
| 500 | Ошибка сервера |

---

## Сводная таблица ручек

| Метод | Путь | Auth | Назначение |
|---|---|---|---|
| POST | `/api/v1/login` | — | Вход / регистрация |
| GET | `/api/v1/me` | user | Профиль + квартиры |
| GET | `/api/v1/user/apartments` | user | Список квартир |
| POST | `/api/v1/user/apartments` | user | Добавить квартиру |
| GET | `/api/v1/user/appeals` | user | Список своих обращений |
| POST | `/api/v1/user/appeals` | user | Создать обращение |
| GET | `/api/v1/user/appeals/<id>` | user | Детали обращения + история |
| GET | `/api/v1/uk/domiks` | uk | Дома сотрудника УК |
| POST | `/api/v1/uk/domiks` | uk | Создать дом + квартиры |
| GET | `/api/v1/uk/domiks/<id>` | uk | Детали дома + квартиры |
| GET | `/api/v1/uk/appeals` | uk | Все обращения по домам УК |
| POST | `/api/v1/uk/appeals/<id>/status` | uk | Обновить статус обращения |

---

## Аутентификация

Кроме `POST /api/v1/login` — все ручки требуют активной сессии.  
Ручки `/api/v1/uk/*` дополнительно требуют `is_jk = true`, иначе:

**401:**
```json
{ "status": "Не авторизован" }
```

**403:**
```json
{ "status": "Только для сотрудников УК" }
```

---

## POST /api/v1/login

Вход или создание пользователя.  
Если пользователь с таким `max_id` уже есть — логинит его.  
Если нет — создаёт нового и логинит.

**Фронт кидает:**
```json
{ "max_id": "ivan", "name": "Иван" }
```

**200** ставит cookie `sessionid`.

Если пользователь новый:
```json
{ "status": "ok", "id": "b3a1f4e2-5c8d-4a1b-9e2f-7d6c1a3b8e9f" }
```

Если пользователь уже существует:
```json
{ "status": "Такой пользователь уже существует", "id": "b3a1f4e2-5c8d-4a1b-9e2f-7d6c1a3b8e9f" }
```

**400:**
```json
{ "status": "Некорректный JSON" }
{ "status": "Нужны поля max_id и name" }
```

---

## GET /api/v1/me

Профиль текущего пользователя + все его квартиры.

**Auth:** да.

**200:**
```json
{
  "id": "b3a1f4e2-5c8d-4a1b-9e2f-7d6c1a3b8e9f",
  "max_id": "ivan",
  "name": "Иван",
  "last_name": "Иванов",
  "is_jk": false,
  "apartments": [
    {
      "id": "a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
      "number": "42",
      "entrance": "1",
      "domik_id": "b3a1f4e2-5c8d-4a1b-9e2f-7d6c1a3b8e9f",
      "domik_address": "г Понск, улица Поновая, д 52",
      "management_org": "УК",
      "role": "resident",
      "role_display": "Житель",
      "is_primary": true
    }
  ]
}
```

**401:**
```json
{ "status": "Не авторизован" }
```

---

## GET /api/v1/user/apartments

Список квартир текущего пользователя.

**Auth:** да.

**200:**
```json
{
  "apartments": [
    {
      "id": "a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
      "number": "42",
      "entrance": "1",
      "domik_id": "b3a1f4e2-5c8d-4a1b-9e2f-7d6c1a3b8e9f",
      "domik_address": "г Понск, улица Поновая, д 52",
      "management_org": "УК",
      "role": "resident",
      "role_display": "Житель",
      "is_primary": true
    }
  ]
}
```

**200 пусто:**
```json
{ "apartments": [] }
```

**405:**
```json
{ "status": "Method not allowed" }
```

---

## POST /api/v1/user/apartments

Добавить существующую квартиру текущему пользователю.  
Квартира ищется по `domik_id` + `number`.  
Первая добавленная квартира автоматически становится основной (`is_primary = true`).

**Auth:** да.

**Фронт кидает:**
```json
{
  "domik_id": "b3a1f4e2-5c8d-4a1b-9e2f-7d6c1a3b8e9f",
  "number": "42"
}
```

**201:**
```json
{
  "id": "a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "number": "42",
  "domik_id": "b3a1f4e2-5c8d-4a1b-9e2f-7d6c1a3b8e9f",
  "role": "resident",
  "is_primary": true
}
```

**400:**
```json
{ "status": "Некорректный JSON" }
{ "status": "Поля domik_id и number обязательны" }
```

**404:**
```json
{ "status": "Квартира не найдена" }
```

**409:**
```json
{ "status": "Квартира уже добавлена" }
```

**405:**
```json
{ "status": "Method not allowed" }
```

---

## GET /api/v1/user/appeals

Список обращений текущего пользователя.

**Auth:** да.

**Фронт кидает:** пустое тело (только cookie `sessionid`).

**200:**
```json
{
  "appeals": [
    {
      "id": "b3a1f4e2-5c8d-4a1b-9e2f-7d6c1a3b8e9f",
      "title": "Не работает лифт",
      "description": "Лифт не работает со вчера",
      "status": "new",
      "created_at": "2025-01-01T12:00:00Z",
      "apartment_id": "a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
      "apartment_number": "42",
      "domik_id": "b3a1f4e2-5c8d-4a1b-9e2f-7d6c1a3b8e9f",
      "domik_address": "г Понск, улица Поновая, д 52",
      "management_org": "УК"
    }
  ]
}
```

**200 пусто:**
```json
{ "appeals": [] }
```

---

## POST /api/v1/user/appeals

Создать обращение по квартире текущего пользователя.  
Дом (`domik`) подставляется автоматически из квартиры.  
Создаётся запись в истории со статусом `new`.

**Auth:** да.

**Фронт кидает:**
```json
{
  "apartment_id": "a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "title": "Не работает лифт",
  "description": "Лифт не работает со вчера"
}
```

**201:**
```json
{
  "id": "b3a1f4e2-5c8d-4a1b-9e2f-7d6c1a3b8e9f",
  "title": "Не работает лифт",
  "description": "Лифт не работает со вчера",
  "management_org": "УК",
  "status": "new",
  "created_at": "2025-01-01T12:00:00Z"
}
```

**400:**
```json
{ "status": "Некорректный JSON" }
```

**404:** (квартира не принадлежит пользователю или не существует)
```json
{ "status": "Квартира не найдена" }
```

**405:**
```json
{ "status": "Method not allowed" }
```

---

## GET /api/v1/user/appeals/<id>

Детали обращения текущего пользователя + история изменений.

**Auth:** да.

**200:**
```json
{
  "id": "b3a1f4e2-5c8d-4a1b-9e2f-7d6c1a3b8e9f",
  "title": "Не работает лифт",
  "description": "Лифт не работает со вчера",
  "status": "in_progress",
  "status_display": "В работе",
  "domik": {
    "id": "b3a1f4e2-5c8d-4a1b-9e2f-7d6c1a3b8e9f",
    "address": "г Понск, улица Поновая, д 52",
    "management_org": "УК"
  },
  "apartment": {
    "id": "a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
    "number": "42"
  },
  "created_at": "2025-01-01T12:00:00Z",
  "updated_at": "2025-01-02T09:30:00Z",
  "history": [
    {
      "status": "new",
      "status_display": "Новая",
      "text": "",
      "changed_by": "Иван",
      "changed_at": "2025-01-01T12:00:00Z"
    },
    {
      "status": "in_progress",
      "status_display": "В работе",
      "text": "Взяли в работу",
      "changed_by": "Пётр",
      "changed_at": "2025-01-02T09:30:00Z"
    }
  ]
}
```

Если `apartment` не задан, вернётся `"apartment": null`.

**404:**
```json
{ "status": "Обращение не найдено" }
```

---

## GET /api/v1/uk/domiks

Список домов, закреплённых за текущим сотрудником УК.

**Auth:** да, сотрудник УК.

**200:**
```json
{
  "domiks": [
    {
      "id": "b3a1f4e2-5c8d-4a1b-9e2f-7d6c1a3b8e9f",
      "address": "г Понск, улица Поновая, д 52",
      "fias_id": "",
      "management_org": "УК",
      "apartments_count": 100,
      "appeals_count": 5,
      "new_appeals_count": 2,
      "created_at": "2025-01-01T12:00:00Z"
    }
  ]
}
```

**405:**
```json
{ "status": "Method not allowed" }
```

---

## POST /api/v1/uk/domiks

Создать дом и квартиры.  
Доступно только пользователю с `is_jk = true`.  
Сотрудник автоматически закрепляется за домом (`JKDomik`).

**Auth:** да, сотрудник УК.

**Фронт кидает:**
```json
{
  "address": "г Понск, улица Поновая, д 52",
  "fias_id": "optional-fias-id",
  "management_org": "УК",
  "apartments": {
    "from": 1,
    "to": 100,
    "entrance": "1"
  }
}
```

**201:**
```json
{
  "status": "ok",
  "domik_id": "b3a1f4e2-5c8d-4a1b-9e2f-7d6c1a3b8e9f",
  "address": "г Понск, улица Поновая, д 52",
  "apartments_created": 100
}
```

**400:**
```json
{ "status": "Некорректный JSON" }
{ "status": "Поле address обязательно" }
{ "status": "Нужны apartments.from и apartments.to" }
{ "status": "from и to должны быть целыми числами" }
{ "status": "from должен быть >= 1" }
{ "status": "to должен быть >= from" }
{ "status": "Слишком большой диапазон: макс 1000 квартир" }
```

**403:**
```json
{ "status": "Только для сотрудников УК" }
```

**405:**
```json
{ "status": "Method not allowed" }
```

**409:**
```json
{ "status": "Дом с таким ФИАС ID уже существует" }
{ "status": "Дом с таким адресом уже существует" }
```

---

## GET /api/v1/uk/domiks/<id>

Детали дома + список квартир.  
Доступ — только если дом закреплён за текущим сотрудником УК.

**Auth:** да, сотрудник УК.

**200:**
```json
{
  "id": "b3a1f4e2-5c8d-4a1b-9e2f-7d6c1a3b8e9f",
  "address": "г Понск, улица Поновая, д 52",
  "fias_id": "",
  "management_org": "УК",
  "created_at": "2025-01-01T12:00:00Z",
  "apartments": [
    {
      "id": "a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
      "number": "1",
      "entrance": "1",
      "residents_count": 2
    }
  ]
}
```

**404:**
```json
{ "status": "Дом не найден или нет доступа" }
```

---

## GET /api/v1/uk/appeals

Список обращений по всем домам текущего сотрудника УК.  
Поддерживает фильтрацию по статусу и дому.

**Auth:** да, сотрудник УК.

**Query-параметры (опционально):**
- `status` — `new` / `in_progress` / `done` / `rejected`
- `domik_id` — UUID дома

**Фронт кидает:** пустое тело (только cookie `sessionid`).

**200:**
```json
{
  "appeals": [
    {
      "id": "b3a1f4e2-5c8d-4a1b-9e2f-7d6c1a3b8e9f",
      "title": "Не работает лифт",
      "status": "new",
      "status_display": "Новая",
      "author": {
        "id": "c1c2c3c4-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
        "name": "Иван",
        "last_name": "Иванов"
      },
      "domik_id": "b3a1f4e2-5c8d-4a1b-9e2f-7d6c1a3b8e9f",
      "domik_address": "г Понск, улица Поновая, д 52",
      "apartment_number": "42",
      "created_at": "2025-01-01T12:00:00Z",
      "updated_at": "2025-01-01T12:00:00Z"
    }
  ]
}
```

**200 пусто:**
```json
{ "appeals": [] }
```

---

## POST /api/v1/uk/appeals/<id>/status

Обновить статус обращения.  
Создаёт запись в истории.  
Доступ — только для дома, закреплённого за сотрудником УК.

**Auth:** да, сотрудник УК.

**Фронт кидает:**
```json
{
  "status": "in_progress",
  "text": "Взяли в работу"
}
```

**200:**
```json
{
  "status": "ok",
  "appeal_id": "b3a1f4e2-5c8d-4a1b-9e2f-7d6c1a3b8e9f",
  "new_status": "in_progress",
  "status_display": "В работе"
}
```

**400:**
```json
{ "status": "Некорректный JSON" }
{
  "status": "Некорректный статус",
  "allowed": ["new", "in_progress", "done", "rejected"]
}
```

**404:**
```json
{ "status": "Обращение не найдено" }
```

---

## Статусы обращений

| Код | Значение |
|---|---|
| `new` | Новая |
| `in_progress` | В работе |
| `done` | Выполнена |
| `rejected` | Отклонена |

## Роли пользователя в квартире

| Код | Значение |
|---|---|
| `resident` | Житель |
| `owner` | Собственник |
| `chair` | Председатель совета МКД |