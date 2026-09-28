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
| GET | `/api/v1/domiks` | auth | Поиск домов по адресу |
| GET | `/api/v1/user/apartments` | user | Список квартир |
| POST | `/api/v1/user/apartments` | user | Привязать квартиру по коду |
| DELETE | `/api/v1/user/apartments/<apartment_id>/delete` | user | Отвязать квартиру |
| GET | `/api/v1/user/appeals` | user | Список своих обращений |
| POST | `/api/v1/user/appeals` | user | Создать обращение |
| GET | `/api/v1/user/appeals/<id>` | user | Детали обращения + история |
| GET | `/api/v1/user/polls` | auth | Опросы по домам пользователя |
| GET | `/api/v1/user/polls/<id>` | user / uk | Детали опроса |
| POST | `/api/v1/user/polls/<id>/vote` | user | Проголосовать / сменить голос |
| GET | `/api/v1/user/polls/<id>/results` | user / uk | Результаты опроса |
| GET | `/api/v1/user/notifications` | user | Уведомления по домам пользователя |
| GET | `/api/v1/user/notifications/<id>` | user | Детали уведомления (юзер) |
| GET | `/api/v1/user/domik/<id>/capital-repair` | user | Капремонт по дому (для жильца) |
| GET | `/api/v1/uk/domiks` | uk | Дома сотрудника УК |
| POST | `/api/v1/uk/domiks` | uk | Создать дом + квартиры |
| GET | `/api/v1/uk/domiks/<id>` | uk | Детали дома + квартиры |
| DELETE | `/api/v1/uk/domiks/<id>` | uk | Удалить дом (каскадно) |
| GET | `/api/v1/uk/domiks/<id>/apartments` | uk | Список квартир дома |
| POST | `/api/v1/uk/domiks/<id>/apartments` | uk | Создать квартиру в доме |
| GET | `/api/v1/uk/domiks/<id>/apartments/<apartment_id>` | uk | Детали квартиры + жильцы |
| PATCH | `/api/v1/uk/domiks/<id>/apartments/<apartment_id>` | uk | Изменить квартиру |
| DELETE | `/api/v1/uk/domiks/<id>/apartments/<apartment_id>` | uk | Удалить квартиру |
| POST | `/api/v1/uk/domiks/<id>/apartments/<apartment_id>/generate-key` | uk | Сгенерировать код привязки |
| GET | `/api/v1/uk/appeals` | uk | Все обращения по домам УК |
| GET | `/api/v1/uk/appeals/<id>` | uk | Детали обращения + история (УК) |
| POST | `/api/v1/uk/appeals/<id>/status` | uk | Обновить статус обращения |
| GET | `/api/v1/uk/polls` | uk | Опросы по домам УК |
| POST | `/api/v1/uk/polls` | uk | Создать опрос |
| POST | `/api/v1/uk/polls/<id>/close` | uk | Закрыть опрос |
| DELETE | `/api/v1/uk/polls/<id>` | uk | Удалить опрос |
| GET | `/api/v1/uk/notifications` | uk | Уведомления по домам УК |
| POST | `/api/v1/uk/notifications` | uk | Создать уведомление |
| GET | `/api/v1/uk/notifications/<id>` | uk | Детали уведомления (УК) |
| GET | `/api/v1/uk/domiks/<id>/capital-repair` | uk | Капремонт дома (УК) |
| POST | `/api/v1/uk/domiks/<id>/capital-repair` | uk | Создать счёт капремонта |
| PATCH | `/api/v1/uk/domiks/<id>/capital-repair` | uk | Обновить показатели капремонта |
| GET | `/api/v1/uk/domiks/<id>/capital-repair/works` | uk | Программа работ |
| POST | `/api/v1/uk/domiks/<id>/capital-repair/works` | uk | Добавить работу |
| PATCH | `/api/v1/uk/domiks/<id>/capital-repair/works/<work_id>` | uk | Изменить работу |
| DELETE | `/api/v1/uk/domiks/<id>/capital-repair/works/<work_id>` | uk | Удалить работу |

> `auth` — любой авторизованный пользователь (юзер или УК).  
> `user` — обычный пользователь (`is_jk = false`).  
> `uk` — сотрудник УК (`is_jk = true` + есть `management_org`).

---

## Аутентификация

Кроме `POST /api/v1/login` — все ручки требуют активной сессии.  
Ручки `/api/v1/uk/*` дополнительно требуют `is_jk = true` и наличия `management_org`.

**401 (если нет сессии):**
```json
{ "status": "Не авторизован" }
```

**403 (обычный юзер на /uk/*):**
```json
{ "status": "Только для сотрудников УК" }
```

**403 (УК без привязки к организации):**
```json
{ "status": "Нет привязки к УК" }
```

**Общий ответ на некорректный JSON (все ручки, где читается тело):**

```json
{ "status": "Некорректный JSON" }
```

```json
{ "status": "Тело запроса должно быть JSON-объектом" }
```

Первое — если тело не парсится как JSON, второе — если JSON валиден, но это не объект (например, массив или строка).

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

`management_org` в этом ответе **не возвращается** — ни для юзера, ни для УК.

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
{ "status": "Тело запроса должно быть JSON-объектом" }
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
  "management_org": null,
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

## GET /api/v1/domiks

Поиск домов по адресу (подстрока, регистронезависимо).  
Нужен жильцу, чтобы найти `domik_id` перед запросом кода у УК.

**Auth:** да (любой авторизованный).

**Query-параметры:**

- `search` — минимум 2 символа. Если короче — вернётся пустой список.
- `limit` — сколько результатов вернуть. По умолчанию `10`, максимум `50`.

**200:**
```json
{
  "domiks": [
    {
      "id": "b3a1f4e2-5c8d-4a1b-9e2f-7d6c1a3b8e9f",
      "address": "г Понск, улица Поновая, д 52",
      "management_org": { "id": "…", "name": "УК Тест" }
    }
  ]
}
```

**200 (пустой запрос или ничего не найдено):**
```json
{ "domiks": [] }
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

Привязать квартиру к пользователю по коду доступа.  
Код генерирует УК через `POST /api/v1/uk/domiks/<id>/apartments/<apartment_id>/generate-key` и передаёт жильцу.  
После успешной привязки код **удаляется** (одноразовый).  
Первая добавленная квартира автоматически становится основной (`is_primary = true`).

**Auth:** да.

**Фронт кидает:**
```json
{
  "domik_id": "b3a1f4e2-5c8d-4a1b-9e2f-7d6c1a3b8e9f",
  "number": "42",
  "code": "4829175036"
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
{ "status": "Тело запроса должно быть JSON-объектом" }
{ "status": "Поля domik_id, number и code обязательны" }
```

**403 (неверный код или код не сгенерирован):**
```json
{ "status": "Неверный код доступа" }
{ "status": "Для этой квартиры не сгенерирован код доступа" }
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

## DELETE /api/v1/user/apartments/<apartment_id>/delete

Отвязать квартиру от текущего пользователя.  
Код подтверждения не требуется — UX-подтверждение («введите адрес квартиры, чтобы отвязаться») реализуется на фронте.

Если отвязывается основная квартира и есть другие привязки — одна из них автоматически становится основной.

**Auth:** да.

**Пример запроса:**
```
DELETE /api/v1/user/apartments/a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d/delete
```

**200:**
```json
{ "status": "ok" }
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

## GET /api/v1/user/appeals

Список обращений текущего пользователя.

**Auth:** да.

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
{ "status": "Тело запроса должно быть JSON-объектом" }
{ "status": { "apartment_id": ["Must be a valid UUID."] } }
{ "status": { "title": ["This field is required."] } }
{ "status": { "description": ["This field is required."] } }
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
**Только GET.** Любой другой метод → `405`.

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

**405:**
```json
{ "status": "Method not allowed" }
```

---

## Опросы

Модель опроса (`Poll`) привязана к дому (`Domik`).

**Права:**

| Действие | Кто может |
|---|---|
| Смотреть список опросов | Только юзер (по своим домам). УК получит пустой список, если у него нет своих квартир |
| Смотреть детали / результаты | Юзер — по своим домам; УК — по домам своей УК |
| Голосовать | Только юзер (не УК) |
| Создать / закрыть / удалить | Только УК своей организации |

### Структура опроса в ответе (`serialize_poll`)

```json
{
  "id": "<uuid>",
  "title": "Собрание жильцов",
  "description": "Голосуем за ремонт подъезда",
  "is_active": true,
  "created_at": "2025-01-01T12:00:00Z",
  "author": { "id": "<uuid>", "name": "Иван", "last_name": "Иванов" },
  "domik": { "id": "<uuid>", "address": "г Понск, улица Поновая, д 52" },
  "total_votes": 5,
  "choices": [
    {
      "id": "<uuid>",
      "text": "За",
      "order": 0,
      "votes_count": 4,
      "is_user_choice": true
    },
    {
      "id": "<uuid>",
      "text": "Против",
      "order": 1,
      "votes_count": 1,
      "is_user_choice": false
    }
  ],
  "user_voted": true,
  "user_choice_id": "<uuid выбранного варианта>"
}
```

**Поля `user_voted`, `user_choice_id` и `is_user_choice` присутствуют всегда** (внутри `serialize_poll` они выставляются безусловно, потому что `with_choices=True` — дефолт, а запросы всегда с авторизованным пользователем). Если пользователь ещё не голосовал — `user_voted=false`, `user_choice_id=null`, у всех вариантов `is_user_choice=false`.

---

## GET /api/v1/user/polls

Список опросов по всем домам, где у пользователя есть квартира.  
Для УК-пользователя вернёт опросы по его собственным квартирам (если они есть); чтобы получить опросы домов своей УК, используй `GET /api/v1/uk/polls`.

**Auth:** да (любой авторизованный).

**Query-параметры (опционально):**
- `domik_id` — UUID дома
- `active=1` — только активные опросы

**200:**
```json
{
  "polls": [ { /* см. структуру опроса */ } ]
}
```

**405:**
```json
{ "status": "Method not allowed" }
```

> `POST` на этот URL → `405`. Создание опросов — только через `POST /api/v1/uk/polls`.

---

## GET /api/v1/user/polls/<id>

Детали опроса.  
Доступ: дом входит в дома пользователя **или** УК-сотрудник обслуживает этот дом.

**Auth:** да (user / uk).

**200:** объект опроса.

**404:**
```json
{ "status": "Опрос не найден" }
```

---

## POST /api/v1/user/polls/<id>/vote

Проголосовать или сменить свой голос.  
Один пользователь — один голос на опрос (повторный вызов перезаписывает выбор).  
**УК голосовать не может** — для `is_jk=true` вернётся `403`.

**Auth:** да, обычный пользователь.

**Фронт кидает:**
```json
{ "choice_id": "<uuid варианта>" }
```

**201 (голос создан):**
```json
{
  "status": "ok",
  "created": true,
  "poll_id": "<uuid>",
  "choice_id": "<uuid>",
  "total_votes": 6
}
```

**200 (голос обновлён):**
```json
{
  "status": "ok",
  "created": false,
  "poll_id": "<uuid>",
  "choice_id": "<uuid>",
  "total_votes": 6
}
```

**400:**
```json
{ "status": "Опрос закрыт" }
{ "status": "Поле choice_id обязательно" }
{ "status": "Некорректный JSON" }
{ "status": "Тело запроса должно быть JSON-объектом" }
```

**403:** (УК пытается голосовать)
```json
{ "status": "Сотрудники УК не голосуют" }
```

**404:**
```json
{ "status": "Опрос не найден" }
{ "status": "Вариант не найден в этом опросе" }
```

**405:**
```json
{ "status": "Method not allowed" }
```

---

## GET /api/v1/user/polls/<id>/results

Результаты опроса.  
Доступ: дом входит в дома пользователя **или** УК-сотрудник обслуживает этот дом.

**Auth:** да (user / uk).

**200:**
```json
{
  "poll_id": "<uuid>",
  "title": "Собрание жильцов",
  "total_votes": 5,
  "results": [
    { "id": "<uuid>", "text": "За", "votes_count": 4, "percent": 80.0 },
    { "id": "<uuid>", "text": "Против", "votes_count": 1, "percent": 20.0 }
  ]
}
```

**404:**
```json
{ "status": "Опрос не найден" }
```

---

## GET /api/v1/uk/polls

Список всех опросов по домам УК текущего сотрудника.

**Auth:** да, сотрудник УК.

**Query-параметры (опционально):**
- `domik_id` — UUID дома

**200:**
```json
{
  "polls": [ { /* см. структуру опроса */ } ]
}
```

**405:**
```json
{ "status": "Method not allowed" }
```

---

## POST /api/v1/uk/polls

Создать опрос в доме. **Только для сотрудников УК.**  
Дом (`domik_id`) должен принадлежать УК текущего сотрудника.

**Auth:** да, сотрудник УК.

**Фронт кидает:**
```json
{
  "domik_id": "b3a1f4e2-5c8d-4a1b-9e2f-7d6c1a3b8e9f",
  "title": "Собрание жильцов",
  "description": "Голосуем за ремонт подъезда",
  "choices": ["За", "Против", "Воздержался"]
}
```

`choices` — массив строк или объектов `{ "text": "..." }`. Минимум 2 непустых уникальных варианта.

**201:** объект опроса.

**400:**
```json
{ "status": "Некорректный JSON" }
{ "status": "Тело запроса должно быть JSON-объектом" }
{ "status": "Поле domik_id обязательно" }
{ "status": "Поле title обязательно" }
{ "status": "Нужно минимум 2 варианта ответа" }
{ "status": "Нужно минимум 2 непустых варианта" }
{ "status": "Варианты не должны повторяться" }
```

**403:**
```json
{ "status": "Только для сотрудников УК" }
{ "status": "Нет привязки к УК" }
```

**404:**
```json
{ "status": "Дом не найден или нет доступа" }
```

**405:**
```json
{ "status": "Method not allowed" }
```

---

## POST /api/v1/uk/polls/<id>/close

Закрыть опрос (устанавливает `is_active = false`).  
**Только для сотрудников УК**, обслуживающей дом опроса.

**Auth:** да, сотрудник УК.

**200:**
```json
{
  "status": "ok",
  "poll_id": "<uuid>",
  "is_active": false
}
```

**403:**
```json
{ "status": "Только для сотрудников УК" }
{ "status": "Нет прав" }
```

**404:**
```json
{ "status": "Опрос не найден" }
```

**405:**
```json
{ "status": "Method not allowed" }
```

---

## DELETE /api/v1/uk/polls/<id>

Удалить опрос (каскадно удаляются варианты и голоса).  
**Только для сотрудников УК**, обслуживающей дом опроса.

**Auth:** да, сотрудник УК.

**200:**
```json
{ "status": "ok" }
```

**403:**
```json
{ "status": "Только для сотрудников УК" }
{ "status": "Нет прав" }
```

**404:**
```json
{ "status": "Опрос не найден" }
```

**405:**
```json
{ "status": "Method not allowed" }
```

---

## Уведомления

Модель `Notification` привязана к дому (`Domik`). Создаётся сотрудником УК.  
Пользователь видит уведомления по всем домам, где у него есть квартира.

### Состав полей по ручкам

| Ручка | `management_org` | `created_by` |
|---|---|---|
| `GET /api/v1/user/notifications` | ✅ | ❌ |
| `GET /api/v1/user/notifications/<id>` | ✅ | ✅ |
| `GET /api/v1/uk/notifications` | ❌ | ✅ |
| `GET /api/v1/uk/notifications/<id>` | ❌ | ✅ |
| `POST /api/v1/uk/notifications` (в ответе) | ❌ | ❌ |

Базовые поля всегда есть: `id`, `title`, `text`, `created_at`, `domik`.

---

## GET /api/v1/user/notifications

Список уведомлений по всем домам, где у текущего пользователя есть квартира.  
**Только GET.**

**Auth:** да, обычный пользователь.

**200:**
```json
{
  "notifications": [
    {
      "id": "<uuid>",
      "title": "Отключение воды",
      "text": "12 января с 10:00 до 14:00",
      "created_at": "2025-01-01T12:00:00Z",
      "domik": { "id": "<uuid>", "address": "г Понск, улица Поновая, д 52" },
      "management_org": { "id": "<uuid>", "name": "УК Тест" }
    }
  ]
}
```

**200 пусто:**
```json
{ "notifications": [] }
```

---

## GET /api/v1/user/notifications/<id>

Детали уведомления.  
Доступ: уведомление относится к дому, где у пользователя есть квартира.

**Auth:** да, обычный пользователь.

**200:**
```json
{
  "id": "<uuid>",
  "title": "Отключение воды",
  "text": "12 января с 10:00 до 14:00",
  "created_at": "2025-01-01T12:00:00Z",
  "domik": { "id": "<uuid>", "address": "г Понск, улица Поновая, д 52" },
  "management_org": { "id": "<uuid>", "name": "УК Тест" },
  "created_by": { "id": "<uuid>", "name": "УК Сотрудник" }
}
```

**404:**
```json
{ "status": "Уведомление не найдено" }
```

---

## GET /api/v1/uk/notifications

Список уведомлений по всем домам УК текущего сотрудника.

**Auth:** да, сотрудник УК.

**200:**
```json
{
  "notifications": [
    {
      "id": "<uuid>",
      "title": "Отключение воды",
      "text": "12 января с 10:00 до 14:00",
      "created_at": "2025-01-01T12:00:00Z",
      "domik": { "id": "<uuid>", "address": "г Понск, улица Поновая, д 52" },
      "created_by": { "id": "<uuid>", "name": "УК Сотрудник" }
    }
  ]
}
```

`created_by` — объект `{id, name}` или `null`.

**405:**
```json
{ "status": "Method not allowed" }
```

---

## POST /api/v1/uk/notifications

Создать уведомление для дома.  
Дом (`domik_id`) должен принадлежать УК текущего сотрудника.

**Auth:** да, сотрудник УК.

**Фронт кидает:**
```json
{
  "domik_id": "b3a1f4e2-5c8d-4a1b-9e2f-7d6c1a3b8e9f",
  "title": "Отключение воды",
  "text": "12 января с 10:00 до 14:00"
}
```

**201:**
```json
{
  "status": "ok",
  "notification": {
    "id": "<uuid>",
    "title": "Отключение воды",
    "text": "12 января с 10:00 до 14:00",
    "created_at": "2025-01-01T12:00:00Z",
    "domik": { "id": "<uuid>", "address": "г Понск, улица Поновая, д 52" }
  }
}
```

**400:**
```json
{ "status": { "domik_id": ["..."] } }
{ "status": { "title": ["..."] } }
{ "status": { "text": ["..."] } }
{ "status": "Некорректный JSON" }
{ "status": "Тело запроса должно быть JSON-объектом" }
```

**404:**
```json
{ "status": "Дом не найден" }
```

**405:**
```json
{ "status": "Method not allowed" }
```

---

## GET /api/v1/uk/notifications/<id>

Детали уведомления из дома УК текущего сотрудника.  
**Только GET.**

**Auth:** да, сотрудник УК.

**200:**
```json
{
  "id": "<uuid>",
  "title": "Отключение воды",
  "text": "12 января с 10:00 до 14:00",
  "created_at": "2025-01-01T12:00:00Z",
  "domik": { "id": "<uuid>", "address": "г Понск, улица Поновая, д 52" },
  "created_by": { "id": "<uuid>", "name": "УК Сотрудник" }
}
```

**404:**
```json
{ "status": "Уведомление не найдено" }
```

---

## Капитальный ремонт

Раздел по капремонту для каждого дома.  
- `CapitalRepair` — один на дом (OneToOne), содержит тариф и суммы.  
- `CapitalRepairWork` — программа работ (много на один дом).

### Структура `capital_repair`

```json
{
  "id": "<uuid>",
  "domik_id": "<uuid>",
  "tariff_per_sqm": "12.50",
  "collected_total": "100000.00",
  "spent_total": "45000.00",
  "balance": "55000.00",
  "updated_at": "2025-01-01T12:00:00Z"
}
```

Все денежные поля — строки (Decimal-сериализация).

### Структура `work`

```json
{
  "id": "<uuid>",
  "work_type": "Ремонт кровли",
  "planned_year": 2025,
  "status": "planned",
  "status_display": "Запланировано",
  "cost": "500000.00",
  "contractor": "ООО Строй",
  "description": "Полная замена",
  "completed_at": "2025-08-15"
}
```

`cost` / `contractor` / `description` / `completed_at` могут быть `null`/`""`.

### Статусы работ

| Код | Значение |
|---|---|
| `planned` | Запланировано |
| `in_progress` | В работе |
| `done` | Выполнено |

---

## GET /api/v1/user/domik/<domik_id>/capital-repair

Раздел капремонта для жителя.  
Доступ: у пользователя есть квартира в этом доме.

**Auth:** да, обычный пользователь.  
**Только GET.**

**200 (раздел заведён):**
```json
{
  "domik": { "id": "<uuid>", "address": "г Понск, улица Поновая, д 52" },
  "capital_repair": { /* см. структуру */ },
  "works": [ { /* см. структуру work */ } ]
}
```

**200 (раздел ещё не заведён):**
```json
{
  "domik": { "id": "<uuid>", "address": "г Понск, улица Поновая, д 52" },
  "capital_repair": null,
  "works": [],
  "status": "Раздел капремонта для дома ещё не заполнен"
}
```

**403 (в том числе если дом не существует — сначала проверяется доступ):**
```json
{ "status": "Нет доступа к этому дому" }
```

---

## GET /api/v1/uk/domiks/<domik_id>/capital-repair

Получить раздел капремонта дома (УК).

**Auth:** да, сотрудник УК. Дом должен принадлежать УК.

**200:**
```json
{
  "domik": { "id": "<uuid>", "address": "г Понск, улица Поновая, д 52" },
  "capital_repair": { /* или null */ },
  "works": [ { /* см. структуру work */ } ]
}
```

**404:**
```json
{ "status": "Дом не найден или нет доступа" }
```

---

## POST /api/v1/uk/domiks/<domik_id>/capital-repair

Создать счёт капремонта для дома.  
Один дом — один счёт.

**Auth:** да, сотрудник УК.

**Фронт кидает:**
```json
{ "tariff_per_sqm": "12.50" }
```

**201:**
```json
{
  "status": "ok",
  "capital_repair": { /* см. структуру */ }
}
```

**400:**
```json
{ "status": "tariff_per_sqm должен быть числом" }
{ "status": "Тариф не может быть отрицательным" }
{ "status": "Некорректный JSON" }
{ "status": "Тело запроса должно быть JSON-объектом" }
```

**404:**
```json
{ "status": "Дом не найден или нет доступа" }
```

**409:**
```json
{ "status": "Счёт капремонта для дома уже заведён" }
```

**405:**
```json
{ "status": "Method not allowed" }
```

---

## PATCH /api/v1/uk/domiks/<domik_id>/capital-repair

Обновить показатели капремонта.  
Принимает любое подмножество: `tariff_per_sqm`, `collected_total`, `spent_total`.

**Auth:** да, сотрудник УК.

**Фронт кидает:**
```json
{
  "tariff_per_sqm": "13.00",
  "collected_total": "120000.00",
  "spent_total": "50000.00"
}
```

**200:**
```json
{
  "status": "ok",
  "capital_repair": { /* см. структуру */ },
  "updated_fields": ["tariff_per_sqm", "collected_total"]
}
```

**400:**
```json
{ "status": "tariff_per_sqm должен быть числом" }
{ "status": "collected_total не может быть отрицательным" }
{ "status": "Нечего обновлять" }
{ "status": "Некорректный JSON" }
{ "status": "Тело запроса должно быть JSON-объектом" }
```

**404:**
```json
{ "status": "Дом не найден или нет доступа" }
{ "status": "Счёт капремонта для дома не заведён" }
```

**405:**
```json
{ "status": "Method not allowed" }
```

---

## GET /api/v1/uk/domiks/<domik_id>/capital-repair/works

Список работ по программе капремонта дома.

**Auth:** да, сотрудник УК.

**200:**
```json
{
  "works": [ { /* см. структуру work */ } ]
}
```

**404:**
```json
{ "status": "Дом не найден или нет доступа" }
{ "status": "Сначала заведите счёт капремонта для дома" }
```

---

## POST /api/v1/uk/domiks/<domik_id>/capital-repair/works

Добавить работу в программу капремонта.

**Auth:** да, сотрудник УК.

**Фронт кидает:**
```json
{
  "work_type": "Ремонт кровли",
  "planned_year": 2025,
  "status": "planned",
  "cost": "500000.00",
  "contractor": "ООО Строй",
  "description": "Полная замена",
  "completed_at": null
}
```

Обязательные: `work_type`, `planned_year`.  
`planned_year` — целое, 1900–2200.  
`status` — одно из `planned` / `in_progress` / `done`. По умолчанию `planned`.  
`cost` — число ≥ 0 или `null`.

**201:**
```json
{
  "status": "ok",
  "work": { /* см. структуру work */ }
}
```

**400:**
```json
{ "status": "Поле work_type обязательно" }
{ "status": "Поле planned_year обязательно" }
{ "status": "planned_year должен быть числом" }
{ "status": "planned_year вне разумных границ" }
{ "status": "Некорректный status" }
{ "status": "cost должен быть числом" }
{ "status": "cost не может быть отрицательным" }
{ "status": "Некорректный JSON" }
{ "status": "Тело запроса должно быть JSON-объектом" }
```

**404:**
```json
{ "status": "Дом не найден или нет доступа" }
{ "status": "Сначала заведите счёт капремонта для дома" }
```

**405:**
```json
{ "status": "Method not allowed" }
```

---

## PATCH /api/v1/uk/domiks/<domik_id>/capital-repair/works/<work_id>

Обновить работу. Принимает любое подмножество полей:  
`work_type`, `planned_year`, `status`, `cost`, `contractor`, `description`, `completed_at`.

**Auth:** да, сотрудник УК.

**Фронт кидает:**
```json
{
  "status": "in_progress",
  "contractor": "ООО Мост"
}
```

**200:**
```json
{
  "status": "ok",
  "work": { /* см. структуру work */ },
  "updated_fields": ["status", "contractor"]
}
```

**400:**
```json
{ "status": "work_type не может быть пустым" }
{ "status": "planned_year должен быть числом" }
{ "status": "Некорректный status" }
{ "status": "cost должен быть числом" }
{ "status": "cost не может быть отрицательным" }
{ "status": "Нечего обновлять" }
{ "status": "Некорректный JSON" }
{ "status": "Тело запроса должно быть JSON-объектом" }
```

**404:**
```json
{ "status": "Дом не найден или нет доступа" }
{ "status": "Работа не найдена" }
```

**405:**
```json
{ "status": "Method not allowed" }
```

---

## DELETE /api/v1/uk/domiks/<domik_id>/capital-repair/works/<work_id>

Удалить работу из программы капремонта.

**Auth:** да, сотрудник УК.

**200:**
```json
{ "status": "ok" }
```

**404:**
```json
{ "status": "Дом не найден или нет доступа" }
{ "status": "Работа не найдена" }
```

**405:**
```json
{ "status": "Method not allowed" }
```

---

## GET /api/v1/uk/domiks

Список домов, закреплённых за УК текущего сотрудника.

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

**Auth:** да, сотрудник УК.

**Фронт кидает (один диапазон — обратно совместимо):**
```json
{
  "address": "г Понск, улица Поновая, д 52",
  "fias_id": "optional-fias-id",
  "apartments": { "from": 1, "to": 100, "entrance": "1" }
}
```

**Фронт кидает (несколько подъездов — массив):**
```json
{
  "address": "г Понск, улица Поновая, д 52",
  "fias_id": "optional-fias-id",
  "apartments": [
    { "entrance": "1", "from": 1,  "to": 50  },
    { "entrance": "2", "from": 51, "to": 100 }
  ]
}
```

`apartments` может быть либо **объектом** (один диапазон), либо **массивом объектов** (несколько диапазонов).  
В каждом диапазоне: `from >= 1`, `to >= from`, суммарно не более 1000 квартир на дом.  
Номера квартир не должны повторяться между диапазонами.

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
{ "status": "Тело запроса должно быть JSON-объектом" }
{ "status": "Поле address обязательно" }
{ "status": "Поле apartments должно быть объектом или массивом" }
{ "status": "Нужно указать хотя бы один диапазон квартир" }
{ "status": "Элемент apartments[0] должен быть объектом" }
{ "status": "Нужны поля from и to в apartments[0]" }
{ "status": "from и to в apartments[0] должны быть целыми числами" }
{ "status": "from в apartments[0] должен быть >= 1" }
{ "status": "to в apartments[0] должен быть >= from" }
{ "status": "Слишком большой диапазон в apartments[0]: макс 1000 квартир" }
{ "status": "Квартира с номером 42 встречается в нескольких диапазонах" }
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
Доступ — только если дом принадлежит УК текущего сотрудника.

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

## DELETE /api/v1/uk/domiks/<id>

Удалить дом вместе со всеми связанными данными.

Каскадно удаляются:
- все квартиры дома (`Apartment`),
- привязки жильцов (`UserApartment`),
- коды доступа к квартирам (`ApartmentKey`),
- все обращения по дому (`Appeal`) и их история (`AppealHistory`),
- все опросы по дому (`Poll`) с вариантами (`Choice`) и голосами (`Vote`),
- уведомления дома (`Notification`),
- счёт капремонта (`CapitalRepair`) и его работы (`CapitalRepairWork`).

Доступ — только если дом принадлежит УК текущего сотрудника.

**Auth:** да, сотрудник УК.

**200:**
```json
{ "status": "ok" }
```

**401:**
```json
{ "status": "Не авторизован" }
```

**403:**
```json
{ "status": "Только для сотрудников УК" }
```

**404:**
```json
{ "status": "Дом не найден" }
```

**405:**
```json
{ "status": "Неправильный метод" }
```

---

## GET /api/v1/uk/domiks/<id>/apartments

Список квартир дома.  
Доступ — только если дом принадлежит УК текущего сотрудника.

**Auth:** да, сотрудник УК.

**200:**
```json
{
  "domik_id": "b3a1f4e2-5c8d-4a1b-9e2f-7d6c1a3b8e9f",
  "address": "г Понск, улица Поновая, д 52",
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

## POST /api/v1/uk/domiks/<id>/apartments

Создать квартиру в доме.  
Доступ — только если дом принадлежит УК текущего сотрудника.

**Auth:** да, сотрудник УК.

**Фронт кидает:**
```json
{
  "number": "101",
  "entrance": "2"
}
```

`entrance` опционален.

**201:**
```json
{
  "status": "ok",
  "id": "a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "number": "101",
  "entrance": "2"
}
```

**400:**
```json
{ "status": "Некорректный JSON" }
{ "status": "Тело запроса должно быть JSON-объектом" }
{ "status": "Поле number обязательно" }
```

**404:**
```json
{ "status": "Дом не найден или нет доступа" }
```

**409:**
```json
{ "status": "Квартира с номером 101 уже есть в этом доме" }
```

---

## GET /api/v1/uk/domiks/<id>/apartments/<apartment_id>

Детали квартиры + список жильцов/собственников.  
Доступ — только если дом принадлежит УК текущего сотрудника.

**Auth:** да, сотрудник УК.

**200:**
```json
{
  "id": "a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "number": "42",
  "entrance": "1",
  "domik_id": "b3a1f4e2-5c8d-4a1b-9e2f-7d6c1a3b8e9f",
  "domik_address": "г Понск, улица Поновая, д 52",
  "residents": [
    {
      "user_id": "c1c2c3c4-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
      "max_id": "ivan",
      "name": "Иван",
      "last_name": "Иванов",
      "role": "resident",
      "role_display": "Житель",
      "is_primary": true
    }
  ],
  "appeals_count": 3
}
```

**404:**
```json
{ "status": "Дом не найден или нет доступа" }
{ "status": "Квартира не найдена" }
```

---

## PATCH /api/v1/uk/domiks/<id>/apartments/<apartment_id>

Обновить данные квартиры (`number` и/или `entrance`).  
Доступ — только если дом принадлежит УК текущего сотрудника.

**Auth:** да, сотрудник УК.

**Фронт кидает:**
```json
{
  "number": "43",
  "entrance": "2"
}
```

Оба поля опциональны, но должен быть хотя бы одно.

**200:**
```json
{
  "status": "ok",
  "id": "a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "number": "43",
  "entrance": "2",
  "updated_fields": ["number", "entrance"]
}
```

**400:**
```json
{ "status": "Некорректный JSON" }
{ "status": "Тело запроса должно быть JSON-объектом" }
{ "status": "number не может быть пустым" }
{ "status": "Нечего обновлять" }
```

**404:**
```json
{ "status": "Дом не найден или нет доступа" }
{ "status": "Квартира не найдена" }
```

**409:**
```json
{ "status": "Квартира с номером 43 уже есть в этом доме" }
{ "status": "Конфликт уникальности: такой номер уже есть" }
```

---

## DELETE /api/v1/uk/domiks/<id>/apartments/<apartment_id>

Удалить квартиру.  
Нельзя удалить, если в квартире есть жильцы/собственники или по ней есть обращения.  
Доступ — только если дом принадлежит УК текущего сотрудника.

**Auth:** да, сотрудник УК.

**200:**
```json
{ "status": "ok" }
```

**404:**
```json
{ "status": "Дом не найден или нет доступа" }
{ "status": "Квартира не найдена" }
```

**409:**
```json
{ "status": "Нельзя удалить: в квартире 2 жильцов/собственников" }
{ "status": "Нельзя удалить: по квартире есть обращения (3)" }
```

---

## POST /api/v1/uk/domiks/<id>/apartments/<apartment_id>/generate-key

Сгенерировать код доступа к квартире.  
Код передаётся жильцу, жилец вводит его в `POST /api/v1/user/apartments` и получает привязку к квартире.  
Код **одноразовый** — удаляется после успешной привязки.  
Повторный вызов ручки для той же квартиры перезаписывает существующий код (старый перестаёт работать).

**Auth:** да, сотрудник УК.  
**Только POST.**

**Код** — 10 цифр (`secrets.choice("0123456789")`).

**Фронт кидает (опционально; тело игнорируется, `purpose` всегда `bind`):**
```json
{}
```

**200 (если код уже был и перезаписан):**
```json
{
  "status": "ok",
  "apartment_id": "a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
  "apartment_number": "42",
  "purpose": "bind",
  "code": "4829175036",
  "created_at": "2026-09-28T10:00:00Z"
}
```

**201 (если код создан впервые):** то же тело.

**404:**
```json
{ "status": "Дом не найден или нет доступа" }
{ "status": "Квартира не найдена" }
```

**405:**
```json
{ "status": "Method not allowed" }
```

---

## GET /api/v1/uk/appeals

Список обращений по всем домам УК текущего сотрудника.  
Поддерживает фильтрацию по статусу и дому.

**Auth:** да, сотрудник УК.

**Query-параметры (опционально):**
- `status` — `new` / `in_progress` / `done` / `rejected`
- `domik_id` — UUID дома

**200:**
```json
{
  "appeals": [
    {
      "id": "b3a1f4e2-5c8d-4a1b-9e2f-7d6c1a3b8e9f",
      "title": "Не работает лифт",
      "description": "Лифт не работает со вчера",
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

## GET /api/v1/uk/appeals/<id>

Детали обращения + история изменений.  
Доступ — только если обращение относится к дому УК текущего сотрудника.

**Auth:** да, сотрудник УК. **Только GET.**

**200:**
```json
{
  "id": "b3a1f4e2-5c8d-4a1b-9e2f-7d6c1a3b8e9f",
  "title": "Не работает лифт",
  "description": "Лифт не работает со вчера",
  "status": "in_progress",
  "status_display": "В работе",
  "author": {
    "id": "c1c2c3c4-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
    "max_id": "ivan",
    "name": "Иван",
    "last_name": "Иванов"
  },
  "domik": {
    "id": "b3a1f4e2-5c8d-4a1b-9e2f-7d6c1a3b8e9f",
    "address": "г Понск, улица Поновая, д 52",
    "management_org": { "id": "…", "name": "УК Тест" }
  },
  "apartment": {
    "id": "a1b2c3d4-5e6f-7a8b-9c0d-1e2f3a4b5c6d",
    "number": "42",
    "entrance": "1"
  },
  "created_at": "2025-01-01T12:00:00Z",
  "updated_at": "2025-01-02T09:30:00Z",
  "history": [
    {
      "status": "new",
      "status_display": "Новая",
      "text": "",
      "changed_by": { "id": "…", "name": "Иван", "last_name": "Иванов" },
      "changed_at": "2025-01-01T12:00:00Z"
    },
    {
      "status": "in_progress",
      "status_display": "В работе",
      "text": "Взяли в работу",
      "changed_by": { "id": "…", "name": "Пётр", "last_name": "Петров" },
      "changed_at": "2025-01-02T09:30:00Z"
    }
  ]
}
```

Если `apartment` не задан — `"apartment": null`.  
`changed_by` может быть `null`, если пользователь был удалён.

**404:**
```json
{ "status": "Обращение не найдено" }
```

**405:**
```json
{ "status": "Method not allowed" }
```

---

## POST /api/v1/uk/appeals/<id>/status

Обновить статус обращения.  
Создаёт запись в истории.  
Доступ — только для дома, принадлежащего УК текущего сотрудника.

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
{ "status": "Тело запроса должно быть JSON-объектом" }
{
  "status": "Некорректный статус",
  "allowed": ["new", "in_progress", "done", "rejected"]
}
```

**404:**
```json
{ "status": "Обращение не найдено" }
```

**405:**
```json
{ "status": "Method not allowed" }
```

---

## Справочники

### Статусы обращений

| Код | Значение |
|---|---|
| `new` | Новая |
| `in_progress` | В работе |
| `done` | Выполнена |
| `rejected` | Отклонена |

### Роли пользователя в квартире

| Код | Значение |
|---|---|
| `resident` | Житель |
| `owner` | Собственник |
| `chair` | Председатель совета МКД |

### Статусы работ капремонта

| Код | Значение |
|---|---|
| `planned` | Запланировано |
| `in_progress` | В работе |
| `done` | Выполнено |

### Формат `management_org`

Во всех ручках (кроме `POST /api/v1/login`, где добавляется `inn`) `management_org` — это:

- **объект** `{ "id": "<uuid>", "name": "<название>" }` — если у дома/пользователя есть УК;
- **`null`** — если УК не задана.

Исключение: в ветке «пользователь уже существует» ручки `POST /api/v1/login` `management_org` вообще не возвращается.

### Cookie-аутентификация

После `POST /api/v1/login` сервер ставит две куки:

| Cookie | Назначение | Срок жизни |
|---|---|---|
| `sessionid` | Основная сессия, привязана к пользователю | 2 недели (дефолт Django) |
| `csrftoken` | CSRF-токен (не проверяется, т.к. все ручки `csrf_exempt`) | 1 год |

Клиент должен сохранять `sessionid` и отправлять его в каждом следующем запросе (браузер делает это автоматически).

---

## Модель `ApartmentKey`

Одноразовый код доступа к квартире. Создаётся УК через `POST /api/v1/uk/domiks/<id>/apartments/<apartment_id>/generate-key`. Используется жильцом в `POST /api/v1/user/apartments`. Удаляется после успешной привязки.

| Поле | Тип | Описание |
|---|---|---|
| `id` | UUID | Первичный ключ |
| `apartment` | FK → Apartment | Квартира, к которой привязан код |
| `code` | CharField(10) | 10-значный цифровой код |
| `purpose` | CharField(10) | `bind` (привязка). Поле оставлено для совместимости, сейчас используется только `bind` |
| `created_by` | FK → User, null | Кто сгенерировал код |
| `created_at` | DateTime | Когда код создан |

Ограничение `unique_together = ("apartment", "purpose")` — на квартиру один активный код на каждое `purpose`. Перегенерация перезаписывает.