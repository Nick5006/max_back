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

## POST /api/v1/user/apartments

Добавить существующую квартиру текущему пользователю.  
Квартира ищется по `domik_id` + `number`.

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
  "role": "resident"
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

**404:**
```json
{ "status": "Квартира не найдена" }
```

**405:**
```json
{ "status": "Method not allowed" }
```

---

## POST /api/v1/uk/domiks

Создать дом и квартиры.  
Доступно только пользователю с `is_jk = true`.

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

**409:**
```json
{ "status": "Дом с таким ФИАС ID уже существует" }
{ "status": "Дом с таким адресом уже существует" }
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