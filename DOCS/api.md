# API

**URL (dev):** `http://127.0.0.1:8000`  
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
| POST | `/api/v1/login` | — | Вход / регистрация (юзер или УК) |
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
Ручки `/api/v1/uk/*` дополнительно требуют `is_jk = true`.

**401 (если нет сессии и настроен api_login_required):**
```json
{ "status": "Не авторизован" }
```

**403 (обычный юзер на /uk/*):**
```json
{ "status": "Только для сотрудников УК" }
```

---

## POST /api/v1/login

Вход или создание пользователя.  
Если пользователь с таким `max_id` уже есть — логинит его.  
Если нет — создаёт нового и логинит.

### Обычный пользователь

**Фронт кидает:**
```json
{ "max_id": "ivan", "name": "Иван" }
```

**200:**
```json
{
  "status": "ok",
  "id": "b3a1f4e2-5c8d-4a1b-9e2f-7d6c1a3b8e9f",
  "is_jk": false,
  "management_org": null
}
```

### Сотрудник УК

**Фронт кидает:**
```json
{
  "max_id": "uk-user",
  "name": "УК Сотрудник",
  "is_jk": true,
  "management_org": { "name": "УК Тест", "inn": "1234567890" }
}
```

`management_org` ищется по `inn`. Если такой УК уже есть — переиспользуется, имя не перезаписывается.

**200:**
```json
{
  "status": "ok",
  "id": "cd99c33a-b6fc-4fc5-b5a0-0d2d86efe373",
  "is_jk": true,
  "management_org": {
    "id": "c79bebc7-615f-4020-a801-8c46b169ee8d",
    "name": "УК Тест",
    "inn": "1234567890"
  }
}
```

### Если пользователь уже существует

**200:**
```json
{
  "status": "Такой пользователь уже существует",
  "id": "b3a1f4e2-5c8d-4a1b-9e2f-7d6c1a3b8e9f",
  "is_jk": false
}
```

### Ошибки

**400:**
```json
{ "status": "Некорректный JSON" }
{ "status": "Нужны поля max_id и name" }
{ "status": "Для сотрудника УК необходимо указать management_org" }
{ "status": "Для management_org нужны поля name и inn" }
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
      "management_org": { "id": "…", "name": "УК Тест" },
      "role": "resident",
      "role_display": "Житель",
      "is_primary": true
    }
  ]
}
```

`management_org` — объект `{id, name}` или `null`.

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
      "management_org": { "id": "…", "name": "УК Тест" },
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
      "management_org": { "id": "…", "name": "УК Тест" }
    }
  ]
}
```

**200 пусто:**
```json
{ "appeals": [] }
```

`management_org` — объект `{id, name}` или `null`.

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
  "management_org": { "id": "…", "name": "УК Тест" },
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
    "management_org": { "id": "…", "name": "УК Тест" }
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
`management_org` — объект `{id, name}` или `null`.

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
      "management_org": { "id": "…", "name": "УК Тест" },
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
`management_org` берётся из `request.user.management_org`, из тела запроса **не читается**.  
Сотрудник автоматически закрепляется за домом (`JKDomik`).

**Auth:** да, сотрудник УК.

**Фронт кидает:**
```json
{
  "address": "г Понск, улица Поновая, д 52",
  "fias_id": "optional-fias-id",
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
  "management_org": { "id": "…", "name": "УК Тест" },
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
{ "status": "Нет привязки к УК" }
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
  "management_org": { "id": "…", "name": "УК Тест" },
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

`text` опционален.

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

## Формат `management_org`

Во всех ручках (кроме `POST /api/v1/login`, где добавляется `inn`) `management_org` — это:

- **объект** `{ "id": "<uuid>", "name": "<название>" }` — если у дома/пользователя есть УК;
- **`null`** — если УК не задана.

Никогда не возвращается строкой, потому что модель `ManagementOrganization` связана через FK.

## Cookie-аутентификация

После `POST /api/v1/login` сервер ставит две куки:

| Cookie | Назначение | Срок жизни |
|---|---|---|
| `sessionid` | Основная сессия, привязана к пользователю | 2 недели (дефолт Django) |
| `csrftoken` | CSRF-токен (не проверяется, т.к. все ручки `csrf_exempt`) | 1 год |

Клиент должен сохранять `sessionid` и отправлять его в каждом следующем запросе (браузер делает это автоматически).