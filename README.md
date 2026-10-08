# opencodeai

Платформа с подключаемыми бизнес-модулями. Модульный монолит в одном репозитории,
каждый бизнес-модуль живёт в своей папке и имеет свою схему PostgreSQL.

Репозиторий: `git@github.com:ermoshinss/opencodeai.git` (приватный, доступ по deploy key).

## Структура

```text
opencodeai/
├── apps/
│   ├── api/                    # backend (FastAPI + SQLAlchemy + Alembic)
│   │   ├── app/
│   │   │   ├── core/           # инфраструктура: config, db, logging, errors, security
│   │   │   └── modules/        # бизнес-модули: identity, tenancy, authorization, registry, audit
│   │   └── migrations/         # миграции Alembic (единый каталог, новая ревизия = новый файл)
│   └── web/                    # frontend (React + Vite + TypeScript)
├── packages/
│   └── contracts/              # общие DTO/типы API между клиентом и сервером
├── infra/                      # Docker, окружения, развёртывание
├── docs/
│   ├── architecture/           # схемы: модули, схемы БД, ключевые решения
│   └── agent-logs/             # журнал решений по датам
├── .github/workflows/          # CI: lint, typecheck, test, build
├── .env.example                # шаблон окружения (секреты сюда не попадают)
└── pyproject.toml              # tooling: ruff, mypy, pytest
```

## Правила архитектуры

- **`core`** — только инфраструктура и общие примитивы: настройки, подключение к БД,
  ошибки, логирование, авторизация. Бизнес-логика в `core` не попадает.
- **`modules/<name>`** — один бизнес-модуль: домен, API, таблицы. Модули общаются
  через сервисы и контракты, а не через прямое обращение к чужим моделям.
- **База данных** — одна БД, отдельная PostgreSQL-схема на модуль (`platform` для ядра).
  Пользовательские workspace изолируются через `workspace_id`, отдельная БД на проект не создаётся.
- **Два уровня «проекта»**: бизнес-модуль — папка в репозитории;
  пользовательский проект — запись в таблице `platform.projects`.
- **Миграции** не переписываются: каждое изменение — новая ревизия Alembic.
- Секреты — только в файле окружения с правами `600`; в репозиторий попадает
  только `.env.example`.

## Разработка

```bash
# backend (venv на хосте: /home/ermoshinss/.venvs/opencodeai)
.venv/bin/pip install -r apps/api/requirements.txt   # или: pip install ".[dev]"

# миграции
ENV_FILE=~/.config/opencodeai/.env alembic -c apps/api/alembic.ini upgrade head

# api (из корня репозитория)
PYTHONPATH=apps/api ENV_FILE=~/.config/opencodeai/.env \
  .venv/bin/uvicorn app.main:app --reload

# проверки
ruff check apps/api/app apps/api/tests
mypy apps/api/app
pytest

# frontend
npm --prefix apps/web install
```

Секреты хранятся в `~/.config/opencodeai/.env` (права `600`); в репозитории
только `.env.example`. Архитектура — `docs/architecture/overview.md`,
журнал решений — `docs/agent-logs/`.
