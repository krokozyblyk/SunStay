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
