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
