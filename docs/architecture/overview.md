# Архитектура opencodeai

Согласованная модель платформы. Обновляется только по решению владельца;
сводка решений по датам — в `docs/agent-logs/`.

## 1. Назначение

Платформа с подключаемыми бизнес-модулями. Целевая аудитория и сценарии
пока не определены — архитектурное ядро строится независимо от них.
Проект пишется с нуля, старый bootstrap не используется.

## 2. Ключевые решения

| № | Решение |
|---|---------|
| 1 | Модульный монолит в одном репозитории, не микросервисы |
| 2 | `core` — только инфраструктура: config, db, logging, errors, security |
| 3 | `modules/<name>` — один бизнес-модуль: домен, API, таблицы; модули общаются через сервисы и контракты |
| 4 | Два уровня изоляции: **workspace → проекты**; данные привязаны через `workspace_id` / `project_id` |
| 5 | Одна БД `opencodeai`, PostgreSQL-схема на модуль + общая схема `platform` |
| 6 | Миграции только добавляются: единый каталог Alembic, новое изменение = новая ревизия |
| 7 | RBAC `user` / `admin`; авторизация включается после первого сквозного сценария, в тестах может отключаться |
| 8 | Типы API — OpenAPI-спека из FastAPI, генерация TS-типов (один источник правды) |
| 9 | Обращение к таблицам — явные схемные имена (`tenancy.workspaces`), без `search_path` |
| 10 | Границы модулей — конвенция (README + ревью), автоматическая проверка в CI не применяется |
| 11 | Секреты — файл окружения с правами `600`, в репозитории только `.env.example` |
| 12 | GitHub, каждый проект — отдельный репозиторий; deploy key с Write access |

## 3. Структура репозитория

```text
opencodeai/
├── apps/
│   ├── api/                    # FastAPI + SQLAlchemy + Alembic
│   │   ├── app/
│   │   │   ├── core/           # config, db, logging, errors, security
│   │   │   ├── modules/        # identity, tenancy, authorization, registry, audit
│   │   │   └── main.py
│   │   └── migrations/         # единый каталог Alembic
│   └── web/                    # React + Vite + TypeScript
│       └── src/
│           ├── features/       # по папке на модуль
│           └── generated/      # TS-типы из OpenAPI (не редактировать руками)
├── packages/contracts/         # общие DTO/типы API
├── infra/                      # Docker, окружения, деплой
├── docs/
│   ├── architecture/           # схемы, ключевые решения
│   └── agent-logs/             # журнал решений по датам
├── .github/workflows/          # CI: lint, typecheck, test, build
├── .env.example
└── pyproject.toml              # ruff, mypy, pytest
```

## 4. Схемы БД

Одна БД `opencodeai`, отдельная PostgreSQL-схема на модуль.

| Схема | Владелец | Таблицы |
|-------|----------|---------|
| `platform` | ядро | `settings` (конфигурация платформы), `user_settings` (конфигурация пользователей), `module_grants` (доступ workspace × модуль) |
| `identity` | модуль | `users` |
| `tenancy` | модуль | `workspaces`, `projects`, `workspace_members` |
| `authz` | модуль authorization | `permissions`, `roles`, `role_permissions`, `role_assignments`, `superadmins` |
| `registry` | модуль | `modules` (каталог: code, title, version, state; seed `mail`) |
| `audit` | модуль | `audit_events` |

Правила:

- писать и читать можно **только таблицы своей схемы**; чужие данные —
  через сервис модуля, не через SQL;
- имя схемы authorization — **`authz`**: `authorization` — зарезервированное
  слово PostgreSQL;
- `platform.module_grants` — исключение: таблица в схеме ядра, но это домен
  authorization (разграничение доступа); читает и пишет её только authorization;
- `audit_events` заполняются всеми модулями, но таблица принадлежит `audit`;
- ссылки между модулями — по значению (`workspace_id`, `user_id`) без внешних
  ключей между схемами; целостность обеспечивает сервисный слой;

## 5. REST-конвенция

- Префикс: `/api/v1`.
- Workspace — в пути: `/api/v1/workspaces/{workspace_id}/<module>/<resource>`.
- Проект — параметр запроса или тела: `?project_id=…` / `"project_id"` в DTO.
- Права проверяются на роуте (роль пользователя) + доступ модуля
  (`platform.module_grants`) до входа в сервис.
- Ответы — JSON, ошибки — единый формат `{code, message, details}`.

Пример модуля `mail`:

| Метод | Путь | Право |
|-------|------|-------|
| GET | `/api/v1/workspaces/{ws}/mail/templates` | `mail.template.read` |
| POST | `/api/v1/workspaces/{ws}/mail/templates` | `mail.template.manage` |
| GET | `/api/v1/workspaces/{ws}/mail/templates/{id}` | `mail.template.read` |
| PATCH | `/api/v1/workspaces/{ws}/mail/templates/{id}` | `mail.template.manage` |
| DELETE | `/api/v1/workspaces/{ws}/mail/templates/{id}` | `mail.template.manage` |
| POST | `/api/v1/workspaces/{ws}/mail/messages` | `mail.send` |
| GET | `/api/v1/workspaces/{ws}/mail/messages` | `mail.send.read` |
| POST | `/api/v1/workspaces/{ws}/mail/events` | вебхук провайдера (HMAC) |

Структура модуля:

```text
apps/api/app/modules/mail/
├── router.py     # эндпоинты: валидация, права, вызов service
├── service.py    # бизнес-логика, транзакции
├── models.py     # SQLAlchemy → таблицы схемы mail
└── schemas.py    # Pydantic DTO → OpenAPI-спека

apps/web/src/features/mail/
├── api/mail.ts   # вызовы API, типы из src/generated
├── hooks/
└── components/
```

Модуль authorization (админка, права):

| Метод | Путь | Назначение |
|-------|------|-----------|
| GET | `/api/v1/admin/users` | все пользователи |
| GET | `/api/v1/admin/workspaces` | все workspace |
| GET | `/api/v1/admin/modules` | весь каталог модулей |
| GET | `/api/v1/admin/superadmins` | суперадмины платформы |
| GET | `/api/v1/admin/roles` | роли и scope |
| GET | `/api/v1/admin/grants` | все `platform.module_grants` |
| POST | `/api/v1/admin/workspaces/{ws}/modules` | включить/выключить модуль |

Зависимости между модулями — только через сервисы: authorization зовёт
`identity`, `tenancy`, `registry` через их сервисы; прямого SQL по чужим
схемам нет (кроме исключения `platform.module_grants` для authorization).

Схема прав создана, проверка ролей включается вместе с RBAC
(после первого сквозного сценария).

## 6. Стек

- Backend: Python ≥3.12, FastAPI, SQLAlchemy 2, Alembic, psycopg3,
  pydantic-settings, uvicorn.
- Frontend: React 19, TypeScript 5.7, Vite 6.
- Tooling: ruff (line-length 100), mypy, pytest, покрытие — pytest-cov.
- БД: PostgreSQL `127.0.0.1:5433` (5432 занят в WSL).

## 7. Порядок развития

1. БД `opencodeai` + первая ревизия Alembic (схема `platform`).
2. `core`: config, db, logging, errors, health.
3. Первый сквозной сценарий: workspace → проект → доступ к модулю.
4. `authorization` (включаем RBAC), `audit`.
5. Контракты (OpenAPI → TS), frontend, GitHub Actions.
6. Защита `main`, теги релизов, бэкапы БД.

## 8. Открытые вопросы

1. Назначение продукта — определим позже, архитектуру не блокирует.
2. Межмодульные вызовы — решено: синхронные сервисы в одном процессе
   (реализовано на authorization: зовёт сервисы identity/tenancy/registry).
3. Мультисхемные миграции — решено: отдельная ревизия на схему.
