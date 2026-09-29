# max_back

**Commit:** `3dff61877c8366cd3d4152f567d24b73cae18ed9`
**API:** https://fancifully-fortified-bonito.cloudpub.ru

Backend-сервис для управления многоквартирными домами: обращения жителей,
опросы, уведомления, капитальный ремонт, роли УК и жильцов.

Решение реализовано на **Django 5** с REST API, с которым работает
**мини-приложение в мессенджере MAX**. Дополнительно бэкенд отправляет
push-уведомления пользователям через **MAX Bot API**.

---

## Содержание

1. [Назначение решения](#назначение-решения)
2. [Целевая аудитория и проблема](#целевая-аудитория-и-проблема)
3. [Основной пользовательский сценарий](#основной-пользовательский-сценарий)
4. [Состав репозитория](#состав-репозитория)
5. [Быстрый старт (Docker)](#быстрый-старт-docker)
6. [Переменные окружения](#переменные-окружения)
7. [Тестовые данные и учётные записи](#тестовые-данные-и-учётные-записи)
8. [Пошаговый сценарий проверки](#пошаговый-сценарий-проверки)
9. [API](#api)
10. [Внешние сервисы и интеграции](#внешние-сервисы-и-интеграции)
11. [Работа с данными](#работа-с-данными)
12. [Зависимости](#зависимости)
13. [Порты](#порты)
14. [Остановка и повторный запуск](#остановка-и-повторный-запуск)
15. [Известные ограничения](#известные-ограничения)

---

## Назначение решения

Сервис закрывает три ключевые задачи управления МКД, обозначенные как
актуальные в треке «Умный город»:

- **Аварии, заявки и коммунальные услуги.** Житель создаёт обращение по
  своей квартире и видит его статус и историю; УК принимает обращения,
  меняет статус и пишет комментарий, жителю приходит push в MAX.
- **Жилищный навигатор: дом, капремонт, тарифы, документы.** По каждому
  дому ведётся счёт капитального ремонта и программа работ с тарифами,
  суммами, статусами и подрядчиками.
- **Домовое сообщество, собрания, коммуникация с УК.** Опросы по дому,
  голосование жителей, результаты в реальном времени, а также
  уведомления от УК всем жителям дома.

Сервис разделяет две роли: **житель** (`is_jk=false`) и **сотрудник УК**
(`is_jk=true` + привязка к `ManagementOrganization`). Это позволяет
использовать один бэкенд и для мини-приложения жителя, и для панели УК.

---

## Целевая аудитория и проблема

**Приоритетный сегмент:** жители и собственники квартир в МКД, которые
управляются УК, а также сотрудники этих УК, работающие с обращениями.

**Проблема:** обращение в УК сегодня часто требует звонка или переписки
в мессенджере, житель не знает, зарегистрировано ли обращение, кому
передано и в какой срок будет рассмотрено. УК, в свою очередь, тратит
время на ручную фиксацию обращений. Между жителем и УК нет единого
цифрового канала, где обращение регистрируется, обрабатывается и
доводится до результата.

**Решение:** сервис даёт жителю и УК единый канал на базе MAX. Житель
создаёт обращение в мини-приложении, УК обрабатывает его на своей
стороне, житель получает push об изменении статуса.

---

## Основной пользовательский сценарий

### Житель

1. Открывает мини-приложение в MAX.
2. Авторизуется автоматически (по данным MAX Bridge) — `POST /api/v1/login`.
3. Ищет свой дом по адресу — `GET /api/v1/domiks?search=...`.
4. Вводит код привязки, полученный от УК, — `POST /api/v1/user/apartments`.
   Первая квартира становится основной.
5. Видит список своих квартир — `GET /api/v1/user/apartments`.
6. Создаёт обращение по квартире — `POST /api/v1/user/appeals`.
7. Отслеживает статус и историю — `GET /api/v1/user/appeals/<id>`.
8. Получает push в MAX при изменении статуса.
9. Голосует в опросах по дому — `POST /api/v1/user/polls/<id>/vote`.
10. Смотрит уведомления от УК и раздел капремонта.

### Сотрудник УК

1. Авторизуется через `POST /api/v1/login` с `is_jk=true` и данными
   организации (`name`, `inn`). Организация создаётся или переиспользуется
   по ИНН.
2. Создаёт дом с диапазонами квартир — `POST /api/v1/uk/domiks`.
3. Генерирует код доступа для квартиры —
   `POST /api/v1/uk/domiks/<id>/apartments/<apartment_id>/generate-key`.
4. Передаёт код жителю.
5. Обрабатывает обращения: `GET /api/v1/uk/appeals`,
   `POST /api/v1/uk/appeals/<id>/status`.
6. Публикует уведомления жителям — `POST /api/v1/uk/notifications`.
7. Создаёт опросы по дому — `POST /api/v1/uk/polls`.
8. Ведёт раздел капремонта —
   `POST/PATCH /api/v1/uk/domiks/<id>/capital-repair`.

---

## Состав репозитория

```
max_back/
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── .dockerignore
├── .env.example                       # шаблон переменных окружения
├── .gitignore
├── requirements.txt
├── manage.py
├── README.md                          # этот файл
├── DOCS/
│   ├── api.md                         # текстовая документация API
│   ├── api.yaml                       # OpenAPI 3.0.3 спецификация
│   ├── seed.json                      # описание тестового набора
│   └── DATA-API.yaml                  # описание обязательных проверок
├── certs/
│   └── Russian_Trusted_Root_CA.cer    # корневой сертификат Минцифры
├── data/
│   └── db.sqlite3                     # файл БД (том, создаётся при первом запуске)
├── staticfiles/                       # собранная статика (после collectstatic)
├── api/                               # конфигурация Django-проекта
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
└── apihandler/                        # основное приложение
    ├── admin.py
    ├── apps.py
    ├── models.py
    ├── views.py
    ├── utils.py
    ├── tests.py
    ├── migrations/
    ├── serializers/
    │   ├── appeal.py
    │   ├── notification.py
    │   ├── poll.py
    │   └── capital_repair.py
    ├── max_bot/
    │   ├── __init__.py                # httpx-клиент MAX Bot API
    │   └── notifications.py           # send_message() и обёртки
    ├── gis_api/
    │   ├── __init__.py
    │   └── collect.py                 # DaData + HouseScore
    └── management/
        └── commands/
            ├── sync_houses.py
            └── load_demo.py           # загрузка тестовых данных
```

---

## Быстрый старт (Docker)

### Одна команда для запуска

```bash
docker compose up --build
```

Поднимается сервис `web` (Gunicorn на порту `8000`) и `cloudpub`
(публикация в HTTPS). При старте `entrypoint.sh` выполняет:

```sh
python manage.py migrate --noinput
python manage.py collectstatic --noinput
exec "$@"
```

### Первичная настройка

Перед запуском скопируйте шаблон переменных окружения и заполните его:

```bash
cp .env.example .env
# откройте .env и заполните SECRET_KEY, MAX_BOT_TOKEN, CLOUDPUB_TOKEN
```

Сгенерировать `SECRET_KEY`:

```bash
python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
```

### Загрузка тестовых данных (один раз)

```bash
docker compose exec web python manage.py load_demo
```

### Запуск без публикации (только локально)

Если не нужен внешний HTTPS-адрес, запускайте только `web`:

```bash
docker compose up --build web
```

После старта:

- API: `http://127.0.0.1:8000/api/v1/`
- Админка: `http://127.0.0.1:8000/admin/`

### Создание суперпользователя админки

```bash
docker compose exec web python manage.py createsuperuser
```

---

## Переменные окружения

Полный список с комментариями — в [`.env.example`](./.env.example).

| Переменная | Обязательна | Назначение |
|---|---|---|
| `SECRET_KEY` | да | Секретный ключ Django |
| `DJANGO_DEBUG` | нет (по умолчанию `0`) | Включение режима отладки |
| `ALLOWED_HOSTS` | нет (по умолчанию `*`) | Список разрешённых хостов через запятую |
| `DB_PATH` | нет | Путь к SQLite-файлу, по умолчанию `/app/data/db.sqlite3` |
| `MAX_BOT_TOKEN` | да (для пушей) | Токен бота MAX, выданный организаторами |
| `MAX_API_BASE_URL` | нет | Базовый URL API MAX, по умолчанию `https://platform-api2.max.ru` |
| `CLOUDPUB_TOKEN` | да (для публикации) | Токен CloudPub для HTTPS-адреса |
| `CORS_ALLOWED_ORIGINS` | нет | Origin'ы, с которых разрешены CORS-запросы |
| `CSRF_TRUSTED_ORIGINS` | нет | Доверенные origin'ы для CSRF |

---

## Тестовые данные и учётные записи

### Быстрый старт

```bash
docker compose exec web python manage.py load_demo
```

Команда создаст (или обновит) демо-набор данных. Идемпотентна —
повторный запуск не создаёт дублей.

Если нужно предварительно удалить старые демо-данные:

```bash
docker compose exec web python manage.py load_demo --reset
```

Флаг `--reset` удаляет только демо-сущности по фиксированным
`fias_id`, `max_id`, `inn` — боевые данные не пострадают.

### Что создаётся

| Сущность | Значение |
|---|---|
| УК | `УК Тест`, ИНН `1234567890` |
| Сотрудник УК | `uk_demo` / `uk_demo_pass` |
| Житель | `resident_demo` / `resident_pass` |
| Дом | `г. Тест, ул. Тестовая, д. 1` (ФИАС `demo-fias-1`) |
| Квартиры | 10 шт., номера 1–10, подъезд 1 |
| Код привязки | `1234567890` для квартиры №1 |

Описание набора — в файле [`DATA/seed.json`](./DATA/seed.json).

### Учётные записи

| Роль | max_id | Пароль | Доступ |
|---|---|---|---|
| Сотрудник УК | `uk_demo` | `uk_demo_pass` | `/api/v1/uk/*`, `/admin/` |
| Житель | `resident_demo` | `resident_pass` | `/api/v1/user/*`, `/api/v1/me` |
| Админ | `admin` | создать через `createsuperuser` | `/admin/` |

Пароли не используются для входа по API (авторизация идёт
по `max_id` через `POST /api/v1/login`), но корректно выставлены
для входа в Django admin.

### Восстановление с чистого листа

```bash
docker compose down
rm -rf ./data
docker compose up --build -d
docker compose exec web python manage.py load_demo
```

---

## Пошаговый сценарий проверки

### Часть 1. Житель

1. **Логин**

   ```
   POST http://127.0.0.1:8000/api/v1/login
   Content-Type: application/json

   { "max_id": "resident_demo", "name": "Иван" }
   ```

   Ожидаемо: `200`, `{ "status": "ok", ... }`, выставлена cookie `sessionid`.

2. **Поиск дома**

   ```
   GET http://127.0.0.1:8000/api/v1/domiks?search=Тест
   ```

   Ожидаемо: `200`, массив с домом «г. Тест, ул. Тестовая, д. 1».

3. **Привязка квартиры**

   ```
   POST http://127.0.0.1:8000/api/v1/user/apartments
   Content-Type: application/json

   {
     "domik_id": "<id дома из шага 2>",
     "number": "1",
     "code": "1234567890"
   }
   ```

   Ожидаемо: `201`, квартира привязана, `is_primary: true`.
   Код привязки удаляется.

4. **Создание обращения**

   ```
   POST http://127.0.0.1:8000/api/v1/user/appeals
   Content-Type: application/json

   {
     "apartment_id": "<id квартиры из шага 3>",
     "title": "Не работает лифт",
     "description": "Лифт не работает со вчера"
   }
   ```

   Ожидаемо: `201`, обращение создано, статус `new`.

5. **Список обращений**

   ```
   GET http://127.0.0.1:8000/api/v1/user/appeals
   ```

   Ожидаемо: `200`, в списке одно обращение.

### Часть 2. УК

6. **Логин УК**

   ```
   POST http://127.0.0.1:8000/api/v1/login
   Content-Type: application/json

   {
     "max_id": "uk_demo",
     "name": "Сотрудник",
     "is_jk": true,
     "management_org": { "name": "УК Тест", "inn": "1234567890" }
   }
   ```

   Ожидаемо: `200`, `is_jk: true`, возвращён объект УК.

7. **Список обращений по домам УК**

   ```
   GET http://127.0.0.1:8000/api/v1/uk/appeals
   ```

   Ожидаемо: `200`, в списке обращение «Не работает лифт».

8. **Изменение статуса обращения**

   ```
   POST http://127.0.0.1:8000/api/v1/uk/appeals/<id>/status
   Content-Type: application/json

   { "status": "in_progress", "text": "Передано мастеру" }
   ```

   Ожидаемо: `200`, статус обновлён, запись добавлена в историю,
   жителю отправлен push через MAX Bot API.

9. **Создание опроса**

   ```
   POST http://127.0.0.1:8000/api/v1/uk/polls
   Content-Type: application/json

   {
     "domik_id": "<id дома>",
     "title": "Ремонт подъезда",
     "description": "Голосуем за ремонт",
     "choices": ["За", "Против"]
   }
   ```

   Ожидаемо: `201`, опрос создан, всем жителям дома отправлен push.

10. **Публикация уведомления**

    ```
    POST http://127.0.0.1:8000/api/v1/uk/notifications
    Content-Type: application/json

    {
      "domik_id": "<id дома>",
      "title": "Отключение воды",
      "text": "12 января с 10:00 до 14:00"
    }
    ```

    Ожидаемо: `201`, уведомление создано и разослано.

### Часть 3. Проверка результата жителем

11. **История обращения**

    ```
    GET http://127.0.0.1:8000/api/v1/user/appeals/<id>
    ```

    Ожидаемо: статус `in_progress`, история содержит запись «Передано мастеру».

12. **Голосование в опросе**

    ```
    POST http://127.0.0.1:8000/api/v1/user/polls/<id>/vote
    Content-Type: application/json

    { "choice_id": "<id варианта>" }
    ```

    Ожидаемо: `201`, голос принят.

13. **Просмотр уведомлений**

    ```
    GET http://127.0.0.1:8000/api/v1/user/notifications
    ```

    Ожидаемо: `200`, в списке уведомление «Отключение воды».

### Автоматические тесты

```bash
docker compose exec web python manage.py test
```

Все тесты из `apihandler/tests.py` должны пройти без ошибок.

---

## API

Полная документация:

- [`api.md`](DOCS/api.md) — текстовая, с примерами запросов и ответов.
- [`api.yaml`](DOCS/api.yaml) — спецификация OpenAPI 3.0.3.
- [`DATA-API.yaml`](DOCS/DATA-API.yaml) — описание обязательных
  проверок для автоматической оценки.

---

## Внешние сервисы и интеграции

### MAX Bot API

- **Назначение:** отправка push-сообщений жителям при событиях
  (обращения, опросы, уведомления, капремонт).
- **Обязательна:** для полноценной работы уведомлений.
- **Переменные:** `MAX_BOT_TOKEN`, `MAX_API_BASE_URL`.
- **Код:** `apihandler/max_bot/__init__.py` (httpx-клиент),
  `apihandler/max_bot/notifications.py` (функция `send_message`).
- **Поведение без токена:** функция `_safe_send_message` глушит
  исключения, сервис продолжает работу, пуш не отправляется.

### Корневой сертификат Минцифры

- **Назначение:** для HTTPS-запросов к `platform-api2.max.ru` может
  потребоваться корневой сертификат НУЦ Минцифры России.
- **Файл:** `certs/Russian_Trusted_Root_CA.cer`.
- **Использование:** если `httpx` не доверяет `platform-api2.max.ru`,
  укажите `verify` в клиенте:

  ```python
  client = httpx.Client(
      base_url=settings.MAX_API_BASE_URL,
      verify="certs/Russian_Trusted_Root_CA.cer",
  )
  ```

- **Обязательно:** нет, если сертификат уже установлен в системном
  хранилище.

### CloudPub

- **Назначение:** публикация локального контейнера `web` по HTTPS
  для проверки мини-приложения MAX (MAX требует HTTPS).
- **Обязательна:** нет. Можно не использовать, если у вас есть
  собственный домен или туннель (Cloudflare Tunnel, ngrok).
- **Переменные:** `CLOUDPUB_TOKEN`.
- **Отключение:** уберите сервис `cloudpub` из `docker-compose.yml`
  или запускайте только `web`:

  ```bash
  docker compose up --build web
  ```

### DaData / HouseScore (опционально)

- **Назначение:** команда `sync_houses` использует `dadata` и
  `housescore` для синхронизации реестра домов.
- **Обязательна:** нет. Для MVP не нужна, команда не запускается
  автоматически.
- **Код:** `apihandler/gis_api/collect.py`,
  `apihandler/management/commands/sync_houses.py`.

---

## Работа с данными

- **Хранилище:** SQLite. Файл БД монтируется в `./data/db.sqlite3`
  (см. volume в `docker-compose.yml`).
- **Миграции:** применяются автоматически при старте контейнера
  (`entrypoint.sh`).
- **Модель данных:** см. `apihandler/models.py`. Ключевые сущности —
  `User`, `ManagementOrganization`, `Domik`, `Apartment`,
  `UserApartment`, `Appeal`, `AppealHistory`, `Poll`, `Choice`, `Vote`,
  `Notification`, `CapitalRepair`, `CapitalRepairWork`, `ApartmentKey`.
- **Тестовые данные:** синтетические, создаются командой
  `python manage.py load_demo` (см. раздел
  «Тестовые данные и учётные записи»).
- **Внешние источники данных** (ГИС ЖКХ, DaData, HouseScore) в MVP
  не подключены к основному сценарию. Команда `sync_houses` —
  заготовка для масштабирования.

---

## Зависимости

Основные:

- Python 3.12
- Django 5.2
- djangorestframework (только сериализаторы)
- dadata
- httpx
- gunicorn
- whitenoise
- django-cors-headers

Полный список с версиями — в [`requirements.txt`](./requirements.txt).
Зависимости фиксируются, чтобы обеспечить воспроизводимость сборки.

Установка локально (без Docker):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py load_demo
python manage.py runserver
```

---

## Порты

| Сервис | Порт | Описание |
|---|---|---|
| `web` (Gunicorn) | `8000` | API + админка |
| `cloudpub` | — | Исходящее HTTPS-соединение, порт не публикуется |

Проверка доступности: `http://127.0.0.1:8000/admin/login/` должен
вернуть `200`.

---

## Остановка и повторный запуск

### Остановить

```bash
docker compose down
```

Данные в `./data/db.sqlite3` сохраняются, потому что том монтируется
с хоста.

### Полностью удалить (включая БД)

```bash
docker compose down -v
rm -rf ./data
```

### Перезапустить

```bash
docker compose up --build
```

или

```bash
docker compose restart web
```

---

## Известные ограничения

- **SQLite.** В проде рекомендуется PostgreSQL, но для хакатона
  SQLite подходит и упрощает воспроизводимость.
