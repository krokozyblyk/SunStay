-- SunStay: единый скрипт инициализации для Supabase/PostgreSQL.
-- Роли БД (005_db_roles.sql) намеренно пропущены: используется пользователь postgres.

-- ===== 000_extensions.sql =====
-- =====================================================================================
--  SunStay: расширения PostgreSQL
-- =====================================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- ===== 001_hotel_db.sql =====
-- =====================================================================================
--  БАЗА ДАННЫХ ГОСТИНИЦЫ «SunStay»  —  PostgreSQL
--  Курсовая работа, вариант «Отель»
--
--  Соответствует ERD: hotel_sunstay_erd.drawio (страница «Даталогическая модель»)
--  28 таблиц, сгруппированных по уровням зависимости (0 → 5), как и на диаграмме:
--    Уровень 0 — независимые справочники
--    Уровень 1 — таблицы, зависящие от справочников (users, rooms, rate_plans, services)
--    Уровень 2 — audit_log, room_amenities, bookings, housekeeping_tasks
--    Уровень 3 — check_ins/outs, additional_guests, service_orders, folios,
--                consumable_usage, maintenance_requests
--    Уровень 4 — folio_lines, payments
--    Уровень 5 — refunds
--
--  Имена таблиц/колонок из ERD (PascalCase) приведены к snake_case —
--  это стандартная конвенция PostgreSQL, позволяющая не квотировать идентификаторы.
--  Пример соответствия: RoomTypes -> room_types, AdditionalGuests -> additional_guests.
--
--  Состав скрипта:
--    1. Создание базы данных (выполнить один раз, отдельно)
--    2. (опционально) полная очистка схемы
--    3. Таблицы + ограничения целостности (PK, FK, CHECK, UNIQUE, NOT NULL, DEFAULT)
--    4. Индексы по внешним ключам
--    5. Тестовые (демонстрационные) данные
--    6. Пара представлений (VIEW) для удобства выборок
--    7. Проверочные запросы (закомментированы, для ручного запуска)
-- =====================================================================================


-- =====================================================================================
-- 1) СОЗДАНИЕ БАЗЫ ДАННЫХ
--    Выполняется один раз, отдельно от остального скрипта (CREATE DATABASE нельзя
--    выполнить внутри транзакции/скрипта, который уже подключён к другой базе).
--    В pgAdmin4: ПКМ на "Databases" -> Create -> Database... -> имя "hotel".
--    Либо в psql, подключившись к базе postgres:
-- =====================================================================================

-- CREATE DATABASE hotel
--     WITH ENCODING = 'UTF8'
--          LC_COLLATE = 'ru_RU.UTF-8'
--          LC_CTYPE   = 'ru_RU.UTF-8'
--          TEMPLATE   = template0;

-- После создания — подключитесь к базе hotel и выполните всё, что ниже.
-- В psql: \c hotel


-- =====================================================================================
-- 2) ПОЛНАЯ ОЧИСТКА СХЕМЫ (опционально, для повторного запуска "с нуля")
--    Раскомментируйте перед повторным запуском скрипта на уже заполненной базе.
-- =====================================================================================

-- DROP TABLE IF EXISTS
--     refunds, payments, folio_lines,
--     maintenance_requests, consumable_usage, folios, service_orders,
--     additional_guests, check_outs, check_ins,
--     housekeeping_tasks, bookings, room_amenities, audit_log,
--     services, rate_plans, rooms, users,
--     consumables, service_units, cancellation_reasons, guests,
--     promo_codes, amenities, block_reasons, room_statuses, room_types, roles
-- CASCADE;


BEGIN;

-- =====================================================================================
-- 3) ТАБЛИЦЫ И ОГРАНИЧЕНИЯ ЦЕЛОСТНОСТИ
-- =====================================================================================

CREATE TABLE roles (
    role_id     INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE
);
COMMENT ON TABLE roles IS 'Роли пользователей системы (справочник)';

CREATE TABLE room_types (
    room_type_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name         VARCHAR(100) NOT NULL UNIQUE,
    capacity     INTEGER NOT NULL CHECK (capacity > 0),
    description  TEXT
);
COMMENT ON TABLE room_types IS 'Типы (категории) номеров: Стандарт, Комфорт, Люкс и т.д.';

CREATE TABLE room_statuses (
    status_id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        VARCHAR(50) NOT NULL UNIQUE
);
COMMENT ON TABLE room_statuses IS 'Статусы номера: свободен/забронирован/заселён/грязный/в уборке/готов/блокирован';

CREATE TABLE block_reasons (
    reason_id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        VARCHAR(150) NOT NULL UNIQUE
);
COMMENT ON TABLE block_reasons IS 'Причины блокировки номера (ремонт, санобработка и т.п.)';

CREATE TABLE amenities (
    amenity_id  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE
);
COMMENT ON TABLE amenities IS 'Удобства/оснащение номера (справочник)';

CREATE TABLE guests (
    guest_id         INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    full_name        VARCHAR(200) NOT NULL,
    document_number  VARCHAR(50)  NOT NULL UNIQUE,
    phone            VARCHAR(30),
    email            VARCHAR(150),
    pdn_consent      BOOLEAN NOT NULL DEFAULT FALSE
);
COMMENT ON TABLE guests IS 'Гости — владельцы бронирований. document_number уникален: один гость = одна запись';
COMMENT ON COLUMN guests.pdn_consent IS 'Согласие на обработку персональных данных';

CREATE TABLE promo_codes (
    promo_id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code              VARCHAR(50) NOT NULL UNIQUE,
    discount_percent  INTEGER NOT NULL CHECK (discount_percent BETWEEN 1 AND 100),
    valid_from        DATE NOT NULL,
    valid_to          DATE NOT NULL,
    CHECK (valid_to >= valid_from)
);
COMMENT ON TABLE promo_codes IS 'Промокоды/скидки на бронирование';

CREATE TABLE cancellation_reasons (
    reason_id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        VARCHAR(150) NOT NULL UNIQUE
);
COMMENT ON TABLE cancellation_reasons IS 'Причины отмены бронирования (справочник)';

CREATE TABLE service_units (
    unit_id     INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        VARCHAR(50) NOT NULL UNIQUE
);
COMMENT ON TABLE service_units IS 'Единицы измерения доп. услуг (шт., час, порция и т.д.)';

CREATE TABLE consumables (
    consumable_id   INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name            VARCHAR(150) NOT NULL UNIQUE,
    unit            VARCHAR(30) NOT NULL,
    stock_quantity  NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0)
);
COMMENT ON TABLE consumables IS 'Расходные материалы хаускипинга (полотенца, шампунь и т.п.) и их остаток на складе';


-- --------------------------------- Уровень 1 -----------------------------------------

CREATE TABLE users (
    user_id         INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    role_id         INTEGER NOT NULL REFERENCES roles(role_id) ON DELETE RESTRICT,
    full_name       VARCHAR(200) NOT NULL,
    email           VARCHAR(150) NOT NULL UNIQUE,
    phone           VARCHAR(30),
    password_hash   VARCHAR(255) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT now()
);
COMMENT ON TABLE users IS 'Персонал/учётные записи системы (менеджер, хаускипинг, управляющий, администратор БД)';

CREATE TABLE rooms (
    room_id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    room_type_id     INTEGER NOT NULL REFERENCES room_types(room_type_id) ON DELETE RESTRICT,
    status_id        INTEGER NOT NULL REFERENCES room_statuses(status_id) ON DELETE RESTRICT,
    block_reason_id  INTEGER REFERENCES block_reasons(reason_id) ON DELETE SET NULL,
    room_number      VARCHAR(20) NOT NULL UNIQUE,
    floor            INTEGER NOT NULL CHECK (floor >= 0)
);
COMMENT ON TABLE rooms IS 'Номерной фонд гостиницы';

CREATE TABLE rate_plans (
    rate_id              INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    room_type_id         INTEGER NOT NULL REFERENCES room_types(room_type_id) ON DELETE RESTRICT,
    name                 VARCHAR(100) NOT NULL,
    season_start         DATE NOT NULL,
    season_end           DATE NOT NULL,
    price_per_night      NUMERIC(10,2) NOT NULL CHECK (price_per_night > 0),
    cancellation_terms   TEXT,
    CHECK (season_end >= season_start)
);
COMMENT ON TABLE rate_plans IS 'Тарифные планы по типам номеров и сезонам';

CREATE TABLE services (
    service_id  INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    unit_id     INTEGER NOT NULL REFERENCES service_units(unit_id) ON DELETE RESTRICT,
    name        VARCHAR(150) NOT NULL UNIQUE,
    price       NUMERIC(10,2) NOT NULL CHECK (price >= 0)
);
COMMENT ON TABLE services IS 'Дополнительные услуги гостиницы (завтрак, парковка, спа и т.д.)';


CREATE TABLE audit_log (
    log_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id      INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    table_name   VARCHAR(100) NOT NULL,
    record_id    INTEGER,
    action       VARCHAR(30) NOT NULL CHECK (action IN ('INSERT','UPDATE','DELETE')),
    old_value    TEXT,
    new_value    TEXT,
    changed_at   TIMESTAMP NOT NULL DEFAULT now(),
    ip_address   VARCHAR(50)
);
COMMENT ON TABLE audit_log IS 'Журнал аудита изменений (кто/что/когда изменил)';

CREATE TABLE room_amenities (
    id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    room_id     INTEGER NOT NULL REFERENCES rooms(room_id) ON DELETE CASCADE,
    amenity_id  INTEGER NOT NULL REFERENCES amenities(amenity_id) ON DELETE CASCADE,
    UNIQUE (room_id, amenity_id)
);
COMMENT ON TABLE room_amenities IS 'Связь "номер — удобство" (многие-ко-многим)';

CREATE TABLE bookings (
    booking_id               INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    guest_id                 INTEGER NOT NULL REFERENCES guests(guest_id) ON DELETE RESTRICT,
    room_id                  INTEGER NOT NULL REFERENCES rooms(room_id) ON DELETE RESTRICT,
    rate_id                  INTEGER NOT NULL REFERENCES rate_plans(rate_id) ON DELETE RESTRICT,
    promo_id                 INTEGER REFERENCES promo_codes(promo_id) ON DELETE SET NULL,
    cancellation_reason_id   INTEGER REFERENCES cancellation_reasons(reason_id) ON DELETE SET NULL,
    checkin_date             DATE NOT NULL,
    checkout_date            DATE NOT NULL,
    status                   VARCHAR(30) NOT NULL DEFAULT 'NEW'
                                 CHECK (status IN ('NEW','CONFIRMED','CHECKED_IN','CHECKED_OUT','CANCELLED','NO_SHOW')),
    source                   VARCHAR(30) NOT NULL DEFAULT 'SITE'
                                 CHECK (source IN ('SITE','PHONE','WALK_IN','OTA')),
    created_at               TIMESTAMP NOT NULL DEFAULT now(),
    CHECK (checkout_date > checkin_date)
);
COMMENT ON TABLE bookings IS 'Бронирования — центральная таблица предметной области';

CREATE TABLE housekeeping_tasks (
    task_id       INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    room_id       INTEGER NOT NULL REFERENCES rooms(room_id) ON DELETE CASCADE,
    staff_id      INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    task_type     VARCHAR(30) NOT NULL CHECK (task_type IN ('DAILY','POST_CHECKOUT','ON_REQUEST')),
    status        VARCHAR(30) NOT NULL DEFAULT 'ASSIGNED'
                     CHECK (status IN ('ASSIGNED','IN_PROGRESS','DONE','CANCELLED')),
    assigned_at   TIMESTAMP NOT NULL DEFAULT now(),
    completed_at  TIMESTAMP,
    CHECK (completed_at IS NULL OR completed_at >= assigned_at)
);
COMMENT ON TABLE housekeeping_tasks IS 'Задания на уборку/подготовку номеров';

CREATE TABLE check_ins (
    checkin_id              INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    booking_id               INTEGER NOT NULL REFERENCES bookings(booking_id) ON DELETE CASCADE,
    manager_id                INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    actual_checkin_at        TIMESTAMP NOT NULL DEFAULT now(),
    guest_document_number    VARCHAR(50) NOT NULL
);
COMMENT ON TABLE check_ins IS 'Факт заселения гостя по брони';

CREATE TABLE check_outs (
    checkout_id           INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    booking_id            INTEGER NOT NULL REFERENCES bookings(booking_id) ON DELETE CASCADE,
    manager_id            INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    actual_checkout_at    TIMESTAMP NOT NULL DEFAULT now()
);
COMMENT ON TABLE check_outs IS 'Факт выселения гостя по брони';

CREATE TABLE additional_guests (
    add_guest_id     INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    booking_id       INTEGER NOT NULL REFERENCES bookings(booking_id) ON DELETE CASCADE,
    full_name        VARCHAR(200) NOT NULL,
    document_number  VARCHAR(50)
);
COMMENT ON TABLE additional_guests IS 'Дополнительные гости, проживающие в номере по той же брони';

CREATE TABLE service_orders (
    order_id     INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    booking_id   INTEGER NOT NULL REFERENCES bookings(booking_id) ON DELETE CASCADE,
    service_id   INTEGER NOT NULL REFERENCES services(service_id) ON DELETE RESTRICT,
    user_id      INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    quantity     INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
    ordered_at   TIMESTAMP NOT NULL DEFAULT now()
);
COMMENT ON TABLE service_orders IS 'Заказы дополнительных услуг по броням';

CREATE TABLE folios (
    folio_id    INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    booking_id  INTEGER NOT NULL REFERENCES bookings(booking_id) ON DELETE CASCADE,
    opened_at   TIMESTAMP NOT NULL DEFAULT now(),
    closed_at   TIMESTAMP,
    status      VARCHAR(30) NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN','CLOSED')),
    CHECK (closed_at IS NULL OR closed_at >= opened_at)
);
COMMENT ON TABLE folios IS 'Лицевые счета (folio), открываются при заселении';

CREATE TABLE consumable_usage (
    usage_id        INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    task_id         INTEGER NOT NULL REFERENCES housekeeping_tasks(task_id) ON DELETE CASCADE,
    consumable_id   INTEGER NOT NULL REFERENCES consumables(consumable_id) ON DELETE RESTRICT,
    quantity        NUMERIC(10,2) NOT NULL CHECK (quantity > 0)
);
COMMENT ON TABLE consumable_usage IS 'Списание расходных материалов при выполнении задания на уборку';

CREATE TABLE maintenance_requests (
    request_id    INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    room_id       INTEGER NOT NULL REFERENCES rooms(room_id) ON DELETE CASCADE,
    task_id       INTEGER REFERENCES housekeeping_tasks(task_id) ON DELETE SET NULL,
    description   TEXT NOT NULL,
    status        VARCHAR(30) NOT NULL DEFAULT 'OPEN'
                     CHECK (status IN ('OPEN','IN_PROGRESS','DONE','CANCELLED')),
    created_at    TIMESTAMP NOT NULL DEFAULT now()
);
COMMENT ON TABLE maintenance_requests IS 'Заявки на техобслуживание/ремонт номера';

CREATE TABLE folio_lines (
    line_id       INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    folio_id      INTEGER NOT NULL REFERENCES folios(folio_id) ON DELETE CASCADE,
    description   VARCHAR(255) NOT NULL,
    amount        NUMERIC(10,2) NOT NULL,
    line_type     VARCHAR(30) NOT NULL CHECK (line_type IN ('ROOM','SERVICE','DISCOUNT','TAX','ADJUSTMENT')),
    created_at    TIMESTAMP NOT NULL DEFAULT now()
);
COMMENT ON TABLE folio_lines IS 'Строки начислений лицевого счёта (проживание, услуги, скидки, корректировки)';

CREATE TABLE payments (
    payment_id     INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    folio_id       INTEGER NOT NULL REFERENCES folios(folio_id) ON DELETE CASCADE,
    amount         NUMERIC(10,2) NOT NULL CHECK (amount > 0),
    method         VARCHAR(30) NOT NULL CHECK (method IN ('CARD','CASH','BANK_TRANSFER','ONLINE')),
    payment_type   VARCHAR(30) NOT NULL DEFAULT 'PAYMENT' CHECK (payment_type IN ('PAYMENT','DEPOSIT')),
    paid_at        TIMESTAMP NOT NULL DEFAULT now()
);
COMMENT ON TABLE payments IS 'Платежи и предоплаты по лицевым счетам';

CREATE TABLE refunds (
    refund_id     INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    payment_id    INTEGER NOT NULL REFERENCES payments(payment_id) ON DELETE CASCADE,
    amount        NUMERIC(10,2) NOT NULL CHECK (amount > 0),
    reason        VARCHAR(255) NOT NULL,
    refunded_at   TIMESTAMP NOT NULL DEFAULT now()
);
COMMENT ON TABLE refunds IS 'Возвраты денежных средств по платежам';


-- =====================================================================================
-- 4) ИНДЕКСЫ ПО ВНЕШНИМ КЛЮЧАМ
--    PostgreSQL не создаёт индексы на FK автоматически (в отличие от PK/UNIQUE) —
--    создаём их вручную для ускорения JOIN и проверок ON DELETE.
-- =====================================================================================

CREATE INDEX idx_users_role_id                    ON users(role_id);
CREATE INDEX idx_audit_log_user_id                 ON audit_log(user_id);
CREATE INDEX idx_rooms_room_type_id                ON rooms(room_type_id);
CREATE INDEX idx_rooms_status_id                   ON rooms(status_id);
CREATE INDEX idx_rooms_block_reason_id             ON rooms(block_reason_id);
CREATE INDEX idx_rate_plans_room_type_id           ON rate_plans(room_type_id);
CREATE INDEX idx_services_unit_id                  ON services(unit_id);
CREATE INDEX idx_bookings_guest_id                 ON bookings(guest_id);
CREATE INDEX idx_bookings_room_id                  ON bookings(room_id);
CREATE INDEX idx_bookings_rate_id                  ON bookings(rate_id);
CREATE INDEX idx_bookings_promo_id                 ON bookings(promo_id);
CREATE INDEX idx_bookings_cancellation_reason_id   ON bookings(cancellation_reason_id);
CREATE INDEX idx_bookings_status                   ON bookings(status);
CREATE INDEX idx_bookings_dates                    ON bookings(checkin_date, checkout_date);
CREATE INDEX idx_check_ins_booking_id              ON check_ins(booking_id);
CREATE INDEX idx_check_ins_manager_id              ON check_ins(manager_id);
CREATE INDEX idx_check_outs_booking_id             ON check_outs(booking_id);
CREATE INDEX idx_check_outs_manager_id             ON check_outs(manager_id);
CREATE INDEX idx_additional_guests_booking_id      ON additional_guests(booking_id);
CREATE INDEX idx_service_orders_booking_id         ON service_orders(booking_id);
CREATE INDEX idx_service_orders_service_id         ON service_orders(service_id);
CREATE INDEX idx_service_orders_user_id            ON service_orders(user_id);
CREATE INDEX idx_folios_booking_id                 ON folios(booking_id);
CREATE INDEX idx_folio_lines_folio_id              ON folio_lines(folio_id);
CREATE INDEX idx_payments_folio_id                 ON payments(folio_id);
CREATE INDEX idx_refunds_payment_id                ON refunds(payment_id);
CREATE INDEX idx_housekeeping_tasks_room_id        ON housekeeping_tasks(room_id);
CREATE INDEX idx_housekeeping_tasks_staff_id       ON housekeeping_tasks(staff_id);
CREATE INDEX idx_consumable_usage_task_id          ON consumable_usage(task_id);
CREATE INDEX idx_consumable_usage_consumable_id    ON consumable_usage(consumable_id);
CREATE INDEX idx_maintenance_requests_room_id      ON maintenance_requests(room_id);
CREATE INDEX idx_maintenance_requests_task_id      ON maintenance_requests(task_id);

COMMIT;


-- =====================================================================================
-- 5) ТЕСТОВЫЕ ДАННЫЕ
--    Вставка строго в порядке зависимостей (родители перед потомками).
--    ID генерируются автоматически (IDENTITY) начиная с 1 — скрипт рассчитан
--    на запуск на пустой базе (см. секцию 2, если нужно пересоздать).
-- =====================================================================================

BEGIN;

-- ---- roles (id 1..5) ----
INSERT INTO roles (name) VALUES
    ('Гость'),
    ('Менеджер'),
    ('Хаускипинг'),
    ('Управляющий отелем'),
    ('Администратор БД');

-- ---- room_types (id 1..3) ----
INSERT INTO room_types (name, capacity, description) VALUES
    ('Стандарт', 2, 'Стандартный номер с одной кроватью или двумя раздельными'),
    ('Комфорт',  2, 'Номер повышенной комфортности с видом на город'),
    ('Люкс',     4, 'Просторный номер с гостиной зоной, до 4 гостей');

-- ---- room_statuses (id 1..7) ----
INSERT INTO room_statuses (name) VALUES
    ('СВОБОДЕН'),
    ('ЗАБРОНИРОВАН'),
    ('ЗАСЕЛЁН'),
    ('ГРЯЗНЫЙ'),
    ('В_УБОРКЕ'),
    ('ЧИСТЫЙ_ГОТОВ'),
    ('БЛОКИРОВАН');

-- ---- block_reasons (id 1..3) ----
INSERT INTO block_reasons (name) VALUES
    ('Плановый ремонт'),
    ('Санитарная обработка'),
    ('Техническая неисправность');

-- ---- amenities (id 1..5) ----
INSERT INTO amenities (name) VALUES
    ('Wi-Fi'),
    ('Кондиционер'),
    ('Мини-бар'),
    ('Сейф'),
    ('Балкон');

-- ---- guests (id 1..4) ----
INSERT INTO guests (full_name, document_number, phone, email, pdn_consent) VALUES
    ('Иванов Иван Иванович',      '4510 123456', '+7 900 111-22-33', 'ivanov@example.com',  TRUE),
    ('Петрова Мария Сергеевна',   '4511 654321', '+7 900 222-33-44', 'petrova@example.com', TRUE),
    ('Сидоров Алексей Викторович','4512 789012', '+7 900 333-44-55', 'sidorov@example.com', TRUE),
    ('Кузнецова Ольга Дмитриевна','4513 345678', '+7 900 444-55-66', 'kuznetsova@example.com', TRUE);

-- ---- promo_codes (id 1..2) ----
INSERT INTO promo_codes (code, discount_percent, valid_from, valid_to) VALUES
    ('SUMMER10',  10, '2026-06-01', '2026-08-31'),
    ('WELCOME15', 15, '2026-01-01', '2026-12-31');

-- ---- cancellation_reasons (id 1..3) ----
INSERT INTO cancellation_reasons (name) VALUES
    ('Отмена по инициативе гостя'),
    ('Овербукинг'),
    ('Форс-мажор');

-- ---- service_units (id 1..3) ----
INSERT INTO service_units (name) VALUES
    ('шт.'),
    ('порция'),
    ('час');

-- ---- consumables (id 1..4) ----
INSERT INTO consumables (name, unit, stock_quantity) VALUES
    ('Полотенце банное',        'шт.', 120),
    ('Шампунь (флакон)',        'шт.', 80),
    ('Туалетная бумага',        'шт.', 200),
    ('Моющее средство (л)',     'л.',  15);

-- ---- users (id 1..5), пароли — демо-хэши (заглушка, не настоящий bcrypt) ----
INSERT INTO users (role_id, full_name, email, phone, password_hash) VALUES
    (1, 'Гостевой аккаунт (демо)',        'guest.demo@sunstay.example',   '+7 900 000-00-01', 'demo_hash_1'),
    (2, 'Смирнова Анна Павловна',         'smirnova@sunstay.example',     '+7 900 000-00-02', 'demo_hash_2'),
    (3, 'Фёдоров Дмитрий Олегович',       'fedorov@sunstay.example',      '+7 900 000-00-03', 'demo_hash_3'),
    (4, 'Волков Сергей Николаевич',       'volkov@sunstay.example',       '+7 900 000-00-04', 'demo_hash_4'),
    (5, 'Администратор БД',               'dba@sunstay.example',          '+7 900 000-00-05', 'demo_hash_5');

-- ---- rooms (id 1..6) ----
INSERT INTO rooms (room_type_id, status_id, block_reason_id, room_number, floor) VALUES
    (1, 1, NULL, '101', 1),
    (1, 3, NULL, '102', 1),
    (2, 6, NULL, '201', 2),
    (2, 2, NULL, '202', 2),
    (3, 1, NULL, '301', 3),
    (1, 7, 1,    '103', 1);   -- заблокирован на ремонт

-- ---- room_amenities (id 1..9) ----
INSERT INTO room_amenities (room_id, amenity_id) VALUES
    (1, 1), (1, 2),
    (2, 1), (2, 2), (2, 4),
    (3, 1), (3, 2), (3, 3),
    (5, 1), (5, 2), (5, 3), (5, 4), (5, 5);

-- ---- rate_plans (id 1..4) ----
INSERT INTO rate_plans (room_type_id, name, season_start, season_end, price_per_night, cancellation_terms) VALUES
    (1, 'Стандарт — низкий сезон', '2026-01-01', '2026-05-31', 3500.00, 'Бесплатная отмена за 24 часа'),
    (1, 'Стандарт — высокий сезон','2026-06-01', '2026-09-30', 4800.00, 'Отмена за 48 часов без штрафа'),
    (2, 'Комфорт — круглый год',   '2026-01-01', '2026-12-31', 5600.00, 'Отмена за 24 часа без штрафа'),
    (3, 'Люкс — круглый год',      '2026-01-01', '2026-12-31', 9200.00, 'Невозвратный тариф');

-- ---- services (id 1..4) ----
INSERT INTO services (unit_id, name, price) VALUES
    (2, 'Завтрак «шведский стол»', 800.00),
    (1, 'Парковка (сутки)',        400.00),
    (1, 'Трансфер аэропорт',       1500.00),
    (3, 'СПА-процедура (час)',     2500.00);

-- ---- bookings (id 1..4) ----
INSERT INTO bookings (guest_id, room_id, rate_id, promo_id, cancellation_reason_id,
                       checkin_date, checkout_date, status, source) VALUES
    (1, 2, 2, NULL, NULL,               '2026-07-01', '2026-07-05', 'CHECKED_OUT', 'SITE'),
    (2, 4, 3, 1,    NULL,               '2026-08-10', '2026-08-13', 'CHECKED_IN',  'SITE'),
    (3, 5, 4, NULL, NULL,               '2026-09-01', '2026-09-04', 'CONFIRMED',   'PHONE'),
    (4, 1, 1, NULL, 1,                  '2026-07-20', '2026-07-22', 'CANCELLED',   'SITE');

-- ---- check_ins (id 1..2) ----
INSERT INTO check_ins (booking_id, manager_id, actual_checkin_at, guest_document_number) VALUES
    (1, 2, '2026-07-01 14:20:00', '4510 123456'),
    (2, 2, '2026-08-10 15:05:00', '4511 654321');

-- ---- check_outs (id 1) ----
INSERT INTO check_outs (booking_id, manager_id, actual_checkout_at) VALUES
    (1, 2, '2026-07-05 11:40:00');

-- ---- additional_guests (id 1..2), к брони №2 подселён второй гость ----
INSERT INTO additional_guests (booking_id, full_name, document_number) VALUES
    (2, 'Петров Игорь Сергеевич', '4520 111222');

-- ---- service_orders (id 1..3) ----
INSERT INTO service_orders (booking_id, service_id, user_id, quantity) VALUES
    (1, 1, 2, 4),   -- завтраки на весь срок проживания
    (2, 2, 2, 1),   -- парковка
    (2, 1, 2, 2);   -- завтраки на 2 дня

-- ---- folios (id 1..2), открыты по заселённым/завершённым броням ----
INSERT INTO folios (booking_id, opened_at, closed_at, status) VALUES
    (1, '2026-07-01 14:20:00', '2026-07-05 11:40:00', 'CLOSED'),
    (2, '2026-08-10 15:05:00', NULL,                  'OPEN');

-- ---- folio_lines (id 1..6) ----
INSERT INTO folio_lines (folio_id, description, amount, line_type) VALUES
    (1, 'Проживание, номер 102, 4 ночи',            19200.00, 'ROOM'),
    (1, 'Завтрак «шведский стол» x4',                 3200.00, 'SERVICE'),
    (2, 'Проживание, номер 202, 3 ночи (текущий)',   16800.00, 'ROOM'),
    (2, 'Парковка (сутки)',                            400.00, 'SERVICE'),
    (2, 'Завтрак «шведский стол» x2',                 1600.00, 'SERVICE'),
    (2, 'Скидка по промокоду SUMMER10',              -1880.00, 'DISCOUNT');

-- ---- payments (id 1..3) ----
INSERT INTO payments (folio_id, amount, method, payment_type, paid_at) VALUES
    (1, 22400.00, 'CARD',   'PAYMENT', '2026-07-05 11:35:00'),
    (2, 10000.00, 'ONLINE', 'DEPOSIT', '2026-08-09 10:00:00'),
    (2,  5000.00, 'CARD',   'PAYMENT', '2026-08-10 15:10:00');

-- ---- refunds (id 1), частичный возврат по завышенному платежу ----
INSERT INTO refunds (payment_id, amount, reason) VALUES
    (1, 500.00, 'Перерасчёт стоимости завтраков — гость отказался от одного дня');

-- ---- housekeeping_tasks (id 1..4) ----
INSERT INTO housekeeping_tasks (room_id, staff_id, task_type, status, assigned_at, completed_at) VALUES
    (1, 3, 'DAILY',         'DONE',       '2026-07-02 09:00:00', '2026-07-02 09:40:00'),
    (2, 3, 'POST_CHECKOUT', 'DONE',       '2026-07-05 12:00:00', '2026-07-05 12:50:00'),
    (3, 3, 'ON_REQUEST',    'IN_PROGRESS','2026-09-15 10:00:00', NULL),
    (6, 3, 'ON_REQUEST',    'ASSIGNED',   '2026-09-16 08:00:00', NULL);

-- ---- consumable_usage (id 1..3) ----
INSERT INTO consumable_usage (task_id, consumable_id, quantity) VALUES
    (1, 1, 2),
    (1, 2, 1),
    (2, 1, 2);

-- ---- maintenance_requests (id 1..2) ----
INSERT INTO maintenance_requests (room_id, task_id, description, status) VALUES
    (6, NULL, 'Течь крана в ванной комнате',           'OPEN'),
    (3, 3,    'Не работает кондиционер',                'IN_PROGRESS');

-- ---- audit_log (id 1..3), пример записей ----
INSERT INTO audit_log (user_id, table_name, record_id, action, old_value, new_value, ip_address) VALUES
    (2, 'bookings', 1, 'UPDATE', 'status=NEW',       'status=CONFIRMED', '192.168.1.10'),
    (2, 'bookings', 2, 'UPDATE', 'status=CONFIRMED', 'status=CHECKED_IN','192.168.1.10'),
    (5, 'users',    3, 'INSERT', NULL,                'full_name=Фёдоров Дмитрий Олегович', '192.168.1.5');

COMMIT;


-- =====================================================================================
-- 6) ПРЕДСТАВЛЕНИЯ (VIEW) — для удобства выборок и отчётов
-- =====================================================================================

CREATE OR REPLACE VIEW v_rooms_status AS
SELECT
    r.room_id,
    r.room_number,
    rt.name           AS room_type,
    rt.capacity,
    rs.name           AS status,
    br.name           AS block_reason,
    r.floor
FROM rooms r
JOIN room_types    rt ON rt.room_type_id = r.room_type_id
JOIN room_statuses rs ON rs.status_id    = r.status_id
LEFT JOIN block_reasons br ON br.reason_id = r.block_reason_id;
COMMENT ON VIEW v_rooms_status IS 'Текущий номерной фонд с расшифровкой типа/статуса/причины блокировки';

CREATE OR REPLACE VIEW v_booking_summary AS
SELECT
    b.booking_id,
    g.full_name         AS guest_name,
    r.room_number,
    rt.name              AS room_type,
    b.checkin_date,
    b.checkout_date,
    b.status,
    b.source,
    rp.price_per_night,
    pc.code              AS promo_code
FROM bookings b
JOIN guests      g  ON g.guest_id  = b.guest_id
JOIN rooms       r  ON r.room_id   = b.room_id
JOIN room_types  rt ON rt.room_type_id = r.room_type_id
JOIN rate_plans  rp ON rp.rate_id  = b.rate_id
LEFT JOIN promo_codes pc ON pc.promo_id = b.promo_id;
COMMENT ON VIEW v_booking_summary IS 'Сводка по бронированиям с расшифровкой гостя/номера/тарифа/промокода';

CREATE OR REPLACE VIEW v_folio_balance AS
SELECT
    f.folio_id,
    f.booking_id,
    f.status,
    COALESCE(SUM(fl.amount), 0)                                   AS charged_total,
    COALESCE((SELECT SUM(p.amount) FROM payments p
              WHERE p.folio_id = f.folio_id), 0)
      - COALESCE((SELECT SUM(rf.amount) FROM refunds rf
                  JOIN payments p2 ON p2.payment_id = rf.payment_id
                  WHERE p2.folio_id = f.folio_id), 0)              AS paid_total
FROM folios f
LEFT JOIN folio_lines fl ON fl.folio_id = f.folio_id
GROUP BY f.folio_id, f.booking_id, f.status;
COMMENT ON VIEW v_folio_balance IS 'Баланс по лицевому счёту: начислено / оплачено (с учётом возвратов)';


-- =====================================================================================
-- 7) ПРОВЕРОЧНЫЕ ЗАПРОСЫ (для ручного запуска, не выполняются автоматически)
-- =====================================================================================

-- Все таблицы и число строк:
-- SELECT relname AS table_name, n_live_tup AS row_count
-- FROM pg_stat_user_tables ORDER BY relname;

-- Текущая загрузка номерного фонда:
-- SELECT * FROM v_rooms_status ORDER BY room_number;

-- Активные и завершённые брони с балансом по счёту:
-- SELECT bs.*, fb.charged_total, fb.paid_total
-- FROM v_booking_summary bs
-- JOIN folios f ON f.booking_id = bs.booking_id
-- JOIN v_folio_balance fb ON fb.folio_id = f.folio_id
-- ORDER BY bs.checkin_date;

-- Проверка ограничения целостности (должно упасть с ошибкой CHECK):
-- INSERT INTO bookings (guest_id, room_id, rate_id, checkin_date, checkout_date)
-- VALUES (1, 1, 1, '2026-10-10', '2026-10-05');  -- checkout раньше checkin -> ошибка

-- Проверка запрета удаления справочника, если он используется (RESTRICT):
-- DELETE FROM room_types WHERE room_type_id = 1;  -- есть номера этого типа -> ошибка

-- ===== 002_week5.sql =====
-- =====================================================================================
--  SunStay: неделя 5 — расширенная серверная логика
--  Ограничения, функции, процедуры, триггеры, транзакционные операции.
-- =====================================================================================

BEGIN;

-- -------------------------------------------------------------------------------------
-- 1. Дополнительные поля и ограничения
-- -------------------------------------------------------------------------------------

ALTER TABLE bookings
    ADD COLUMN adults   INTEGER NOT NULL DEFAULT 1 CHECK (adults > 0),
    ADD COLUMN children INTEGER NOT NULL DEFAULT 0 CHECK (children >= 0);

ALTER TABLE check_ins
    ADD CONSTRAINT check_ins_booking_unique UNIQUE (booking_id);

ALTER TABLE check_outs
    ADD CONSTRAINT check_outs_booking_unique UNIQUE (booking_id);

ALTER TABLE folios
    ADD CONSTRAINT folios_booking_unique UNIQUE (booking_id);

ALTER TABLE folio_lines
    ADD COLUMN charge_date DATE,
    ADD COLUMN service_order_id INTEGER REFERENCES service_orders(order_id) ON DELETE SET NULL;

UPDATE folio_lines fl
SET charge_date = f.opened_at::date
FROM folios f
WHERE fl.folio_id = f.folio_id
  AND fl.line_type = 'ROOM'
  AND fl.charge_date IS NULL;

UPDATE folio_lines
SET charge_date = created_at::date
WHERE charge_date IS NULL;

CREATE UNIQUE INDEX uq_folio_room_charge
    ON folio_lines (folio_id, charge_date)
    WHERE line_type = 'ROOM' AND charge_date IS NOT NULL;

CREATE UNIQUE INDEX uq_folio_service_order
    ON folio_lines (service_order_id)
    WHERE service_order_id IS NOT NULL;

ALTER TABLE consumables
    ADD COLUMN min_stock NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (min_stock >= 0);

ALTER TABLE maintenance_requests
    ADD COLUMN priority VARCHAR(10) NOT NULL DEFAULT 'NORMAL'
        CHECK (priority IN ('LOW','NORMAL','HIGH','URGENT')),
    ADD COLUMN assigned_to INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT now();

ALTER TABLE housekeeping_tasks
    ADD COLUMN priority VARCHAR(10) NOT NULL DEFAULT 'NORMAL'
        CHECK (priority IN ('LOW','NORMAL','HIGH','URGENT'));

ALTER TABLE guests
    ADD COLUMN user_id INTEGER UNIQUE REFERENCES users(user_id) ON DELETE SET NULL;

UPDATE guests SET user_id = 1 WHERE guest_id = 1;

ALTER TABLE payments
    ADD COLUMN external_ref VARCHAR(100);

CREATE UNIQUE INDEX uq_payments_external_ref
    ON payments (external_ref)
    WHERE external_ref IS NOT NULL;

ALTER TABLE audit_log
    ADD COLUMN user_agent VARCHAR(255),
    ADD COLUMN request_id VARCHAR(100);

ALTER TABLE bookings
    ADD CONSTRAINT bookings_no_overlap
    EXCLUDE USING gist (
        room_id WITH =,
        daterange(checkin_date, checkout_date, '[)') WITH &&
    )
    WHERE (status IN ('NEW','CONFIRMED','CHECKED_IN'));

CREATE TABLE business_days (
    business_date DATE PRIMARY KEY,
    closed_at     TIMESTAMP NOT NULL DEFAULT now(),
    closed_by     INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    totals        JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE system_settings (
    key         VARCHAR(100) PRIMARY KEY,
    value       JSONB NOT NULL,
    updated_at  TIMESTAMP NOT NULL DEFAULT now(),
    updated_by  INTEGER REFERENCES users(user_id) ON DELETE SET NULL
);

CREATE TABLE import_batches (
    import_id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    import_type   VARCHAR(30) NOT NULL CHECK (import_type IN ('BANK_STATEMENT','RATES')),
    filename      VARCHAR(255),
    status        VARCHAR(20) NOT NULL DEFAULT 'PREVIEW'
        CHECK (status IN ('PREVIEW','COMMITTED','FAILED')),
    total_rows    INTEGER NOT NULL DEFAULT 0,
    success_rows  INTEGER NOT NULL DEFAULT 0,
    error_rows    INTEGER NOT NULL DEFAULT 0,
    errors        JSONB,
    created_by    INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    created_at    TIMESTAMP NOT NULL DEFAULT now(),
    committed_at  TIMESTAMP
);

INSERT INTO system_settings (key, value) VALUES
    ('hotel.name',       '"SunStay"'::jsonb),
    ('hotel.address',    '"Санкт-Петербург, набережная реки Мойки, 12"'::jsonb),
    ('hotel.phone',      '"+7 (812) 490-70-00"'::jsonb),
    ('hotel.email',      '"welcome@sunstay-hotel.ru"'::jsonb),
    ('app.default_theme','"light"'::jsonb),
    ('app.default_language','"ru"'::jsonb)
ON CONFLICT (key) DO NOTHING;

COMMIT;

-- -------------------------------------------------------------------------------------
-- 2. Функции проверки и расчёта
-- -------------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION fn_room_available(
    p_room_id INTEGER,
    p_checkin DATE,
    p_checkout DATE,
    p_exclude_booking_id INTEGER DEFAULT NULL
) RETURNS BOOLEAN
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_available BOOLEAN;
BEGIN
    IF p_checkin IS NULL OR p_checkout IS NULL OR p_checkout <= p_checkin THEN
        RETURN FALSE;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM rooms r
        JOIN room_statuses rs ON rs.status_id = r.status_id
        WHERE r.room_id = p_room_id
          AND rs.name <> 'БЛОКИРОВАН'
    ) THEN
        RETURN FALSE;
    END IF;

    SELECT NOT EXISTS (
        SELECT 1
        FROM bookings b
        WHERE b.room_id = p_room_id
          AND b.status IN ('NEW','CONFIRMED','CHECKED_IN')
          AND daterange(b.checkin_date, b.checkout_date, '[)')
              && daterange(p_checkin, p_checkout, '[)')
          AND (p_exclude_booking_id IS NULL OR b.booking_id <> p_exclude_booking_id)
    ) INTO v_available;

    RETURN v_available;
END;
$$;

CREATE OR REPLACE FUNCTION fn_calculate_stay_price(
    p_rate_id INTEGER,
    p_checkin DATE,
    p_checkout DATE,
    p_promo_id INTEGER DEFAULT NULL
) RETURNS NUMERIC
LANGUAGE plpgsql
STABLE
AS $$
DECLARE
    v_price NUMERIC(10,2);
    v_nights INTEGER;
    v_discount INTEGER;
    v_total NUMERIC(12,2);
BEGIN
    v_nights := p_checkout - p_checkin;
    IF v_nights <= 0 THEN
        RAISE EXCEPTION 'Дата выезда должна быть позже даты заезда';
    END IF;

    SELECT price_per_night INTO v_price
    FROM rate_plans
    WHERE rate_id = p_rate_id;

    IF v_price IS NULL THEN
        RAISE EXCEPTION 'Тариф % не найден', p_rate_id;
    END IF;

    v_total := v_price * v_nights;

    IF p_promo_id IS NOT NULL THEN
        SELECT discount_percent INTO v_discount
        FROM promo_codes
        WHERE promo_id = p_promo_id
          AND p_checkin BETWEEN valid_from AND valid_to;

        IF v_discount IS NOT NULL THEN
            v_total := v_total * (1 - v_discount / 100.0);
        END IF;
    END IF;

    RETURN ROUND(v_total, 2);
END;
$$;

CREATE OR REPLACE FUNCTION fn_folio_charged(p_folio_id INTEGER) RETURNS NUMERIC
LANGUAGE sql STABLE AS $$
    SELECT COALESCE(SUM(amount), 0)
    FROM folio_lines
    WHERE folio_id = p_folio_id;
$$;

CREATE OR REPLACE FUNCTION fn_folio_paid(p_folio_id INTEGER) RETURNS NUMERIC
LANGUAGE sql STABLE AS $$
    SELECT COALESCE((
        SELECT SUM(p.amount) FROM payments p WHERE p.folio_id = p_folio_id
    ), 0) - COALESCE((
        SELECT SUM(rf.amount)
        FROM refunds rf
        JOIN payments p2 ON p2.payment_id = rf.payment_id
        WHERE p2.folio_id = p_folio_id
    ), 0);
$$;

CREATE OR REPLACE FUNCTION fn_folio_balance(p_folio_id INTEGER) RETURNS NUMERIC
LANGUAGE sql STABLE AS $$
    SELECT fn_folio_charged(p_folio_id) - fn_folio_paid(p_folio_id);
$$;

CREATE OR REPLACE FUNCTION fn_booking_balance(p_booking_id INTEGER) RETURNS NUMERIC
LANGUAGE sql STABLE AS $$
    SELECT COALESCE(fn_folio_balance(f.folio_id), 0)
    FROM folios f
    WHERE f.booking_id = p_booking_id
    ORDER BY f.folio_id DESC
    LIMIT 1;
$$;

-- -------------------------------------------------------------------------------------
-- 3. Триггеры валидации, аудита и защиты
-- -------------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION fn_validate_booking() RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_room_type INTEGER;
    v_capacity INTEGER;
    v_rate_type INTEGER;
BEGIN
    IF NEW.checkout_date <= NEW.checkin_date THEN
        RAISE EXCEPTION 'Дата выезда должна быть позже даты заезда';
    END IF;

    SELECT rt.room_type_id, rt.capacity
    INTO v_room_type, v_capacity
    FROM rooms r
    JOIN room_types rt ON rt.room_type_id = r.room_type_id
    WHERE r.room_id = NEW.room_id;

    IF v_room_type IS NULL OR v_capacity IS NULL THEN
        RAISE EXCEPTION 'Номер % не найден', NEW.room_id;
    END IF;

    SELECT room_type_id INTO v_rate_type
    FROM rate_plans
    WHERE rate_id = NEW.rate_id;

    IF v_rate_type IS NULL OR v_rate_type <> v_room_type THEN
        RAISE EXCEPTION 'Тариф не соответствует типу номера';
    END IF;

    IF NEW.adults + NEW.children > v_capacity THEN
        RAISE EXCEPTION 'Количество гостей превышает вместимость номера';
    END IF;

    IF NEW.status IN ('NEW','CONFIRMED','CHECKED_IN') THEN
        IF NOT EXISTS (
            SELECT 1
            FROM rate_plans rp
            WHERE rp.rate_id = NEW.rate_id
              AND NEW.checkin_date >= rp.season_start
              AND NEW.checkout_date - 1 <= rp.season_end
        ) THEN
            RAISE EXCEPTION 'Тариф не действует на выбранные даты';
        END IF;
    END IF;

    IF NEW.promo_id IS NOT NULL THEN
        IF NOT EXISTS (
            SELECT 1
            FROM promo_codes pc
            WHERE pc.promo_id = NEW.promo_id
              AND NEW.checkin_date BETWEEN pc.valid_from AND pc.valid_to
        ) THEN
            RAISE EXCEPTION 'Промокод не действует на выбранные даты';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validate_booking
BEFORE INSERT OR UPDATE ON bookings
FOR EACH ROW EXECUTE FUNCTION fn_validate_booking();

CREATE OR REPLACE FUNCTION fn_audit_row() RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_user_id INTEGER;
    v_ip VARCHAR(50);
    v_ua VARCHAR(255);
    v_request_id VARCHAR(100);
    v_record_id INTEGER;
    v_old TEXT;
    v_new TEXT;
BEGIN
    v_user_id := NULLIF(current_setting('app.current_user_id', true), '')::INTEGER;
    v_ip := NULLIF(current_setting('app.client_ip', true), '');
    v_ua := NULLIF(current_setting('app.user_agent', true), '');
    v_request_id := NULLIF(current_setting('app.request_id', true), '');

    IF TG_OP = 'DELETE' THEN
        v_record_id := (to_jsonb(OLD) ->> TG_ARGV[0])::INTEGER;
        v_old := to_jsonb(OLD)::TEXT;
        v_new := NULL;
    ELSIF TG_OP = 'UPDATE' THEN
        v_record_id := (to_jsonb(NEW) ->> TG_ARGV[0])::INTEGER;
        v_old := to_jsonb(OLD)::TEXT;
        v_new := to_jsonb(NEW)::TEXT;
    ELSE
        v_record_id := (to_jsonb(NEW) ->> TG_ARGV[0])::INTEGER;
        v_old := NULL;
        v_new := to_jsonb(NEW)::TEXT;
    END IF;

    INSERT INTO audit_log (
        user_id, table_name, record_id, action,
        old_value, new_value, ip_address, user_agent, request_id
    ) VALUES (
        v_user_id, TG_TABLE_NAME, v_record_id, TG_OP,
        v_old, v_new, v_ip, v_ua, v_request_id
    );

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_audit_bookings
AFTER INSERT OR UPDATE OR DELETE ON bookings
FOR EACH ROW EXECUTE FUNCTION fn_audit_row('booking_id');

CREATE TRIGGER trg_audit_rooms
AFTER INSERT OR UPDATE OR DELETE ON rooms
FOR EACH ROW EXECUTE FUNCTION fn_audit_row('room_id');

CREATE TRIGGER trg_audit_users
AFTER INSERT OR UPDATE OR DELETE ON users
FOR EACH ROW EXECUTE FUNCTION fn_audit_row('user_id');

CREATE TRIGGER trg_audit_folios
AFTER INSERT OR UPDATE OR DELETE ON folios
FOR EACH ROW EXECUTE FUNCTION fn_audit_row('folio_id');

CREATE TRIGGER trg_audit_payments
AFTER INSERT OR UPDATE OR DELETE ON payments
FOR EACH ROW EXECUTE FUNCTION fn_audit_row('payment_id');

CREATE TRIGGER trg_audit_refunds
AFTER INSERT OR UPDATE OR DELETE ON refunds
FOR EACH ROW EXECUTE FUNCTION fn_audit_row('refund_id');

CREATE TRIGGER trg_audit_rate_plans
AFTER INSERT OR UPDATE OR DELETE ON rate_plans
FOR EACH ROW EXECUTE FUNCTION fn_audit_row('rate_id');

CREATE TRIGGER trg_audit_services
AFTER INSERT OR UPDATE OR DELETE ON services
FOR EACH ROW EXECUTE FUNCTION fn_audit_row('service_id');

CREATE TRIGGER trg_audit_guests
AFTER INSERT OR UPDATE OR DELETE ON guests
FOR EACH ROW EXECUTE FUNCTION fn_audit_row('guest_id');

CREATE TRIGGER trg_audit_housekeeping
AFTER INSERT OR UPDATE OR DELETE ON housekeeping_tasks
FOR EACH ROW EXECUTE FUNCTION fn_audit_row('task_id');

CREATE TRIGGER trg_audit_maintenance
AFTER INSERT OR UPDATE OR DELETE ON maintenance_requests
FOR EACH ROW EXECUTE FUNCTION fn_audit_row('request_id');

CREATE TRIGGER trg_audit_consumables
AFTER INSERT OR UPDATE OR DELETE ON consumables
FOR EACH ROW EXECUTE FUNCTION fn_audit_row('consumable_id');

CREATE OR REPLACE FUNCTION fn_consumable_stock() RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE consumables
        SET stock_quantity = stock_quantity - NEW.quantity
        WHERE consumable_id = NEW.consumable_id
          AND stock_quantity >= NEW.quantity;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'Недостаточно расходного материала %', NEW.consumable_id;
        END IF;
        RETURN NEW;

    ELSIF TG_OP = 'UPDATE' THEN
        UPDATE consumables
        SET stock_quantity = stock_quantity + OLD.quantity
        WHERE consumable_id = OLD.consumable_id;

        UPDATE consumables
        SET stock_quantity = stock_quantity - NEW.quantity
        WHERE consumable_id = NEW.consumable_id
          AND stock_quantity >= NEW.quantity;

        IF NOT FOUND THEN
            RAISE EXCEPTION 'Недостаточно расходного материала %', NEW.consumable_id;
        END IF;
        RETURN NEW;

    ELSIF TG_OP = 'DELETE' THEN
        UPDATE consumables
        SET stock_quantity = stock_quantity + OLD.quantity
        WHERE consumable_id = OLD.consumable_id;
        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$;

CREATE TRIGGER trg_consumable_stock
BEFORE INSERT OR UPDATE OR DELETE ON consumable_usage
FOR EACH ROW EXECUTE FUNCTION fn_consumable_stock();

CREATE OR REPLACE FUNCTION fn_prevent_closed_day() RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_date DATE;
BEGIN
    IF current_setting('app.bypass_closed_day', true) = 'on' THEN
        IF TG_OP = 'DELETE' THEN
            RETURN OLD;
        END IF;
        RETURN NEW;
    END IF;

    IF TG_OP = 'DELETE' THEN
        IF TG_TABLE_NAME = 'folio_lines' THEN
            v_date := COALESCE(OLD.charge_date, OLD.created_at::date);
        ELSIF TG_TABLE_NAME = 'payments' THEN
            v_date := OLD.paid_at::date;
        ELSIF TG_TABLE_NAME = 'refunds' THEN
            v_date := OLD.refunded_at::date;
        END IF;
    ELSE
        IF TG_TABLE_NAME = 'folio_lines' THEN
            v_date := COALESCE(NEW.charge_date, NEW.created_at::date);
        ELSIF TG_TABLE_NAME = 'payments' THEN
            v_date := NEW.paid_at::date;
        ELSIF TG_TABLE_NAME = 'refunds' THEN
            v_date := NEW.refunded_at::date;
        END IF;
    END IF;

    IF v_date IS NOT NULL AND EXISTS (
        SELECT 1 FROM business_days
        WHERE business_date = v_date AND closed_at IS NOT NULL
    ) THEN
        RAISE EXCEPTION 'Бизнес-день % закрыт. Изменения запрещены', v_date;
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_prevent_closed_day_folio_lines
BEFORE INSERT OR UPDATE OR DELETE ON folio_lines
FOR EACH ROW EXECUTE FUNCTION fn_prevent_closed_day();

CREATE TRIGGER trg_prevent_closed_day_payments
BEFORE INSERT OR UPDATE OR DELETE ON payments
FOR EACH ROW EXECUTE FUNCTION fn_prevent_closed_day();

CREATE TRIGGER trg_prevent_closed_day_refunds
BEFORE INSERT OR UPDATE OR DELETE ON refunds
FOR EACH ROW EXECUTE FUNCTION fn_prevent_closed_day();

CREATE OR REPLACE FUNCTION fn_set_updated_at() RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_maintenance_updated_at
BEFORE UPDATE ON maintenance_requests
FOR EACH ROW EXECUTE FUNCTION fn_set_updated_at();

-- -------------------------------------------------------------------------------------
-- 4. Транзакционные серверные операции
-- -------------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION fn_create_booking(
    p_guest_id INTEGER,
    p_room_id INTEGER,
    p_rate_id INTEGER,
    p_checkin DATE,
    p_checkout DATE,
    p_promo_id INTEGER,
    p_source VARCHAR,
    p_adults INTEGER,
    p_children INTEGER,
    p_user_id INTEGER,
    p_ip VARCHAR
) RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_booking_id INTEGER;
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    IF NOT fn_room_available(p_room_id, p_checkin, p_checkout) THEN
        RAISE EXCEPTION 'Номер недоступен на выбранные даты';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM guests WHERE guest_id = p_guest_id AND pdn_consent = TRUE
    ) THEN
        RAISE EXCEPTION 'Нет согласия гостя на обработку персональных данных';
    END IF;

    INSERT INTO bookings (
        guest_id, room_id, rate_id, promo_id,
        checkin_date, checkout_date, status, source,
        adults, children
    ) VALUES (
        p_guest_id, p_room_id, p_rate_id, p_promo_id,
        p_checkin, p_checkout, 'NEW', COALESCE(p_source, 'SITE'),
        COALESCE(p_adults, 1), COALESCE(p_children, 0)
    )
    RETURNING booking_id INTO v_booking_id;

    RETURN v_booking_id;
EXCEPTION
    WHEN exclusion_violation THEN
        RAISE EXCEPTION 'Номер уже забронирован на выбранные даты';
END;
$$;

CREATE OR REPLACE PROCEDURE sp_confirm_booking(
    p_booking_id INTEGER,
    p_user_id INTEGER,
    p_ip VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    UPDATE bookings
    SET status = 'CONFIRMED'
    WHERE booking_id = p_booking_id
      AND status = 'NEW';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Бронь % нельзя подтвердить: неверный статус', p_booking_id;
    END IF;
END;
$$;

CREATE OR REPLACE PROCEDURE sp_cancel_booking(
    p_booking_id INTEGER,
    p_reason_id INTEGER,
    p_user_id INTEGER,
    p_ip VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    UPDATE bookings
    SET status = 'CANCELLED',
        cancellation_reason_id = p_reason_id
    WHERE booking_id = p_booking_id
      AND status IN ('NEW','CONFIRMED');

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Бронь % нельзя отменить: неверный статус', p_booking_id;
    END IF;
END;
$$;

CREATE OR REPLACE PROCEDURE sp_check_in(
    p_booking_id INTEGER,
    p_manager_id INTEGER,
    p_document_number VARCHAR,
    p_deposit_amount NUMERIC,
    p_payment_method VARCHAR,
    p_ip VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_room_id INTEGER;
    v_folio_id INTEGER;
    v_status_id INTEGER;
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_manager_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    SELECT room_id INTO v_room_id
    FROM bookings
    WHERE booking_id = p_booking_id
      AND status = 'CONFIRMED';

    IF v_room_id IS NULL THEN
        RAISE EXCEPTION 'Заселение возможно только для подтверждённой брони';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM rooms r
        JOIN room_statuses rs ON rs.status_id = r.status_id
        WHERE r.room_id = v_room_id AND rs.name = 'БЛОКИРОВАН'
    ) THEN
        RAISE EXCEPTION 'Номер заблокирован';
    END IF;

    INSERT INTO check_ins (booking_id, manager_id, guest_document_number)
    VALUES (p_booking_id, p_manager_id, p_document_number);

    UPDATE bookings SET status = 'CHECKED_IN' WHERE booking_id = p_booking_id;

    SELECT status_id INTO v_status_id FROM room_statuses WHERE name = 'ЗАСЕЛЁН';
    UPDATE rooms SET status_id = v_status_id WHERE room_id = v_room_id;

    INSERT INTO folios (booking_id, status)
    VALUES (p_booking_id, 'OPEN')
    ON CONFLICT (booking_id) DO NOTHING;

    SELECT folio_id INTO v_folio_id
    FROM folios
    WHERE booking_id = p_booking_id
    ORDER BY folio_id DESC
    LIMIT 1;

    IF COALESCE(p_deposit_amount, 0) > 0 THEN
        INSERT INTO payments (folio_id, amount, method, payment_type)
        VALUES (v_folio_id, p_deposit_amount, COALESCE(p_payment_method, 'CARD'), 'DEPOSIT');
    END IF;
END;
$$;

CREATE OR REPLACE PROCEDURE sp_check_out(
    p_booking_id INTEGER,
    p_manager_id INTEGER,
    p_payment_amount NUMERIC,
    p_payment_method VARCHAR,
    p_ip VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_room_id INTEGER;
    v_folio_id INTEGER;
    v_status_id INTEGER;
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_manager_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    SELECT room_id INTO v_room_id
    FROM bookings
    WHERE booking_id = p_booking_id
      AND status = 'CHECKED_IN';

    IF v_room_id IS NULL THEN
        RAISE EXCEPTION 'Выселение возможно только для заселённой брони';
    END IF;

    SELECT folio_id INTO v_folio_id
    FROM folios
    WHERE booking_id = p_booking_id AND status = 'OPEN'
    ORDER BY folio_id DESC
    LIMIT 1;

    IF v_folio_id IS NULL THEN
        RAISE EXCEPTION 'Открытый folio не найден';
    END IF;

    IF COALESCE(p_payment_amount, 0) > 0 THEN
        INSERT INTO payments (folio_id, amount, method, payment_type)
        VALUES (v_folio_id, p_payment_amount, COALESCE(p_payment_method, 'CARD'), 'PAYMENT');
    END IF;

    UPDATE folios
    SET status = 'CLOSED', closed_at = now()
    WHERE folio_id = v_folio_id;

    UPDATE bookings
    SET status = 'CHECKED_OUT'
    WHERE booking_id = p_booking_id;

    SELECT status_id INTO v_status_id FROM room_statuses WHERE name = 'ГРЯЗНЫЙ';
    UPDATE rooms SET status_id = v_status_id WHERE room_id = v_room_id;

    INSERT INTO housekeeping_tasks (room_id, staff_id, task_type, status, priority)
    VALUES (v_room_id, NULL, 'POST_CHECKOUT', 'ASSIGNED', 'HIGH');
END;
$$;

CREATE OR REPLACE PROCEDURE sp_night_audit(
    p_business_date DATE,
    p_user_id INTEGER,
    p_ip VARCHAR,
    OUT p_posted_count INTEGER,
    OUT p_no_show_count INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    r RECORD;
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    IF EXISTS (SELECT 1 FROM business_days WHERE business_date = p_business_date) THEN
        RAISE EXCEPTION 'Бизнес-день % уже закрыт', p_business_date;
    END IF;

    p_posted_count := 0;

    FOR r IN
        SELECT b.booking_id, f.folio_id, rp.price_per_night
        FROM bookings b
        JOIN folios f ON f.booking_id = b.booking_id AND f.status = 'OPEN'
        JOIN rate_plans rp ON rp.rate_id = b.rate_id
        WHERE b.status = 'CHECKED_IN'
          AND p_business_date >= b.checkin_date
          AND p_business_date < b.checkout_date
    LOOP
        IF NOT EXISTS (
            SELECT 1
            FROM folio_lines fl
            WHERE fl.folio_id = r.folio_id
              AND fl.line_type = 'ROOM'
              AND fl.charge_date = p_business_date
        ) THEN
            INSERT INTO folio_lines (folio_id, description, amount, line_type, charge_date)
            VALUES (
                r.folio_id,
                'Проживание за ' || to_char(p_business_date, 'DD.MM.YYYY'),
                r.price_per_night,
                'ROOM',
                p_business_date
            );
            p_posted_count := p_posted_count + 1;
        END IF;
    END LOOP;

    UPDATE bookings
    SET status = 'NO_SHOW'
    WHERE status = 'CONFIRMED'
      AND checkin_date = p_business_date;

    GET DIAGNOSTICS p_no_show_count = ROW_COUNT;

    INSERT INTO business_days (business_date, closed_by, totals)
    VALUES (
        p_business_date,
        p_user_id,
        jsonb_build_object(
            'posted_count', p_posted_count,
            'no_show_count', p_no_show_count
        )
    );
END;
$$;

CREATE OR REPLACE FUNCTION fn_add_service_order(
    p_booking_id INTEGER,
    p_service_id INTEGER,
    p_quantity INTEGER,
    p_user_id INTEGER,
    p_ip VARCHAR
) RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_order_id INTEGER;
    v_folio_id INTEGER;
    v_price NUMERIC(10,2);
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    SELECT folio_id INTO v_folio_id
    FROM folios
    WHERE booking_id = p_booking_id AND status = 'OPEN'
    ORDER BY folio_id DESC
    LIMIT 1;

    IF v_folio_id IS NULL THEN
        RAISE EXCEPTION 'Открытый folio не найден';
    END IF;

    SELECT price INTO v_price FROM services WHERE service_id = p_service_id;

    INSERT INTO service_orders (booking_id, service_id, user_id, quantity)
    VALUES (p_booking_id, p_service_id, p_user_id, p_quantity)
    RETURNING order_id INTO v_order_id;

    INSERT INTO folio_lines (folio_id, description, amount, line_type, charge_date, service_order_id)
    VALUES (
        v_folio_id,
        'Услуга: ' || (SELECT name FROM services WHERE service_id = p_service_id),
        v_price * p_quantity,
        'SERVICE',
        CURRENT_DATE,
        v_order_id
    );

    RETURN v_order_id;
END;
$$;

CREATE OR REPLACE FUNCTION fn_record_payment(
    p_folio_id INTEGER,
    p_amount NUMERIC,
    p_method VARCHAR,
    p_type VARCHAR,
    p_user_id INTEGER,
    p_ip VARCHAR
) RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_payment_id INTEGER;
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    IF NOT EXISTS (SELECT 1 FROM folios WHERE folio_id = p_folio_id AND status = 'OPEN') THEN
        RAISE EXCEPTION 'Folio закрыт или не найден';
    END IF;

    INSERT INTO payments (folio_id, amount, method, payment_type)
    VALUES (p_folio_id, p_amount, p_method, COALESCE(p_type, 'PAYMENT'))
    RETURNING payment_id INTO v_payment_id;

    RETURN v_payment_id;
END;
$$;

CREATE OR REPLACE FUNCTION fn_refund_payment(
    p_payment_id INTEGER,
    p_amount NUMERIC,
    p_reason VARCHAR,
    p_user_id INTEGER,
    p_ip VARCHAR
) RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_refund_id INTEGER;
    v_payment_amount NUMERIC(10,2);
    v_refunded NUMERIC(10,2);
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    SELECT amount INTO v_payment_amount FROM payments WHERE payment_id = p_payment_id;

    SELECT COALESCE(SUM(amount), 0) INTO v_refunded
    FROM refunds
    WHERE payment_id = p_payment_id;

    IF p_amount > v_payment_amount - v_refunded THEN
        RAISE EXCEPTION 'Сумма возврата превышает остаток платежа';
    END IF;

    INSERT INTO refunds (payment_id, amount, reason)
    VALUES (p_payment_id, p_amount, p_reason)
    RETURNING refund_id INTO v_refund_id;

    RETURN v_refund_id;
END;
$$;

CREATE OR REPLACE FUNCTION fn_assign_housekeeping_task(
    p_room_id INTEGER,
    p_staff_id INTEGER,
    p_task_type VARCHAR,
    p_priority VARCHAR,
    p_user_id INTEGER,
    p_ip VARCHAR
) RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_task_id INTEGER;
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    INSERT INTO housekeeping_tasks (room_id, staff_id, task_type, status, priority)
    VALUES (p_room_id, p_staff_id, p_task_type, 'ASSIGNED', COALESCE(p_priority, 'NORMAL'))
    RETURNING task_id INTO v_task_id;

    RETURN v_task_id;
END;
$$;

CREATE OR REPLACE PROCEDURE sp_start_housekeeping_task(
    p_task_id INTEGER,
    p_user_id INTEGER,
    p_ip VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_room_id INTEGER;
    v_status_id INTEGER;
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    UPDATE housekeeping_tasks
    SET status = 'IN_PROGRESS'
    WHERE task_id = p_task_id AND status = 'ASSIGNED'
    RETURNING room_id INTO v_room_id;

    IF v_room_id IS NULL THEN
        RAISE EXCEPTION 'Задание % нельзя начать', p_task_id;
    END IF;

    SELECT status_id INTO v_status_id FROM room_statuses WHERE name = 'В_УБОРКЕ';
    UPDATE rooms SET status_id = v_status_id WHERE room_id = v_room_id;
END;
$$;

CREATE OR REPLACE PROCEDURE sp_complete_housekeeping_task(
    p_task_id INTEGER,
    p_user_id INTEGER,
    p_ip VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_room_id INTEGER;
    v_status_id INTEGER;
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    UPDATE housekeeping_tasks
    SET status = 'DONE', completed_at = now()
    WHERE task_id = p_task_id AND status IN ('ASSIGNED','IN_PROGRESS')
    RETURNING room_id INTO v_room_id;

    IF v_room_id IS NULL THEN
        RAISE EXCEPTION 'Задание % нельзя завершить', p_task_id;
    END IF;

    SELECT status_id INTO v_status_id FROM room_statuses WHERE name = 'ЧИСТЫЙ_ГОТОВ';
    UPDATE rooms SET status_id = v_status_id WHERE room_id = v_room_id;
END;
$$;

CREATE OR REPLACE PROCEDURE sp_cancel_housekeeping_task(
    p_task_id INTEGER,
    p_user_id INTEGER,
    p_ip VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    UPDATE housekeeping_tasks
    SET status = 'CANCELLED'
    WHERE task_id = p_task_id AND status IN ('ASSIGNED','IN_PROGRESS');

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Задание % нельзя отменить', p_task_id;
    END IF;
END;
$$;

CREATE OR REPLACE FUNCTION fn_write_off_consumable(
    p_task_id INTEGER,
    p_consumable_id INTEGER,
    p_quantity NUMERIC,
    p_user_id INTEGER,
    p_ip VARCHAR
) RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_usage_id INTEGER;
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    INSERT INTO consumable_usage (task_id, consumable_id, quantity)
    VALUES (p_task_id, p_consumable_id, p_quantity)
    RETURNING usage_id INTO v_usage_id;

    RETURN v_usage_id;
END;
$$;

CREATE OR REPLACE FUNCTION fn_create_maintenance_request(
    p_room_id INTEGER,
    p_task_id INTEGER,
    p_description TEXT,
    p_priority VARCHAR,
    p_assigned_to INTEGER,
    p_user_id INTEGER,
    p_ip VARCHAR
) RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_request_id INTEGER;
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    INSERT INTO maintenance_requests (room_id, task_id, description, status, priority, assigned_to)
    VALUES (p_room_id, p_task_id, p_description, 'OPEN', COALESCE(p_priority, 'NORMAL'), p_assigned_to)
    RETURNING request_id INTO v_request_id;

    RETURN v_request_id;
END;
$$;

CREATE OR REPLACE PROCEDURE sp_set_room_status(
    p_room_id INTEGER,
    p_status_name VARCHAR,
    p_reason_id INTEGER,
    p_user_id INTEGER,
    p_ip VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_status_id INTEGER;
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    SELECT status_id INTO v_status_id FROM room_statuses WHERE name = p_status_name;

    IF v_status_id IS NULL THEN
        RAISE EXCEPTION 'Статус номера % не найден', p_status_name;
    END IF;

    IF p_status_name = 'БЛОКИРОВАН' AND p_reason_id IS NULL THEN
        RAISE EXCEPTION 'Для блокировки номера нужно указать причину';
    END IF;

    UPDATE rooms
    SET status_id = v_status_id,
        block_reason_id = CASE WHEN p_status_name = 'БЛОКИРОВАН' THEN p_reason_id ELSE NULL END
    WHERE room_id = p_room_id;
END;
$$;

CREATE OR REPLACE PROCEDURE sp_update_maintenance_status(
    p_request_id INTEGER,
    p_status VARCHAR,
    p_user_id INTEGER,
    p_ip VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    UPDATE maintenance_requests
    SET status = p_status
    WHERE request_id = p_request_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Заявка % не найдена', p_request_id;
    END IF;
END;
$$;

-- ===== 003_week6.sql =====
-- =====================================================================================
--  SunStay: неделя 6 — безопасность и администрирование
--  RBAC, сессии, настройки пользователя, журнал входов.
-- =====================================================================================

BEGIN;

ALTER TABLE users
    ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN last_login_at TIMESTAMP,
    ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0 CHECK (failed_login_attempts >= 0),
    ADD COLUMN locked_until TIMESTAMP,
    ADD COLUMN password_changed_at TIMESTAMP;

CREATE TABLE permissions (
    permission_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code          VARCHAR(100) NOT NULL UNIQUE,
    module        VARCHAR(50)  NOT NULL,
    description   VARCHAR(255) NOT NULL
);

CREATE TABLE role_permissions (
    role_id       INTEGER NOT NULL REFERENCES roles(role_id) ON DELETE CASCADE,
    permission_id INTEGER NOT NULL REFERENCES permissions(permission_id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

CREATE TABLE user_sessions (
    session_id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    refresh_token_hash  VARCHAR(255) NOT NULL UNIQUE,
    user_agent          VARCHAR(255),
    ip_address          VARCHAR(50),
    created_at          TIMESTAMP NOT NULL DEFAULT now(),
    expires_at          TIMESTAMP NOT NULL,
    revoked_at          TIMESTAMP
);

CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);

CREATE TABLE login_attempts (
    attempt_id   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email        VARCHAR(150) NOT NULL,
    ip_address   VARCHAR(50),
    success      BOOLEAN NOT NULL DEFAULT FALSE,
    attempted_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_login_attempts_email ON login_attempts(email);

CREATE TABLE user_settings (
    user_id       INTEGER PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    theme         VARCHAR(10) NOT NULL DEFAULT 'system'
        CHECK (theme IN ('light','dark','system')),
    language      VARCHAR(5) NOT NULL DEFAULT 'ru'
        CHECK (language IN ('ru','en')),
    date_format   VARCHAR(20) NOT NULL DEFAULT 'dd.MM.yyyy',
    number_format VARCHAR(20) NOT NULL DEFAULT 'space_comma',
    page_size     INTEGER NOT NULL DEFAULT 25
        CHECK (page_size IN (10,25,50)),
    saved_filters JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_at    TIMESTAMP NOT NULL DEFAULT now()
);

INSERT INTO permissions (code, module, description) VALUES
    ('dashboard:view',       'dashboard',    'Просмотр дашборда'),
    ('bookings:view',        'bookings',     'Просмотр бронирований'),
    ('bookings:create',      'bookings',     'Создание бронирований'),
    ('bookings:update',      'bookings',     'Изменение бронирований'),
    ('bookings:confirm',     'bookings',     'Подтверждение бронирований'),
    ('bookings:cancel',      'bookings',     'Отмена бронирований'),
    ('bookings:checkin',     'bookings',     'Заселение гостя'),
    ('bookings:checkout',    'bookings',     'Выселение гостя'),
    ('bookings:night_audit', 'bookings',     'Ночной аудит'),
    ('rooms:view',           'rooms',        'Просмотр номерного фонда'),
    ('rooms:update_status',  'rooms',        'Изменение статуса номера'),
    ('rooms:manage',         'rooms',        'Управление номерным фондом'),
    ('rates:view',           'rates',        'Просмотр тарифов'),
    ('rates:manage',         'rates',        'Управление тарифами'),
    ('services:view',        'services',     'Просмотр услуг'),
    ('services:order',       'services',     'Заказ дополнительных услуг'),
    ('services:manage',      'services',     'Управление услугами'),
    ('promo:manage',         'promo',        'Управление промокодами'),
    ('folios:view',          'folios',       'Просмотр folio и счетов'),
    ('folios:manage',        'folios',       'Управление folio и счетами'),
    ('payments:create',      'payments',     'Приём платежей'),
    ('payments:refund',      'payments',     'Возвраты платежей'),
    ('housekeeping:view',    'housekeeping', 'Просмотр заданий хаускипинга'),
    ('housekeeping:manage',  'housekeeping', 'Управление заданиями хаускипинга'),
    ('maintenance:view',     'maintenance',  'Просмотр заявок на ремонт'),
    ('maintenance:manage',   'maintenance',  'Управление заявками на ремонт'),
    ('consumables:view',     'consumables',  'Просмотр расходных материалов'),
    ('consumables:manage',   'consumables',  'Списание расходных материалов'),
    ('reports:view',         'reports',      'Просмотр отчётов'),
    ('reports:export',       'reports',      'Экспорт отчётов'),
    ('users:view',           'users',        'Просмотр пользователей'),
    ('users:manage',         'users',        'Управление пользователями'),
    ('users:assign_roles',   'users',        'Назначение ролей сотрудникам'),
    ('roles:manage',         'roles',        'Управление правами ролей'),
    ('audit:view',           'audit',        'Просмотр журнала аудита'),
    ('audit:export',         'audit',        'Экспорт журнала аудита'),
    ('backup:manage',        'backup',       'Резервное копирование и восстановление'),
    ('monitoring:view',      'monitoring',   'Мониторинг системы'),
    ('settings:manage',      'settings',     'Управление настройками системы'),
    ('imports:bank',         'imports',      'Импорт банковской выписки'),
    ('imports:rates',        'imports',      'Импорт тарифов'),
    ('guest:self',           'guest',        'Доступ к собственным данным гостя'),
    ('profile:edit',         'profile',      'Редактирование профиля и настроек')
ON CONFLICT (code) DO NOTHING;

-- Гость
INSERT INTO role_permissions (role_id, permission_id)
SELECT 1, permission_id FROM permissions
WHERE code IN (
    'guest:self', 'profile:edit',
    'bookings:view', 'bookings:create', 'bookings:cancel',
    'folios:view', 'services:view', 'services:order'
)
ON CONFLICT DO NOTHING;

-- Менеджер
INSERT INTO role_permissions (role_id, permission_id)
SELECT 2, permission_id FROM permissions
WHERE code IN (
    'dashboard:view',
    'bookings:view', 'bookings:create', 'bookings:update', 'bookings:confirm',
    'bookings:cancel', 'bookings:checkin', 'bookings:checkout', 'bookings:night_audit',
    'rooms:view', 'rooms:update_status',
    'rates:view', 'services:view', 'services:order',
    'folios:view', 'folios:manage', 'payments:create', 'payments:refund',
    'housekeeping:view', 'housekeeping:manage',
    'maintenance:view', 'maintenance:manage',
    'consumables:view', 'consumables:manage',
    'reports:view', 'reports:export', 'imports:bank', 'profile:edit'
)
ON CONFLICT DO NOTHING;

-- Хаускипинг
INSERT INTO role_permissions (role_id, permission_id)
SELECT 3, permission_id FROM permissions
WHERE code IN (
    'housekeeping:view', 'housekeeping:manage',
    'rooms:view', 'rooms:update_status',
    'maintenance:view', 'maintenance:manage',
    'consumables:view', 'consumables:manage',
    'profile:edit'
)
ON CONFLICT DO NOTHING;

-- Управляющий отелем (всё, кроме админских операций)
INSERT INTO role_permissions (role_id, permission_id)
SELECT 4, permission_id FROM permissions
WHERE code NOT IN (
    'backup:manage', 'monitoring:view', 'settings:manage',
    'roles:manage', 'audit:export'
)
ON CONFLICT DO NOTHING;

-- Администратор БД
INSERT INTO role_permissions (role_id, permission_id)
SELECT 5, permission_id FROM permissions
ON CONFLICT DO NOTHING;

-- Демонстрационные пароли: SunStay2026!
UPDATE users
SET password_hash = crypt('SunStay2026!', gen_salt('bf', 12)),
    password_changed_at = now(),
    is_active = TRUE;

INSERT INTO user_settings (user_id)
SELECT user_id FROM users
ON CONFLICT (user_id) DO NOTHING;

COMMIT;

CREATE OR REPLACE VIEW v_user_permissions AS
SELECT
    u.user_id,
    u.full_name,
    r.name AS role_name,
    p.code AS permission_code,
    p.module,
    p.description
FROM users u
JOIN roles r ON r.role_id = u.role_id
JOIN role_permissions rp ON rp.role_id = r.role_id
JOIN permissions p ON p.permission_id = rp.permission_id;

CREATE OR REPLACE FUNCTION fn_has_permission(p_user_id INTEGER, p_code VARCHAR)
RETURNS BOOLEAN
LANGUAGE sql STABLE AS $$
    SELECT EXISTS (
        SELECT 1
        FROM v_user_permissions
        WHERE user_id = p_user_id AND permission_code = p_code
    );
$$;

CREATE OR REPLACE FUNCTION fn_user_permissions(p_user_id INTEGER)
RETURNS TABLE(permission_code VARCHAR)
LANGUAGE sql STABLE AS $$
    SELECT permission_code
    FROM v_user_permissions
    WHERE user_id = p_user_id
    ORDER BY permission_code;
$$;

-- ===== 004_week8_views.sql =====
-- =====================================================================================
--  SunStay: неделя 8 — представления для статистики и отчётности
-- =====================================================================================

CREATE OR REPLACE VIEW v_occupancy_daily AS
WITH bounds AS (
    SELECT MIN(checkin_date) AS min_date,
           MAX(checkout_date) AS max_date
    FROM bookings
), dates AS (
    SELECT generate_series(min_date, max_date - 1, interval '1 day')::date AS report_date
    FROM bounds
), totals AS (
    SELECT COUNT(*)::numeric AS rooms_total FROM rooms
)
SELECT
    d.report_date,
    COALESCE(COUNT(DISTINCT b.room_id), 0) AS rooms_occupied,
    t.rooms_total AS rooms_available,
    ROUND(COALESCE(COUNT(DISTINCT b.room_id), 0) / NULLIF(t.rooms_total, 0) * 100, 2) AS occupancy_pct
FROM dates d
CROSS JOIN totals t
LEFT JOIN bookings b
    ON b.status IN ('NEW','CONFIRMED','CHECKED_IN','CHECKED_OUT')
   AND d.report_date >= b.checkin_date
   AND d.report_date < b.checkout_date
GROUP BY d.report_date, t.rooms_total
ORDER BY d.report_date;

CREATE OR REPLACE VIEW v_occupancy_by_type AS
WITH bounds AS (
    SELECT MIN(checkin_date) AS min_date,
           MAX(checkout_date) AS max_date
    FROM bookings
), dates AS (
    SELECT generate_series(min_date, max_date - 1, interval '1 day')::date AS report_date
    FROM bounds
), room_totals AS (
    SELECT rt.room_type_id, rt.name, COUNT(r.room_id)::numeric AS rooms_total
    FROM room_types rt
    LEFT JOIN rooms r ON r.room_type_id = rt.room_type_id
    GROUP BY rt.room_type_id, rt.name
)
SELECT
    d.report_date,
    rt.room_type_id,
    rt.name AS room_type,
    rt.rooms_total,
    COALESCE(COUNT(DISTINCT b.room_id), 0) AS rooms_occupied,
    ROUND(COALESCE(COUNT(DISTINCT b.room_id), 0) / NULLIF(rt.rooms_total, 0) * 100, 2) AS occupancy_pct
FROM dates d
CROSS JOIN room_totals rt
LEFT JOIN rooms r ON r.room_type_id = rt.room_type_id
LEFT JOIN bookings b
    ON b.room_id = r.room_id
   AND b.status IN ('NEW','CONFIRMED','CHECKED_IN','CHECKED_OUT')
   AND d.report_date >= b.checkin_date
   AND d.report_date < b.checkout_date
GROUP BY d.report_date, rt.room_type_id, rt.name, rt.rooms_total
ORDER BY d.report_date, rt.name;

CREATE OR REPLACE VIEW v_adr_revpar_daily AS
WITH bounds AS (
    SELECT MIN(checkin_date) AS min_date,
           MAX(checkout_date) AS max_date
    FROM bookings
), dates AS (
    SELECT generate_series(min_date, max_date - 1, interval '1 day')::date AS report_date
    FROM bounds
), revenue AS (
    SELECT
        d.report_date,
        SUM(rp.price_per_night) AS room_revenue
    FROM dates d
    JOIN bookings b
        ON b.status IN ('NEW','CONFIRMED','CHECKED_IN','CHECKED_OUT')
       AND d.report_date >= b.checkin_date
       AND d.report_date < b.checkout_date
    JOIN rate_plans rp ON rp.rate_id = b.rate_id
    GROUP BY d.report_date
), sold AS (
    SELECT d.report_date, COUNT(DISTINCT b.room_id)::numeric AS rooms_sold
    FROM dates d
    LEFT JOIN bookings b
        ON b.status IN ('NEW','CONFIRMED','CHECKED_IN','CHECKED_OUT')
       AND d.report_date >= b.checkin_date
       AND d.report_date < b.checkout_date
    GROUP BY d.report_date
), total_rooms AS (
    SELECT COUNT(*)::numeric AS rooms_available FROM rooms
)
SELECT
    d.report_date,
    COALESCE(r.room_revenue, 0) AS room_revenue,
    COALESCE(s.rooms_sold, 0) AS rooms_sold,
    tr.rooms_available,
    ROUND(COALESCE(r.room_revenue, 0) / NULLIF(s.rooms_sold, 0), 2) AS adr,
    ROUND(COALESCE(r.room_revenue, 0) / NULLIF(tr.rooms_available, 0), 2) AS revpar
FROM dates d
CROSS JOIN total_rooms tr
LEFT JOIN revenue r ON r.report_date = d.report_date
LEFT JOIN sold s ON s.report_date = d.report_date
ORDER BY d.report_date;

CREATE OR REPLACE VIEW v_cancellations_monthly AS
SELECT
    date_trunc('month', checkin_date)::date AS month,
    COUNT(*) AS total_bookings,
    COUNT(*) FILTER (WHERE status = 'CANCELLED') AS cancelled,
    COUNT(*) FILTER (WHERE status = 'NO_SHOW') AS no_show,
    ROUND(COUNT(*) FILTER (WHERE status = 'CANCELLED')::numeric / NULLIF(COUNT(*), 0) * 100, 2) AS cancellation_pct,
    ROUND(COUNT(*) FILTER (WHERE status = 'NO_SHOW')::numeric / NULLIF(COUNT(*), 0) * 100, 2) AS no_show_pct
FROM bookings
GROUP BY date_trunc('month', checkin_date)::date
ORDER BY month;

CREATE OR REPLACE VIEW v_cancellation_reasons AS
SELECT
    date_trunc('month', b.checkin_date)::date AS month,
    COALESCE(cr.name, 'Без причины') AS reason,
    COUNT(*) AS bookings
FROM bookings b
LEFT JOIN cancellation_reasons cr ON cr.reason_id = b.cancellation_reason_id
WHERE b.status = 'CANCELLED'
GROUP BY date_trunc('month', b.checkin_date)::date, COALESCE(cr.name, 'Без причины')
ORDER BY month, bookings DESC;

CREATE OR REPLACE VIEW v_room_status_today AS
SELECT
    rs.name AS status,
    COUNT(r.room_id) AS rooms,
    ROUND(COUNT(r.room_id)::numeric / NULLIF((SELECT COUNT(*) FROM rooms), 0) * 100, 2) AS percent
FROM room_statuses rs
LEFT JOIN rooms r ON r.status_id = rs.status_id
GROUP BY rs.name
ORDER BY rs.name;

CREATE OR REPLACE VIEW v_consumables_stock AS
SELECT
    c.consumable_id,
    c.name,
    c.unit,
    c.stock_quantity,
    c.min_stock,
    (c.stock_quantity < c.min_stock) AS deficit,
    COALESCE(SUM(cu.quantity), 0) AS used_total,
    COALESCE(SUM(cu.quantity) FILTER (WHERE ht.assigned_at >= now() - interval '30 days'), 0) AS used_30d
FROM consumables c
LEFT JOIN consumable_usage cu ON cu.consumable_id = c.consumable_id
LEFT JOIN housekeeping_tasks ht ON ht.task_id = cu.task_id
GROUP BY c.consumable_id, c.name, c.unit, c.stock_quantity, c.min_stock
ORDER BY c.name;

CREATE OR REPLACE VIEW v_revenue_by_service AS
SELECT
    date_trunc('month', so.ordered_at)::date AS month,
    s.service_id,
    s.name AS service,
    SUM(so.quantity) AS quantity,
    SUM(so.quantity * s.price) AS revenue
FROM service_orders so
JOIN services s ON s.service_id = so.service_id
GROUP BY date_trunc('month', so.ordered_at)::date, s.service_id, s.name
ORDER BY month, revenue DESC;

CREATE OR REPLACE VIEW v_payments_by_method AS
SELECT
    method,
    COUNT(*) AS payments,
    SUM(amount) AS total
FROM payments
GROUP BY method
ORDER BY total DESC;

CREATE OR REPLACE VIEW v_dashboard_today AS
SELECT
    (SELECT COUNT(DISTINCT room_id)
     FROM bookings
     WHERE CURRENT_DATE >= checkin_date
       AND CURRENT_DATE < checkout_date
       AND status IN ('NEW','CONFIRMED','CHECKED_IN','CHECKED_OUT')) AS occupied_rooms,
    (SELECT COUNT(*) FROM rooms) AS total_rooms,
    (SELECT ROUND(COUNT(DISTINCT room_id)::numeric / NULLIF((SELECT COUNT(*) FROM rooms), 0) * 100, 2)
     FROM bookings
     WHERE CURRENT_DATE >= checkin_date
       AND CURRENT_DATE < checkout_date
       AND status IN ('NEW','CONFIRMED','CHECKED_IN','CHECKED_OUT')) AS occupancy_pct,
    (SELECT COUNT(*) FROM bookings WHERE checkin_date = CURRENT_DATE AND status IN ('NEW','CONFIRMED')) AS arrivals_today,
    (SELECT COUNT(*) FROM bookings WHERE checkout_date = CURRENT_DATE AND status = 'CHECKED_IN') AS departures_today,
    (SELECT COALESCE(SUM(amount), 0) FROM folio_lines WHERE line_type = 'ROOM' AND charge_date = CURRENT_DATE) AS room_revenue_today,
    (SELECT COALESCE(SUM(amount), 0) FROM payments WHERE paid_at::date = CURRENT_DATE) AS payments_today,
    (SELECT ROUND(SUM(rp.price_per_night) / NULLIF(COUNT(*), 0), 2)
     FROM bookings b
     JOIN rate_plans rp ON rp.rate_id = b.rate_id
     WHERE CURRENT_DATE >= b.checkin_date
       AND CURRENT_DATE < b.checkout_date
       AND b.status IN ('NEW','CONFIRMED','CHECKED_IN','CHECKED_OUT')) AS adr_today,
    (SELECT ROUND(SUM(rp.price_per_night) / NULLIF((SELECT COUNT(*) FROM rooms), 0), 2)
     FROM bookings b
     JOIN rate_plans rp ON rp.rate_id = b.rate_id
     WHERE CURRENT_DATE >= b.checkin_date
       AND CURRENT_DATE < b.checkout_date
       AND b.status IN ('NEW','CONFIRMED','CHECKED_IN','CHECKED_OUT')) AS revpar_today;

-- ===== 006_fix_checkout.sql =====
-- =====================================================================================
--  SunStay: доработка check-out — гарантированное начисление всех ночей проживания
-- =====================================================================================

CREATE OR REPLACE PROCEDURE sp_check_out(
    p_booking_id INTEGER,
    p_manager_id INTEGER,
    p_payment_amount NUMERIC,
    p_payment_method VARCHAR,
    p_ip VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_room_id INTEGER;
    v_checkin DATE;
    v_checkout DATE;
    v_rate_id INTEGER;
    v_price NUMERIC(10,2);
    v_folio_id INTEGER;
    v_status_id INTEGER;
    d DATE;
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_manager_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    SELECT room_id, checkin_date, checkout_date, rate_id
    INTO v_room_id, v_checkin, v_checkout, v_rate_id
    FROM bookings
    WHERE booking_id = p_booking_id
      AND status = 'CHECKED_IN';

    IF v_room_id IS NULL THEN
        RAISE EXCEPTION 'Выселение возможно только для заселённой брони';
    END IF;

    SELECT folio_id INTO v_folio_id
    FROM folios
    WHERE booking_id = p_booking_id AND status = 'OPEN'
    ORDER BY folio_id DESC
    LIMIT 1;

    IF v_folio_id IS NULL THEN
        RAISE EXCEPTION 'Открытый folio не найден';
    END IF;

    SELECT price_per_night INTO v_price
    FROM rate_plans
    WHERE rate_id = v_rate_id;

    FOR d IN
        SELECT generate_series(v_checkin, v_checkout - 1, interval '1 day')::date
    LOOP
        IF NOT EXISTS (
            SELECT 1
            FROM folio_lines
            WHERE folio_id = v_folio_id
              AND line_type = 'ROOM'
              AND charge_date = d
        ) THEN
            INSERT INTO folio_lines (folio_id, description, amount, line_type, charge_date)
            VALUES (
                v_folio_id,
                'Проживание за ' || to_char(d, 'DD.MM.YYYY'),
                v_price,
                'ROOM',
                d
            );
        END IF;
    END LOOP;

    IF COALESCE(p_payment_amount, 0) > 0 THEN
        INSERT INTO payments (folio_id, amount, method, payment_type)
        VALUES (v_folio_id, p_payment_amount, COALESCE(p_payment_method, 'CARD'), 'PAYMENT');
    END IF;

    UPDATE folios
    SET status = 'CLOSED', closed_at = now()
    WHERE folio_id = v_folio_id;

    UPDATE bookings
    SET status = 'CHECKED_OUT'
    WHERE booking_id = p_booking_id;

    SELECT status_id INTO v_status_id FROM room_statuses WHERE name = 'ГРЯЗНЫЙ';
    UPDATE rooms SET status_id = v_status_id WHERE room_id = v_room_id;

    INSERT INTO housekeeping_tasks (room_id, staff_id, task_type, status, priority)
    VALUES (v_room_id, NULL, 'POST_CHECKOUT', 'ASSIGNED', 'HIGH');
END;
$$;

-- ===== 007_demo_current.sql =====
-- =====================================================================================
--  SunStay: демонстрационные брони на текущую неделю
--  Выполняется после основной схемы и наполнения.
-- =====================================================================================

UPDATE users
SET full_name = 'Иванов Иван Иванович'
WHERE user_id = 1
  AND full_name = 'Гостевой аккаунт (демо)';

INSERT INTO rate_plans (room_type_id, name, season_start, season_end, price_per_night, cancellation_terms)
SELECT 1, 'Стандарт — межсезонье', '2026-10-01', '2026-12-31', 4000.00, 'Бесплатная отмена за 24 часа'
WHERE NOT EXISTS (SELECT 1 FROM rate_plans WHERE name = 'Стандарт — межсезонье');

DO $$
DECLARE
    v_booking_id INTEGER;
    v_rate_standard INTEGER;
BEGIN
    SELECT rate_id INTO v_rate_standard
    FROM rate_plans
    WHERE room_type_id = 1
      AND CURRENT_DATE BETWEEN season_start AND season_end
    ORDER BY price_per_night
    LIMIT 1;

    IF v_rate_standard IS NULL THEN
        RAISE EXCEPTION 'Не найден тариф для Стандарта на текущую дату';
    END IF;

    -- 101: подтверждённая бронь на 2 ночи
    IF NOT EXISTS (
        SELECT 1 FROM bookings
        WHERE room_id = 1
          AND status IN ('NEW','CONFIRMED','CHECKED_IN')
          AND daterange(checkin_date, checkout_date, '[)')
              && daterange(CURRENT_DATE, CURRENT_DATE + 2, '[)')
    ) THEN
        SELECT fn_create_booking(2, 1, v_rate_standard, CURRENT_DATE, CURRENT_DATE + 2, NULL, 'SITE', 1, 0, 2, '127.0.0.1')
        INTO v_booking_id;
        CALL sp_confirm_booking(v_booking_id, 2, '127.0.0.1');
    END IF;

    -- 102: подтверждённая бронь на 3 ночи
    IF NOT EXISTS (
        SELECT 1 FROM bookings
        WHERE room_id = 2
          AND status IN ('NEW','CONFIRMED','CHECKED_IN')
          AND daterange(checkin_date, checkout_date, '[)')
              && daterange(CURRENT_DATE, CURRENT_DATE + 3, '[)')
    ) THEN
        SELECT fn_create_booking(1, 2, v_rate_standard, CURRENT_DATE, CURRENT_DATE + 3, NULL, 'PHONE', 1, 0, 2, '127.0.0.1')
        INTO v_booking_id;
        CALL sp_confirm_booking(v_booking_id, 2, '127.0.0.1');
    END IF;

    -- 201: подтверждённая бронь на 2 ночи
    IF NOT EXISTS (
        SELECT 1 FROM bookings
        WHERE room_id = 3
          AND status IN ('NEW','CONFIRMED','CHECKED_IN')
          AND daterange(checkin_date, checkout_date, '[)')
              && daterange(CURRENT_DATE, CURRENT_DATE + 2, '[)')
    ) THEN
        SELECT fn_create_booking(4, 3, 3, CURRENT_DATE, CURRENT_DATE + 2, NULL, 'OTA', 1, 0, 2, '127.0.0.1')
        INTO v_booking_id;
        CALL sp_confirm_booking(v_booking_id, 2, '127.0.0.1');
    END IF;

    -- 202: заселённый гость на 3 ночи
    IF NOT EXISTS (
        SELECT 1 FROM bookings
        WHERE room_id = 4
          AND status IN ('NEW','CONFIRMED','CHECKED_IN')
          AND daterange(checkin_date, checkout_date, '[)')
              && daterange(CURRENT_DATE, CURRENT_DATE + 3, '[)')
    ) THEN
        SELECT fn_create_booking(3, 4, 3, CURRENT_DATE, CURRENT_DATE + 3, NULL, 'SITE', 1, 1, 2, '127.0.0.1')
        INTO v_booking_id;
        CALL sp_confirm_booking(v_booking_id, 2, '127.0.0.1');
        CALL sp_check_in(v_booking_id, 2, '4512 789012', 5000, 'CARD', '127.0.0.1');
    END IF;
END;
$$;

-- Демонстрационная история проживаний за последние две недели
DO $$
DECLARE
    v_std INTEGER;
    v_comf INTEGER;
    v_lux INTEGER;
BEGIN
    SELECT rate_id INTO v_std
    FROM rate_plans
    WHERE room_type_id = 1
      AND CURRENT_DATE BETWEEN season_start AND season_end
    ORDER BY price_per_night
    LIMIT 1;

    SELECT rate_id INTO v_comf
    FROM rate_plans
    WHERE room_type_id = 2
      AND CURRENT_DATE BETWEEN season_start AND season_end
    ORDER BY price_per_night
    LIMIT 1;

    SELECT rate_id INTO v_lux
    FROM rate_plans
    WHERE room_type_id = 3
      AND CURRENT_DATE BETWEEN season_start AND season_end
    ORDER BY price_per_night
    LIMIT 1;

    IF v_std IS NULL OR v_comf IS NULL OR v_lux IS NULL THEN
        RETURN;
    END IF;

    INSERT INTO bookings (guest_id, room_id, rate_id, checkin_date, checkout_date, status, source, adults, children)
    VALUES
        (2, 1, v_std, CURRENT_DATE - 15, CURRENT_DATE - 13, 'CHECKED_OUT', 'SITE', 1, 0),
        (4, 1, v_std, CURRENT_DATE - 10, CURRENT_DATE - 8,  'CHECKED_OUT', 'PHONE', 2, 0),
        (2, 1, v_std, CURRENT_DATE - 5,  CURRENT_DATE - 3,  'CHECKED_OUT', 'OTA', 1, 1),
        (1, 2, v_std, CURRENT_DATE - 14, CURRENT_DATE - 12, 'CHECKED_OUT', 'SITE', 1, 0),
        (3, 2, v_std, CURRENT_DATE - 9,  CURRENT_DATE - 7,  'CHECKED_OUT', 'WALK_IN', 1, 0),
        (4, 2, v_std, CURRENT_DATE - 4,  CURRENT_DATE - 2,  'CHECKED_OUT', 'SITE', 2, 0),
        (2, 3, v_comf, CURRENT_DATE - 15, CURRENT_DATE - 14, 'CHECKED_OUT', 'SITE', 2, 0),
        (3, 3, v_comf, CURRENT_DATE - 11, CURRENT_DATE - 9,  'CHECKED_OUT', 'OTA', 1, 0),
        (1, 3, v_comf, CURRENT_DATE - 6,  CURRENT_DATE - 4,  'CHECKED_OUT', 'PHONE', 1, 1),
        (4, 4, v_comf, CURRENT_DATE - 13, CURRENT_DATE - 11, 'CHECKED_OUT', 'SITE', 2, 0),
        (1, 4, v_comf, CURRENT_DATE - 8,  CURRENT_DATE - 6,  'CHECKED_OUT', 'OTA', 1, 0),
        (2, 4, v_comf, CURRENT_DATE - 3,  CURRENT_DATE - 1,  'CHECKED_OUT', 'SITE', 1, 0),
        (3, 5, v_lux, CURRENT_DATE - 12, CURRENT_DATE - 10, 'CHECKED_OUT', 'SITE', 2, 1),
        (4, 5, v_lux, CURRENT_DATE - 7,  CURRENT_DATE - 5,  'CHECKED_OUT', 'PHONE', 1, 0),
        (1, 5, v_lux, CURRENT_DATE - 2,  CURRENT_DATE - 1,  'CHECKED_OUT', 'OTA', 2, 0),
        (1, 2, v_std, CURRENT_DATE - 15, CURRENT_DATE - 14, 'CHECKED_OUT', 'SITE', 1, 0),
        (2, 3, v_comf, CURRENT_DATE - 14, CURRENT_DATE - 12, 'CHECKED_OUT', 'SITE', 2, 0),
        (3, 4, v_comf, CURRENT_DATE - 15, CURRENT_DATE - 13, 'CHECKED_OUT', 'OTA', 1, 0),
        (4, 5, v_lux, CURRENT_DATE - 15, CURRENT_DATE - 12, 'CHECKED_OUT', 'SITE', 1, 0),
        (3, 2, v_std, CURRENT_DATE - 12, CURRENT_DATE - 10, 'CHECKED_OUT', 'PHONE', 1, 0),
        (4, 1, v_std, CURRENT_DATE - 13, CURRENT_DATE - 10, 'CHECKED_OUT', 'SITE', 2, 0),
        (1, 3, v_comf, CURRENT_DATE - 9,  CURRENT_DATE - 6,  'CHECKED_OUT', 'SITE', 1, 1),
        (2, 4, v_comf, CURRENT_DATE - 6,  CURRENT_DATE - 3,  'CHECKED_OUT', 'OTA', 2, 0),
        (3, 5, v_lux, CURRENT_DATE - 5,  CURRENT_DATE - 2,  'CHECKED_OUT', 'SITE', 1, 0)
    ON CONFLICT DO NOTHING;

    INSERT INTO bookings (guest_id, room_id, rate_id, checkin_date, checkout_date, status, source, adults, children, cancellation_reason_id)
    VALUES
        (3, 1, v_std, CURRENT_DATE - 16, CURRENT_DATE - 14, 'CANCELLED', 'SITE', 1, 0, 1),
        (2, 3, v_comf, CURRENT_DATE - 12, CURRENT_DATE - 10, 'CANCELLED', 'SITE', 1, 0, 2),
        (4, 5, v_lux, CURRENT_DATE - 6, CURRENT_DATE - 4, 'NO_SHOW', 'PHONE', 1, 0, NULL)
    ON CONFLICT DO NOTHING;
END;
$$;

-- Демонстрационное начисление проживания за текущую ночь
INSERT INTO folio_lines (folio_id, description, amount, line_type, charge_date)
SELECT
    f.folio_id,
    'Проживание за ' || to_char(CURRENT_DATE, 'DD.MM.YYYY'),
    rp.price_per_night,
    'ROOM',
    CURRENT_DATE
FROM folios f
JOIN bookings b ON b.booking_id = f.booking_id
JOIN rate_plans rp ON rp.rate_id = b.rate_id
WHERE f.status = 'OPEN'
  AND b.status = 'CHECKED_IN'
  AND CURRENT_DATE >= b.checkin_date
  AND CURRENT_DATE < b.checkout_date
  AND NOT EXISTS (
      SELECT 1
      FROM folio_lines fl
      WHERE fl.folio_id = f.folio_id
        AND fl.line_type = 'ROOM'
        AND fl.charge_date = CURRENT_DATE
  );

-- Актуальные статусы номеров для демонстрации
UPDATE rooms SET status_id = (SELECT status_id FROM room_statuses WHERE name = 'ЗАБРОНИРОВАН')
WHERE room_id IN (1, 2)
  AND NOT EXISTS (
      SELECT 1 FROM bookings b
      WHERE b.room_id = rooms.room_id
        AND b.status = 'CHECKED_IN'
        AND CURRENT_DATE >= b.checkin_date
        AND CURRENT_DATE < b.checkout_date
  );

UPDATE rooms SET status_id = (SELECT status_id FROM room_statuses WHERE name = 'ЧИСТЫЙ_ГОТОВ')
WHERE room_id = 3
  AND NOT EXISTS (
      SELECT 1 FROM bookings b
      WHERE b.room_id = rooms.room_id
        AND b.status = 'CHECKED_IN'
        AND CURRENT_DATE >= b.checkin_date
        AND CURRENT_DATE < b.checkout_date
  );

UPDATE rooms SET status_id = (SELECT status_id FROM room_statuses WHERE name = 'СВОБОДЕН')
WHERE room_id = 5
  AND NOT EXISTS (
      SELECT 1 FROM bookings b
      WHERE b.room_id = rooms.room_id
        AND b.status = 'CHECKED_IN'
        AND CURRENT_DATE >= b.checkin_date
        AND CURRENT_DATE < b.checkout_date
  );

-- ===== 008_security_features.sql =====
-- =====================================================================================
--  SunStay: безопасность, аудит, блокировки, удержание брони, бэкапы
-- =====================================================================================

BEGIN;

ALTER TABLE users
    ADD COLUMN last_seen_at TIMESTAMPTZ,
    ADD COLUMN block_reason TEXT,
    ADD COLUMN blocked_at TIMESTAMPTZ,
    ADD COLUMN blocked_by INTEGER REFERENCES users(user_id) ON DELETE SET NULL;

CREATE TABLE user_block_reasons (
    reason_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name      VARCHAR(150) NOT NULL UNIQUE
);

INSERT INTO user_block_reasons (name) VALUES
    ('Нарушение правил'),
    ('Подозрительная активность'),
    ('Неактуальная учётная запись'),
    ('По заявлению сотрудника')
ON CONFLICT (name) DO NOTHING;

ALTER TABLE audit_log
    ADD COLUMN is_error BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN error_message TEXT,
    ADD COLUMN severity VARCHAR(10) NOT NULL DEFAULT 'INFO',
    ADD COLUMN event_type VARCHAR(30) NOT NULL DEFAULT 'DATA_CHANGE';

ALTER TABLE audit_log DROP CONSTRAINT IF EXISTS audit_log_action_check;
ALTER TABLE audit_log
    ADD CONSTRAINT audit_log_action_check CHECK (
        action IN (
            'INSERT', 'UPDATE', 'DELETE',
            'LOGIN_SUCCESS', 'LOGIN_FAILED', 'LOGIN_BLOCKED',
            'ERROR', 'AUTO_RELEASE'
        )
    );

CREATE INDEX idx_audit_error ON audit_log(is_error) WHERE is_error;
CREATE INDEX idx_audit_event_type ON audit_log(event_type);
CREATE INDEX idx_audit_changed_at ON audit_log(changed_at);
CREATE INDEX idx_users_last_seen ON users(last_seen_at);

ALTER TABLE bookings
    ADD COLUMN arrival_time TIME,
    ADD COLUMN hold_minutes INTEGER NOT NULL DEFAULT 60
        CHECK (hold_minutes BETWEEN 5 AND 1440),
    ADD COLUMN hold_until TIMESTAMPTZ;

CREATE INDEX idx_bookings_hold_until
    ON bookings(hold_until)
    WHERE hold_until IS NOT NULL;

INSERT INTO cancellation_reasons (name)
SELECT 'Истекло время ожидания'
WHERE NOT EXISTS (
    SELECT 1 FROM cancellation_reasons WHERE name = 'Истекло время ожидания'
);

INSERT INTO system_settings (key, value) VALUES
    ('backup.enabled', 'true'::jsonb),
    ('backup.schedule_time', '"03:00"'::jsonb),
    ('backup.last_run_at', 'null'::jsonb),
    ('backup.last_status', '"never"'::jsonb),
    ('backup.last_error', 'null'::jsonb)
ON CONFLICT (key) DO NOTHING;

COMMIT;

CREATE OR REPLACE FUNCTION fn_audit_row() RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_user_id INTEGER;
    v_ip VARCHAR(50);
    v_ua VARCHAR(255);
    v_request_id VARCHAR(100);
    v_record_id INTEGER;
    v_old JSONB;
    v_new JSONB;
BEGIN
    v_user_id := NULLIF(current_setting('app.current_user_id', true), '')::INTEGER;
    v_ip := NULLIF(current_setting('app.client_ip', true), '');
    v_ua := NULLIF(current_setting('app.user_agent', true), '');
    v_request_id := NULLIF(current_setting('app.request_id', true), '');

    -- Не засоряем аудит обновлениями last_seen_at при каждом запросе.
    IF TG_TABLE_NAME = 'users' AND TG_OP = 'UPDATE' THEN
        IF (to_jsonb(OLD) - 'last_seen_at') = (to_jsonb(NEW) - 'last_seen_at') THEN
            RETURN NEW;
        END IF;
    END IF;

    IF TG_OP = 'DELETE' THEN
        v_record_id := (to_jsonb(OLD) ->> TG_ARGV[0])::INTEGER;
        v_old := to_jsonb(OLD);
        v_new := NULL;
    ELSIF TG_OP = 'UPDATE' THEN
        v_record_id := (to_jsonb(NEW) ->> TG_ARGV[0])::INTEGER;
        v_old := to_jsonb(OLD);
        v_new := to_jsonb(NEW);
    ELSE
        v_record_id := (to_jsonb(NEW) ->> TG_ARGV[0])::INTEGER;
        v_old := NULL;
        v_new := to_jsonb(NEW);
    END IF;

    -- Не сохраняем в аудит шифротекст и хэши чувствительных полей.
    IF v_old IS NOT NULL THEN
        v_old := v_old
            - 'phone_enc' - 'document_number_enc' - 'guest_document_number_enc'
            - 'phone_hash' - 'document_number_hash' - 'guest_document_number_hash'
            - 'password_hash';
    END IF;
    IF v_new IS NOT NULL THEN
        v_new := v_new
            - 'phone_enc' - 'document_number_enc' - 'guest_document_number_enc'
            - 'phone_hash' - 'document_number_hash' - 'guest_document_number_hash'
            - 'password_hash';
    END IF;

    INSERT INTO audit_log (
        user_id, table_name, record_id, action,
        old_value, new_value, ip_address, user_agent, request_id,
        is_error, event_type, severity
    ) VALUES (
        v_user_id, TG_TABLE_NAME, v_record_id, TG_OP,
        v_old::TEXT, v_new::TEXT, v_ip, v_ua, v_request_id,
        FALSE, 'DATA_CHANGE', 'INFO'
    );

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$;

-- ===== 008b_audit_function.sql =====
CREATE OR REPLACE FUNCTION fn_audit_row() RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_user_id INTEGER;
    v_ip VARCHAR(50);
    v_ua VARCHAR(255);
    v_request_id VARCHAR(100);
    v_record_id INTEGER;
    v_old JSONB;
    v_new JSONB;
BEGIN
    v_user_id := NULLIF(current_setting('app.current_user_id', true), '')::INTEGER;
    v_ip := NULLIF(current_setting('app.client_ip', true), '');
    v_ua := NULLIF(current_setting('app.user_agent', true), '');
    v_request_id := NULLIF(current_setting('app.request_id', true), '');

    -- Не засоряем аудит обновлениями last_seen_at при каждом запросе.
    IF TG_TABLE_NAME = 'users' AND TG_OP = 'UPDATE' THEN
        IF (to_jsonb(OLD) - 'last_seen_at') = (to_jsonb(NEW) - 'last_seen_at') THEN
            RETURN NEW;
        END IF;
    END IF;

    IF TG_OP = 'DELETE' THEN
        v_record_id := (to_jsonb(OLD) ->> TG_ARGV[0])::INTEGER;
        v_old := to_jsonb(OLD);
        v_new := NULL;
    ELSIF TG_OP = 'UPDATE' THEN
        v_record_id := (to_jsonb(NEW) ->> TG_ARGV[0])::INTEGER;
        v_old := to_jsonb(OLD);
        v_new := to_jsonb(NEW);
    ELSE
        v_record_id := (to_jsonb(NEW) ->> TG_ARGV[0])::INTEGER;
        v_old := NULL;
        v_new := to_jsonb(NEW);
    END IF;

    -- Не сохраняем в аудит шифротекст и хэши чувствительных полей.
    IF v_old IS NOT NULL THEN
        v_old := v_old
            - 'phone_enc' - 'document_number_enc' - 'guest_document_number_enc'
            - 'phone_hash' - 'document_number_hash' - 'guest_document_number_hash'
            - 'password_hash';
    END IF;
    IF v_new IS NOT NULL THEN
        v_new := v_new
            - 'phone_enc' - 'document_number_enc' - 'guest_document_number_enc'
            - 'phone_hash' - 'document_number_hash' - 'guest_document_number_hash'
            - 'password_hash';
    END IF;

    INSERT INTO audit_log (
        user_id, table_name, record_id, action,
        old_value, new_value, ip_address, user_agent, request_id,
        is_error, event_type, severity
    ) VALUES (
        v_user_id, TG_TABLE_NAME, v_record_id, TG_OP,
        v_old::TEXT, v_new::TEXT, v_ip, v_ua, v_request_id,
        FALSE, 'DATA_CHANGE', 'INFO'
    );

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$;

-- ===== 009_encryption.sql =====
-- =====================================================================================
--  SunStay: шифрование чувствительных контактов
--  Открытые значения заменяются маскированными, полные — шифруются в *_enc,
--  для поиска и уникальности используются *_hash.
-- =====================================================================================

BEGIN;

ALTER TABLE guests
    ADD COLUMN phone_enc TEXT,
    ADD COLUMN document_number_enc TEXT,
    ADD COLUMN phone_hash VARCHAR(64),
    ADD COLUMN document_number_hash VARCHAR(64);

DO $$
DECLARE
    c RECORD;
BEGIN
    FOR c IN
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = 'guests'::regclass
          AND contype = 'u'
    LOOP
        IF c.conname = 'guests_document_number_key' THEN
            EXECUTE format('ALTER TABLE guests DROP CONSTRAINT %I', c.conname);
        END IF;
    END LOOP;
END;
$$;

CREATE UNIQUE INDEX uq_guests_document_hash
    ON guests(document_number_hash)
    WHERE document_number_hash IS NOT NULL;

CREATE INDEX idx_guests_phone_hash
    ON guests(phone_hash);

ALTER TABLE users
    ADD COLUMN phone_enc TEXT,
    ADD COLUMN phone_hash VARCHAR(64);

CREATE INDEX idx_users_phone_hash
    ON users(phone_hash);

ALTER TABLE check_ins
    ADD COLUMN guest_document_number_enc TEXT,
    ADD COLUMN guest_document_number_hash VARCHAR(64);

CREATE INDEX idx_check_ins_document_hash
    ON check_ins(guest_document_number_hash);

COMMIT;

-- ===== 010_secure_checkin_hold.sql =====
-- =====================================================================================
--  SunStay: безопасное заселение и удержание брони
-- =====================================================================================

DROP FUNCTION IF EXISTS fn_create_booking(INTEGER, INTEGER, INTEGER, DATE, DATE, INTEGER, VARCHAR, INTEGER, INTEGER, INTEGER, VARCHAR);

CREATE OR REPLACE FUNCTION fn_create_booking(
    p_guest_id INTEGER,
    p_room_id INTEGER,
    p_rate_id INTEGER,
    p_checkin DATE,
    p_checkout DATE,
    p_promo_id INTEGER,
    p_source VARCHAR,
    p_adults INTEGER,
    p_children INTEGER,
    p_user_id INTEGER,
    p_ip VARCHAR,
    p_arrival_time TIME DEFAULT NULL,
    p_hold_minutes INTEGER DEFAULT 60
) RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_booking_id INTEGER;
    v_arrival TIME;
    v_hold_until TIMESTAMPTZ;
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    IF NOT fn_room_available(p_room_id, p_checkin, p_checkout) THEN
        RAISE EXCEPTION 'Номер недоступен на выбранные даты';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM guests WHERE guest_id = p_guest_id AND pdn_consent = TRUE
    ) THEN
        RAISE EXCEPTION 'Нет согласия гостя на обработку персональных данных';
    END IF;

    v_arrival := COALESCE(p_arrival_time, TIME '14:00');
    v_hold_until := (p_checkin::timestamp + v_arrival)
        + make_interval(mins => COALESCE(p_hold_minutes, 60));

    INSERT INTO bookings (
        guest_id, room_id, rate_id, promo_id,
        checkin_date, checkout_date, status, source,
        adults, children, arrival_time, hold_minutes, hold_until
    ) VALUES (
        p_guest_id, p_room_id, p_rate_id, p_promo_id,
        p_checkin, p_checkout, 'NEW', COALESCE(p_source, 'SITE'),
        COALESCE(p_adults, 1), COALESCE(p_children, 0),
        v_arrival, COALESCE(p_hold_minutes, 60), v_hold_until
    )
    RETURNING booking_id INTO v_booking_id;

    RETURN v_booking_id;
EXCEPTION
    WHEN exclusion_violation THEN
        RAISE EXCEPTION 'Номер уже забронирован на выбранные даты';
END;
$$;

CREATE OR REPLACE PROCEDURE sp_check_in_secure(
    p_booking_id INTEGER,
    p_manager_id INTEGER,
    p_document_masked VARCHAR,
    p_document_enc TEXT,
    p_document_hash VARCHAR,
    p_deposit_amount NUMERIC,
    p_payment_method VARCHAR,
    p_ip VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_room_id INTEGER;
    v_folio_id INTEGER;
    v_status_id INTEGER;
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_manager_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    SELECT room_id INTO v_room_id
    FROM bookings
    WHERE booking_id = p_booking_id
      AND status = 'CONFIRMED';

    IF v_room_id IS NULL THEN
        RAISE EXCEPTION 'Заселение возможно только для подтверждённой брони';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM bookings b
        JOIN guests g ON g.guest_id = b.guest_id
        WHERE b.booking_id = p_booking_id
          AND g.document_number_hash = p_document_hash
    ) THEN
        RAISE EXCEPTION 'Документ не совпадает с данными гостя';
    END IF;

    IF EXISTS (
        SELECT 1
        FROM rooms r
        JOIN room_statuses rs ON rs.status_id = r.status_id
        WHERE r.room_id = v_room_id AND rs.name = 'БЛОКИРОВАН'
    ) THEN
        RAISE EXCEPTION 'Номер заблокирован';
    END IF;

    INSERT INTO check_ins (
        booking_id, manager_id, guest_document_number,
        guest_document_number_enc, guest_document_number_hash
    ) VALUES (
        p_booking_id, p_manager_id, p_document_masked,
        p_document_enc, p_document_hash
    );

    UPDATE bookings SET status = 'CHECKED_IN' WHERE booking_id = p_booking_id;

    SELECT status_id INTO v_status_id FROM room_statuses WHERE name = 'ЗАСЕЛЁН';
    UPDATE rooms SET status_id = v_status_id WHERE room_id = v_room_id;

    INSERT INTO folios (booking_id, status)
    VALUES (p_booking_id, 'OPEN')
    ON CONFLICT (booking_id) DO NOTHING;

    SELECT folio_id INTO v_folio_id
    FROM folios
    WHERE booking_id = p_booking_id
    ORDER BY folio_id DESC
    LIMIT 1;

    IF COALESCE(p_deposit_amount, 0) > 0 THEN
        INSERT INTO payments (folio_id, amount, method, payment_type)
        VALUES (v_folio_id, p_deposit_amount, COALESCE(p_payment_method, 'CARD'), 'DEPOSIT');
    END IF;
END;
$$;

-- ===== 011_closed_day_fix.sql =====
-- =====================================================================================
--  SunStay: закрытие бизнес-дня — разрешаем платежи после закрытия,
--  но запрещаем закрывать будущие даты.
-- =====================================================================================

CREATE OR REPLACE FUNCTION fn_prevent_closed_day() RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_date DATE;
    v_closed_at TIMESTAMP;
BEGIN
    IF current_setting('app.bypass_closed_day', true) = 'on' THEN
        IF TG_OP = 'DELETE' THEN
            RETURN OLD;
        END IF;
        RETURN NEW;
    END IF;

    IF TG_OP = 'DELETE' THEN
        IF TG_TABLE_NAME = 'folio_lines' THEN
            v_date := COALESCE(OLD.charge_date, OLD.created_at::date);
        ELSIF TG_TABLE_NAME = 'payments' THEN
            v_date := OLD.paid_at::date;
        ELSIF TG_TABLE_NAME = 'refunds' THEN
            v_date := OLD.refunded_at::date;
        END IF;
    ELSE
        IF TG_TABLE_NAME = 'folio_lines' THEN
            v_date := COALESCE(NEW.charge_date, NEW.created_at::date);
        ELSIF TG_TABLE_NAME = 'payments' THEN
            v_date := NEW.paid_at::date;
        ELSIF TG_TABLE_NAME = 'refunds' THEN
            v_date := NEW.refunded_at::date;
        END IF;
    END IF;

    IF v_date IS NOT NULL THEN
        SELECT closed_at INTO v_closed_at
        FROM business_days
        WHERE business_date = v_date;
    END IF;

    IF v_closed_at IS NOT NULL THEN
        IF TG_TABLE_NAME = 'payments' THEN
            IF TG_OP = 'DELETE' OR (TG_OP IN ('INSERT', 'UPDATE') AND NEW.paid_at <= v_closed_at) THEN
                RAISE EXCEPTION 'Бизнес-день % закрыт. Изменения запрещены', v_date;
            END IF;
        ELSIF TG_TABLE_NAME = 'refunds' THEN
            IF TG_OP = 'DELETE' OR (TG_OP IN ('INSERT', 'UPDATE') AND NEW.refunded_at <= v_closed_at) THEN
                RAISE EXCEPTION 'Бизнес-день % закрыт. Изменения запрещены', v_date;
            END IF;
        ELSE
            RAISE EXCEPTION 'Бизнес-день % закрыт. Изменения запрещены', v_date;
        END IF;
    END IF;

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE PROCEDURE sp_night_audit(
    p_business_date DATE,
    p_user_id INTEGER,
    p_ip VARCHAR,
    OUT p_posted_count INTEGER,
    OUT p_no_show_count INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    r RECORD;
BEGIN
    PERFORM set_config('app.current_user_id', COALESCE(p_user_id::text, ''), true);
    PERFORM set_config('app.client_ip', COALESCE(p_ip, ''), true);

    IF p_business_date > CURRENT_DATE THEN
        RAISE EXCEPTION 'Нельзя закрыть будущий бизнес-день %', p_business_date;
    END IF;

    IF EXISTS (SELECT 1 FROM business_days WHERE business_date = p_business_date) THEN
        RAISE EXCEPTION 'Бизнес-день % уже закрыт', p_business_date;
    END IF;

    p_posted_count := 0;

    FOR r IN
        SELECT b.booking_id, f.folio_id, rp.price_per_night
        FROM bookings b
        JOIN folios f ON f.booking_id = b.booking_id AND f.status = 'OPEN'
        JOIN rate_plans rp ON rp.rate_id = b.rate_id
        WHERE b.status = 'CHECKED_IN'
          AND p_business_date >= b.checkin_date
          AND p_business_date < b.checkout_date
    LOOP
        IF NOT EXISTS (
            SELECT 1
            FROM folio_lines fl
            WHERE fl.folio_id = r.folio_id
              AND fl.line_type = 'ROOM'
              AND fl.charge_date = p_business_date
        ) THEN
            INSERT INTO folio_lines (folio_id, description, amount, line_type, charge_date)
            VALUES (
                r.folio_id,
                'Проживание за ' || to_char(p_business_date, 'DD.MM.YYYY'),
                r.price_per_night,
                'ROOM',
                p_business_date
            );
            p_posted_count := p_posted_count + 1;
        END IF;
    END LOOP;

    UPDATE bookings
    SET status = 'NO_SHOW'
    WHERE status = 'CONFIRMED'
      AND checkin_date = p_business_date;

    GET DIAGNOSTICS p_no_show_count = ROW_COUNT;

    INSERT INTO business_days (business_date, closed_by, totals)
    VALUES (
        p_business_date,
        p_user_id,
        jsonb_build_object(
            'posted_count', p_posted_count,
            'no_show_count', p_no_show_count
        )
    );
END;
$$;

-- ===== 012_guest_experience.sql =====
-- =====================================================================================
--  SunStay: гостевой опыт — отзывы, лист ожидания, уведомления, курсы валют
-- =====================================================================================

BEGIN;

CREATE TABLE reviews (
    review_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    booking_id INTEGER NOT NULL UNIQUE REFERENCES bookings(booking_id) ON DELETE CASCADE,
    guest_id INTEGER NOT NULL REFERENCES guests(guest_id) ON DELETE CASCADE,
    rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    title VARCHAR(150),
    body TEXT NOT NULL CHECK (length(body) BETWEEN 10 AND 2000),
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING'
        CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
    moderated_by INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    moderated_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_reviews_status ON reviews(status, created_at DESC);
CREATE INDEX idx_reviews_guest ON reviews(guest_id, created_at DESC);

CREATE TRIGGER trg_audit_reviews
AFTER INSERT OR UPDATE OR DELETE ON reviews
FOR EACH ROW EXECUTE FUNCTION fn_audit_row('review_id');

CREATE TABLE waitlist_entries (
    waitlist_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    guest_name VARCHAR(200) NOT NULL,
    email VARCHAR(150),
    phone_masked VARCHAR(30),
    phone_enc TEXT,
    phone_hash VARCHAR(64),
    room_type_id INTEGER REFERENCES room_types(room_type_id) ON DELETE SET NULL,
    checkin_date DATE NOT NULL,
    checkout_date DATE NOT NULL,
    adults INTEGER NOT NULL DEFAULT 1 CHECK (adults BETWEEN 1 AND 10),
    children INTEGER NOT NULL DEFAULT 0 CHECK (children BETWEEN 0 AND 10),
    note TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'WAITING'
        CHECK (status IN ('WAITING', 'NOTIFIED', 'CONVERTED', 'CANCELLED')),
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    notified_at TIMESTAMP,
    processed_by INTEGER REFERENCES users(user_id) ON DELETE SET NULL,
    processed_at TIMESTAMP,
    CHECK (checkout_date > checkin_date)
);

CREATE INDEX idx_waitlist_status ON waitlist_entries(status, checkin_date);
CREATE INDEX idx_waitlist_dates ON waitlist_entries(checkin_date, checkout_date);

CREATE TRIGGER trg_audit_waitlist
AFTER INSERT OR UPDATE OR DELETE ON waitlist_entries
FOR EACH ROW EXECUTE FUNCTION fn_audit_row('waitlist_id');

CREATE TABLE notifications (
    notification_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    body TEXT,
    link VARCHAR(255),
    read_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_notifications_user ON notifications(user_id, read_at, created_at DESC);

INSERT INTO system_settings (key, value)
VALUES
    ('currency.usd_rate', '90'::jsonb),
    ('currency.eur_rate', '100'::jsonb)
ON CONFLICT (key) DO NOTHING;

INSERT INTO permissions (code, module, description)
VALUES ('reviews:moderate', 'reviews', 'Модерация отзывов гостей')
ON CONFLICT (code) DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id)
SELECT r.role_id, p.permission_id
FROM roles r
CROSS JOIN permissions p
WHERE r.name IN ('Управляющий отелем', 'Администратор БД')
  AND p.code = 'reviews:moderate'
ON CONFLICT DO NOTHING;

-- Демонстрационные одобренные отзывы по завершённым проживаниям.
WITH picked AS (
    SELECT b.booking_id, b.guest_id,
           row_number() OVER (ORDER BY b.booking_id) AS rn
    FROM bookings b
    WHERE b.status = 'CHECKED_OUT'
    ORDER BY b.booking_id
    LIMIT 3
)
INSERT INTO reviews (booking_id, guest_id, rating, title, body, status, created_at)
SELECT
    p.booking_id,
    p.guest_id,
    CASE p.rn WHEN 1 THEN 5 WHEN 2 THEN 4 ELSE 5 END,
    CASE p.rn
        WHEN 1 THEN 'Вернусь снова'
        WHEN 2 THEN 'Тихо и удобно'
        ELSE 'Отличный сервис'
    END,
    CASE p.rn
        WHEN 1 THEN 'Очень удобное расположение, внимательный персонал и спокойные номера. Завтрак свежий, всё продумано до мелочей.'
        WHEN 2 THEN 'Номер чистый, кровать удобная, интернет стабильный. Немного слышно улицу, но в целом отличный вариант для поездки.'
        ELSE 'Быстрое заселение, красивый интерьер и помощь с любыми вопросами. Отдельное спасибо команде за атмосферу.'
    END,
    'APPROVED',
    now() - (p.rn * interval '2 days')
FROM picked p
ON CONFLICT (booking_id) DO NOTHING;

COMMIT;

-- ===== 013_loyalty_security.sql =====
-- =====================================================================================
--  SunStay: лояльность, шаблоны сообщений, 2FA, политика паролей
-- =====================================================================================

BEGIN;

CREATE TABLE loyalty_accounts (
    user_id INTEGER PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    points_balance INTEGER NOT NULL DEFAULT 0 CHECK (points_balance >= 0),
    updated_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE loyalty_transactions (
    transaction_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    points INTEGER NOT NULL,
    transaction_type VARCHAR(20) NOT NULL CHECK (transaction_type IN ('EARN', 'REDEEM', 'ADJUST')),
    description VARCHAR(255),
    booking_id INTEGER REFERENCES bookings(booking_id) ON DELETE SET NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX idx_loyalty_tx_user ON loyalty_transactions(user_id, created_at DESC);

CREATE TABLE message_templates (
    template_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE,
    subject VARCHAR(200),
    body TEXT NOT NULL,
    template_type VARCHAR(30) NOT NULL DEFAULT 'NOTIFICATION',
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

ALTER TABLE users
    ADD COLUMN totp_secret_enc TEXT,
    ADD COLUMN totp_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN totp_recovery_codes JSONB;

INSERT INTO system_settings (key, value)
VALUES
    ('password.min_length', '8'::jsonb),
    ('password.require_uppercase', 'true'::jsonb),
    ('password.require_digit', 'true'::jsonb),
    ('password.require_special', 'false'::jsonb),
    ('loyalty.earn_percent', '5'::jsonb),
    ('loyalty.redeem_max_percent', '30'::jsonb)
ON CONFLICT (key) DO NOTHING;

INSERT INTO message_templates (name, subject, body, template_type)
VALUES
    ('Подтверждение брони', 'Ваша бронь подтверждена', 'Уважаемый гость, ваша бронь #{{booking_id}} подтверждена. Заезд {{checkin}}, выезд {{checkout}}.', 'NOTIFICATION'),
    ('Напоминание о заезде', 'Напоминание о заезде', 'Напоминаем, что ваш заезд {{checkin}} в SunStay. Будем рады вас видеть!', 'NOTIFICATION'),
    ('Счёт готов', 'Ваш счёт готов', 'Ваш счёт по брони #{{booking_id}} готов к оплате.', 'NOTIFICATION')
ON CONFLICT (name) DO NOTHING;

COMMIT;

-- ===== 014_guest_cancellation.sql =====
-- =====================================================================================
--  SunStay: особые пожелания и политика отмены
-- =====================================================================================

BEGIN;

ALTER TABLE bookings
    ADD COLUMN special_requests TEXT;

ALTER TABLE waitlist_entries
    ADD COLUMN converted_booking_id INTEGER REFERENCES bookings(booking_id) ON DELETE SET NULL;

INSERT INTO system_settings (key, value)
VALUES
    ('cancellation.free_hours', '48'::jsonb),
    ('cancellation.half_hours', '24'::jsonb),
    ('cancellation.half_percent', '50'::jsonb)
ON CONFLICT (key) DO NOTHING;

COMMIT;

-- ===== 015_images_features.sql =====
-- =====================================================================================
--  SunStay: изображения, feature flags, идемпотентность
-- =====================================================================================

BEGIN;

ALTER TABLE room_types ADD COLUMN image_url TEXT;
ALTER TABLE services ADD COLUMN image_url TEXT;

UPDATE room_types SET image_url = 'images/room-standard.jpg' WHERE name = 'Стандарт';
UPDATE room_types SET image_url = 'images/room-comfort.jpg' WHERE name = 'Комфорт';
UPDATE room_types SET image_url = 'images/room-lux.jpg' WHERE name = 'Люкс';

UPDATE services SET image_url = 'images/service-breakfast.jpg' WHERE name ILIKE '%завтрак%';
UPDATE services SET image_url = 'images/service-spa.jpg' WHERE name ILIKE '%спа%' OR name ILIKE '%массаж%';
UPDATE services SET image_url = 'images/service-other.jpg' WHERE image_url IS NULL;

INSERT INTO system_settings (key, value)
VALUES
    ('feature.reviews', 'true'::jsonb),
    ('feature.waitlist', 'true'::jsonb),
    ('feature.loyalty', 'true'::jsonb),
    ('feature.special_requests', 'true'::jsonb)
ON CONFLICT (key) DO NOTHING;

CREATE TABLE idempotency_keys (
    key TEXT PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
    endpoint VARCHAR(200) NOT NULL,
    response JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT now(),
    expires_at TIMESTAMP NOT NULL DEFAULT now() + interval '24 hours'
);

CREATE INDEX idx_idempotency_expires ON idempotency_keys(expires_at);

COMMIT;

-- ===== 016_demo_rooms.sql =====
-- =====================================================================================
--  SunStay: 48 демонстрационных номеров
-- =====================================================================================

BEGIN;

-- Стандарт: 20 номеров (110–129), этажи 1–2
INSERT INTO rooms (room_number, room_type_id, status_id, floor)
SELECT '1' || lpad(i::text, 2, '0'), 1, 6, CASE WHEN i <= 19 THEN 1 ELSE 2 END
FROM generate_series(10, 29) AS i
ON CONFLICT (room_number) DO NOTHING;

-- Комфорт: 20 номеров (210–229), этажи 2–3
INSERT INTO rooms (room_number, room_type_id, status_id, floor)
SELECT '2' || lpad(i::text, 2, '0'), 2, 6, CASE WHEN i <= 19 THEN 2 ELSE 3 END
FROM generate_series(10, 29) AS i
ON CONFLICT (room_number) DO NOTHING;

-- Люкс: 8 номеров (310–317), этаж 3–4
INSERT INTO rooms (room_number, room_type_id, status_id, floor)
SELECT '3' || lpad(i::text, 2, '0'), 3, 6, CASE WHEN i <= 14 THEN 3 ELSE 4 END
FROM generate_series(10, 17) AS i
ON CONFLICT (room_number) DO NOTHING;

COMMIT;
