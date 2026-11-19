# SunStay — информационная система гостиницы

Курсовой проект: веб-приложение для автоматизации деятельности бутик-отеля SunStay.

Система покрывает номерной фонд, тарифы, гостей, бронирования, заселение/выселение, folio, платежи, возвраты, хаускипинг, техобслуживание, расходники, отчёты, RBAC, аудит, резервное копирование и импорт/экспорт CSV.

## Стек

- **База данных:** PostgreSQL 16, SQL-процедуры, функции, триггеры, представления.
- **Backend:** Python 3.13, FastAPI, psycopg 3, PyJWT, bcrypt.
- **Analytics:** отдельный FastAPI-микросервис для отчётов.
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Recharts, Lucide.
- **Инфраструктура:** Docker Compose, Nginx, Adminer.

## Архитектура

```
web (Nginx + React SPA)
  ├── /api/*        → api (FastAPI core, :8000) → PostgreSQL
  └── /analytics/*  → analytics (FastAPI reports, :8001) → PostgreSQL
```

## Быстрый запуск

```powershell
Copy-Item .env.example .env
docker compose up -d --build
```

После запуска:

- Веб-приложение: http://localhost:8080
- API и OpenAPI: http://localhost:8000/api/docs
- Analytics API: http://localhost:8001/api/docs
- Adminer: http://localhost:8081

## Демо-аккаунты

Пароль для всех демо-аккаунтов: `SunStay2026!`

| Роль | Email |
|---|---|
| Гость | guest.demo@sunstay.example |
| Менеджер | smirnova@sunstay.example |
| Хаускипинг | fedorov@sunstay.example |
| Управляющий отелем | volkov@sunstay.example |
| Администратор БД | dba@sunstay.example |

На странице входа есть кнопки быстрого демо-входа.

## Что реализовано

- 37 таблиц, 14 представлений, ограничения PK/FK/CHECK/UNIQUE, exclusion-constraint против пересечения броней.
- Функции и процедуры: создание брони, подтверждение, отмена, заселение, выселение, ночной аудит, услуги, платежи, возвраты, хаускипинг, расходники, техзаявки, статусы номеров.
- Триггеры: аудит изменений и ошибок, валидация брони, контроль остатков расходников, запрет изменений закрытого бизнес-дня и разрешение платежей после его закрытия.
- RBAC на 5 ролей, JWT access/refresh-сессии, bcrypt, журнал входов, блокировка после 3 неудачных попыток на 30 секунд.
- Настройки пользователя на сервере: тема, язык, формат даты/чисел, размер страниц, сохранённые фильтры.
- Две темы, RU/EN, 10 горячих клавиш.
- Импорт банковской выписки и тарифов CSV с предпросмотром и отчётом об ошибках.
- Экспорт CSV, PNG и PDF-счетов.
- Отчёты: загрузка, ADR/RevPAR, отмены/no-show, статусы номеров, расходники.
- Шифрование телефонов и документов (Fernet), маскирование контактов, поиск по хэшу и безопасное заселение.
- Онлайн-статистика пользователей, блокировка с причиной, аудит с ошибками и фильтрами.
- Бэкап в один файл sunstay_latest.dump с расписанием, скачиванием и восстановлением.
- Удержание брони (arrival_time, hold_minutes, hold_until) и автоотмена по истечении времени.
- Шахматка с цветными точками без имён гостей и компактный график загрузки за 7 дней.
- Тесты SQL и API, нагрузочный тест.

## Структура проекта

```
backend/            FastAPI core, тесты, CODE_SERVER.md
analytics/          FastAPI-микросервис отчётности
database/           SQL-миграции, тесты, CODE_DATABASE.md
frontend/           React SPA, Dockerfile, nginx.conf
docs/               ПЗ, схемы, скриншоты, результаты тестов
scripts/            backup/restore, load test, smoke test
docker-compose.yml
README.md
```

## Разработка

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Переменные окружения — в `.env.example`. Для шифрования контактов задайте `DATA_ENCRYPTION_KEY` (Fernet); без него API не сможет расшифровать существующие данные. Ключ не коммитится в Git.

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Vite проксирует `/api` на `http://localhost:8000`, `/analytics` на `http://localhost:8001`.

## Тесты

```powershell
# SQL-тесты (все изменения откатываются)
docker compose exec -T db psql -U postgres -d hotel -f /tmp/week5_tests.sql

# API-тесты
docker compose exec -e PYTHONPATH=/app -T -w /app api pytest -q /app/tests

# Нагрузочный тест
docker compose exec -T api python /tmp/load_test.py
```

Перед SQL/API-тестами скопируйте файлы в контейнеры:

```powershell
docker cp database/tests/week5_tests.sql sunstay_db:/tmp/week5_tests.sql
docker cp backend/tests sunstay_api:/app/tests
docker cp scripts/load_test.py sunstay_api:/tmp/load_test.py
```

## Резервное копирование

```powershell
.\scripts\backup.ps1
.\scripts\restore.ps1 -File sunstay_latest.dump
.\scripts\test_backup_restore.ps1
```

API также предоставляет администратору БД эндпоинты `/api/admin/backups`.

## Горячие клавиши

`?` — помощь, `N` — новая бронь, `F` — поиск, `G` — шахматка, `B` — бронирования, `R` — отчёты, `T` — тема, `L` — язык, `Esc` — закрыть, `Ctrl+Enter` — сохранить/отправить.

## Документация

- `docs/Пояснительная_записка_SunStay.docx` — пояснительная записка.
- `backend/CODE_SERVER.md` — полный текст серверного кода.
- `database/CODE_DATABASE.md` — полный текст SQL-скриптов.
- `docs/screenshots/` — скриншоты интерфейса.
- `docs/load_test_results.json` — результаты нагрузочного теста.
