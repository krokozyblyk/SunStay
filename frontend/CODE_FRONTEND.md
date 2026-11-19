# SunStay — текст клиентской части

> Сгенерировано: 18.11.2026 14:27

Полные листинги React/TypeScript-приложения, дизайн-токенов, конфигурации Vite/Tailwind, Nginx и smoke-теста. Файл является приложением к проекту и не вставляется в пояснительную записку целиком.

## Состав

- `frontend/package.json`
- `frontend/vite.config.ts`
- `frontend/tailwind.config.js`
- `frontend/postcss.config.js`
- `frontend/index.html`
- `frontend/nginx.conf`
- `frontend/Dockerfile`
- `frontend/src/App.tsx`
- `frontend/src/components/Layout.tsx`
- `frontend/src/components/ui.tsx`
- `frontend/src/index.css`
- `frontend/src/lib/api.ts`
- `frontend/src/lib/auth.tsx`
- `frontend/src/lib/i18n.tsx`
- `frontend/src/lib/theme.tsx`
- `frontend/src/lib/utils.ts`
- `frontend/src/main.tsx`
- `frontend/src/pages/AdminPages.tsx`
- `frontend/src/pages/GuestPages.tsx`
- `frontend/src/pages/ManagerPages.tsx`
- `frontend/src/pages/OperationsPages.tsx`
- `frontend/src/pages/PublicPages.tsx`
- `frontend/src/pages/ReportsPage.tsx`
- `frontend/scripts/capture_diagrams.mjs`
- `frontend/scripts/smoke.mjs`

## `frontend/package.json`

```json
{
  "name": "sunstay-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "@fontsource/manrope": "^5.1.0",
    "@fontsource/playfair-display": "^5.1.0",
    "@tanstack/react-query": "^5.62.11",
    "axios": "^1.7.9",
    "clsx": "^2.1.1",
    "html2canvas": "^1.4.1",
    "lucide-react": "^0.468.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.28.1",
    "recharts": "^2.15.0",
    "tailwind-merge": "^2.6.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.18",
    "@types/react-dom": "^18.3.5",
    "@vitejs/plugin-react": "^4.3.4",
    "autoprefixer": "^10.4.20",
    "playwright": "^1.65.1",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.17",
    "typescript": "^5.7.2",
    "vite": "^6.0.7"
  }
}

```

## `frontend/vite.config.ts`

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
      "/analytics": {
        target: "http://localhost:8001",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/analytics/, ""),
      },
    },
  },
});

```

## `frontend/tailwind.config.js`

```text
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "rgb(var(--canvas-rgb) / <alpha-value>)",
        surface: "rgb(var(--surface-rgb) / <alpha-value>)",
        surface2: "rgb(var(--surface2-rgb) / <alpha-value>)",
        ink: "rgb(var(--ink-rgb) / <alpha-value>)",
        muted: "rgb(var(--muted-rgb) / <alpha-value>)",
        forest: "rgb(var(--forest-rgb) / <alpha-value>)",
        forestDark: "rgb(var(--forestDark-rgb) / <alpha-value>)",
        terracotta: "rgb(var(--terracotta-rgb) / <alpha-value>)",
        amber: "rgb(var(--amber-rgb) / <alpha-value>)",
        sage: "rgb(var(--sage-rgb) / <alpha-value>)",
        success: "rgb(var(--success-rgb) / <alpha-value>)",
        warning: "rgb(var(--warning-rgb) / <alpha-value>)",
        danger: "rgb(var(--danger-rgb) / <alpha-value>)",
        info: "rgb(var(--info-rgb) / <alpha-value>)",
        line: "rgb(var(--border-rgb) / <alpha-value>)",
        tableHeader: "rgb(var(--tableHeader-rgb) / <alpha-value>)",
        rowHover: "rgb(var(--rowHover-rgb) / <alpha-value>)",
        inputBg: "rgb(var(--inputBg-rgb) / <alpha-value>)",
      },
      fontFamily: {
        display: ["Playfair Display", "Georgia", "serif"],
        sans: ["Manrope", "system-ui", "sans-serif"],
      },
      borderRadius: {
        lg: "1rem",
        xl: "1.25rem",
        "2xl": "1.5rem",
      },
      boxShadow: {
        soft: "0 8px 24px -4px rgba(18, 59, 54, 0.08), 0 2px 6px -1px rgba(18, 59, 54, 0.04)",
        float: "0 24px 48px -12px rgba(18, 59, 54, 0.16)",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0", transform: "translateY(6px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "slide-in": {
          from: { opacity: "0", transform: "translateX(16px)" },
          to: { opacity: "1", transform: "translateX(0)" },
        },
      },
      animation: {
        "fade-in": "fade-in 220ms ease-out",
        "slide-in": "slide-in 240ms ease-out",
      },
    },
  },
  plugins: [],
};

```

## `frontend/postcss.config.js`

```text
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};

```

## `frontend/index.html`

```html
<!doctype html>
<html lang="ru">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="theme-color" content="#F7F3EC" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <title>SunStay — управление отелем</title>
  </head>
  <body>
    <script>
      (function () {
        try {
          var theme = localStorage.getItem("sunstay_theme") || "light";
          var dark = theme === "dark" || (theme === "system" && window.matchMedia("(prefers-color-scheme: dark)").matches);
          document.documentElement.classList.toggle("dark", dark);
          document.documentElement.dataset.theme = dark ? "dark" : "light";
        } catch (e) {}
      })();
    </script>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>

```

## `frontend/nginx.conf`

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;
    client_max_body_size 10m;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript application/xml image/svg+xml;

    location /api/ {
        proxy_pass http://api:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /analytics/ {
        proxy_pass http://analytics:8001/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}

```

## `frontend/Dockerfile`

```dockerfile
FROM node:24-alpine AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

```

## `frontend/src/App.tsx`

```tsx
import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell, PublicLayout, RequireAuth, RequireRole } from "./components/Layout";
import { LandingPage, SearchPage, CheckoutPage, ConfirmationPage, LoginPage } from "./pages/PublicPages";
import {
  GuestBookingDetailPage,
  GuestBookingsPage,
  GuestDashboardPage,
  GuestInvoicesPage,
  GuestProfilePage,
  GuestServicesPage,
} from "./pages/GuestPages";
import {
  BookingDetailPage,
  BookingsRegistryPage,
  FolioPaymentsPage,
  ManagerDashboardPage,
  RoomGridPage,
} from "./pages/ManagerPages";
import { ReportsPage } from "./pages/ReportsPage";
import { ConsumablesPage, HousekeepingBoardPage, MaintenancePage } from "./pages/OperationsPages";
import {
  AdminAuditPage,
  AdminBackupsPage,
  AdminDirectoriesPage,
  AdminSettingsPage,
  AdminUsersPage,
  EmployeesPage,
} from "./pages/AdminPages";

const STAFF = ["MANAGER", "HOUSEKEEPING", "HOTEL_MANAGER", "DB_ADMIN"];
const MANAGERS = ["MANAGER", "HOTEL_MANAGER", "DB_ADMIN"];

export default function App() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path="/" element={<LandingPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/checkout" element={<CheckoutPage />} />
        <Route path="/confirmation" element={<ConfirmationPage />} />
      </Route>

      <Route path="/login" element={<LoginPage />} />

      <Route
        element={
          <RequireAuth>
            <RequireRole roles={STAFF}>
              <AppShell />
            </RequireRole>
          </RequireAuth>
        }
      >
        <Route path="/app" element={<RequireRole roles={MANAGERS}><ManagerDashboardPage /></RequireRole>} />
        <Route path="/app/room-grid" element={<RequireRole roles={MANAGERS}><RoomGridPage /></RequireRole>} />
        <Route path="/app/bookings" element={<RequireRole roles={MANAGERS}><BookingsRegistryPage /></RequireRole>} />
        <Route path="/app/bookings/:id" element={<RequireRole roles={MANAGERS}><BookingDetailPage /></RequireRole>} />
        <Route path="/app/folios" element={<RequireRole roles={MANAGERS}><FolioPaymentsPage /></RequireRole>} />
        <Route path="/app/reports" element={<RequireRole roles={MANAGERS}><ReportsPage /></RequireRole>} />
        <Route path="/app/housekeeping" element={<RequireRole roles={STAFF}><HousekeepingBoardPage /></RequireRole>} />
        <Route path="/app/maintenance" element={<RequireRole roles={STAFF}><MaintenancePage /></RequireRole>} />
        <Route path="/app/consumables" element={<RequireRole roles={["HOUSEKEEPING", "DB_ADMIN", "HOTEL_MANAGER"]}><ConsumablesPage /></RequireRole>} />
        <Route path="/app/admin/users" element={<RequireRole roles={["DB_ADMIN"]}><AdminUsersPage /></RequireRole>} />
        <Route path="/app/employees" element={<RequireRole roles={["HOTEL_MANAGER", "DB_ADMIN"]}><EmployeesPage /></RequireRole>} />
        <Route path="/app/admin/directories" element={<RequireRole roles={["HOTEL_MANAGER", "DB_ADMIN"]}><AdminDirectoriesPage /></RequireRole>} />
        <Route path="/app/admin/audit" element={<RequireRole roles={["HOTEL_MANAGER", "DB_ADMIN"]}><AdminAuditPage /></RequireRole>} />
        <Route path="/app/admin/backups" element={<RequireRole roles={["DB_ADMIN"]}><AdminBackupsPage /></RequireRole>} />
        <Route path="/app/admin/settings" element={<RequireRole roles={["DB_ADMIN"]}><AdminSettingsPage /></RequireRole>} />
      </Route>

      <Route
        path="/me"
        element={
          <RequireAuth>
            <RequireRole roles={["GUEST"]}>
              <AppShell />
            </RequireRole>
          </RequireAuth>
        }
      >
        <Route index element={<GuestDashboardPage />} />
        <Route path="bookings" element={<GuestBookingsPage />} />
        <Route path="bookings/:id" element={<GuestBookingDetailPage />} />
        <Route path="invoices" element={<GuestInvoicesPage />} />
        <Route path="services" element={<GuestServicesPage />} />
        <Route path="profile" element={<GuestProfilePage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

```

## `frontend/src/components/Layout.tsx`

```tsx
﻿import {
  BarChart3,
  BookOpen,
  CalendarDays,
  CircleHelp,
  DatabaseBackup,
  Grid3X3,
  Home,
  Languages,
  LayoutDashboard,
  LogOut,
  Menu,
  Moon,
  Package,
  ReceiptText,
  Settings,
  ShieldCheck,
  Sparkles,
  Sun,
  UserRound,
  Users,
  Wrench,
} from "lucide-react";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link, NavLink, Navigate, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth, type User } from "../lib/auth";
import { useI18n } from "../lib/i18n";
import { useTheme } from "../lib/theme";
import { cn, ROLE_LABELS } from "../lib/utils";
import { Avatar, Button, Modal } from "./ui";

export function homeForRole(user: User | null) {
  if (!user) return "/login";
  if (user.role_code === "GUEST") return "/me";
  if (user.role_code === "HOUSEKEEPING") return "/app/housekeeping";
  return "/app";
}

export function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="flex min-h-screen items-center justify-center text-muted">Загрузка…</div>;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export function RequireRole({ roles, children }: { roles: string[]; children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="flex min-h-screen items-center justify-center text-muted">Загрузка…</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (!roles.includes(user.role_code)) return <Navigate to={homeForRole(user)} replace />;
  return <>{children}</>;
}

export function ThemeToggle({ compact = false }: { compact?: boolean }) {
  const { resolvedTheme, toggleTheme } = useTheme();
  return (
    <button
      onClick={toggleTheme}
      className={cn(
        "inline-flex items-center justify-center rounded-xl border border-line bg-surface text-muted transition hover:text-ink",
        compact ? "h-9 w-9" : "h-10 gap-2 px-3",
      )}
      title="Переключить тему"
    >
      {resolvedTheme === "dark" ? <Sun size={17} /> : <Moon size={17} />}
      {!compact && <span className="text-xs font-semibold">{resolvedTheme === "dark" ? "Светлая" : "Тёмная"}</span>}
    </button>
  );
}

export function LanguageToggle({ compact = false }: { compact?: boolean }) {
  const { lang, toggleLang } = useI18n();
  return (
    <button
      onClick={toggleLang}
      className={cn(
        "inline-flex items-center justify-center rounded-xl border border-line bg-surface text-muted transition hover:text-ink",
        compact ? "h-9 w-9" : "h-10 gap-2 px-3",
      )}
      title="RU / EN"
    >
      <Languages size={17} />
      {!compact && <span className="text-xs font-semibold">{lang.toUpperCase()}</span>}
    </button>
  );
}

function Brand({ compact = false }: { compact?: boolean }) {
  return (
    <Link to="/" className="flex items-center gap-2.5">
      <span className="flex h-9 w-9 items-center justify-center rounded-2xl bg-terracotta/15 text-terracotta">
        <Sun size={18} />
      </span>
      {!compact && (
        <span className="font-display text-xl font-semibold tracking-tight text-ink">
          Sun<span className="text-terracotta">Stay</span>
        </span>
      )}
    </Link>
  );
}

export function PublicLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 border-b border-line/70 bg-canvas/90 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-[1240px] items-center justify-between gap-4 px-4 md:px-6">
          <Brand />
          <nav className="hidden items-center gap-6 text-sm font-medium text-muted md:flex">
            <Link to="/" className="hover:text-ink">Номера</Link>
            <Link to="/search" className="hover:text-ink">Бронирование</Link>
          </nav>
          <div className="flex items-center gap-2">
            <LanguageToggle compact />
            <ThemeToggle compact />
            {user ? (
              <div className="flex items-center gap-2">
                <Link
                  to={homeForRole(user)}
                  className="hidden items-center gap-2 rounded-xl border border-line bg-surface px-3 py-2 text-sm font-semibold text-ink sm:flex"
                >
                  <Avatar name={user.full_name} className="h-7 w-7 text-[10px]" />
                  {user.role_code === "GUEST" ? "Личный кабинет" : "Панель"}
                </Link>
                <Button variant="ghost" size="sm" onClick={() => logout().then(() => navigate("/"))}>
                  <LogOut size={15} /> Выйти
                </Button>
              </div>
            ) : (
              <>
                <Link to="/login" className="hidden text-sm font-semibold text-ink hover:text-terracotta sm:block">
                  Войти
                </Link>
                <Link to="/search" className="btn-primary btn-sm">Забронировать</Link>
              </>
            )}
          </div>
        </div>
      </header>
      <Outlet />
      <footer className="border-t border-line bg-surface">
        <div className="mx-auto flex max-w-[1240px] flex-col gap-4 px-4 py-8 text-sm text-muted md:flex-row md:items-center md:justify-between md:px-6">
          <div>
            <p className="font-display text-lg font-semibold text-ink">SunStay</p>
            <p className="mt-1">Бутик-отель · Санкт-Петербург, набережная реки Мойки, 12</p>
          </div>
          <div className="flex flex-wrap gap-5">
            <span>+7 (812) 490-70-00</span>
            <span>welcome@sunstay-hotel.ru</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

type NavItem = { to: string; label: string; icon: ReactNode; end?: boolean };

function navForRole(role: string, t: (key: string) => string): Array<{ group: string; items: NavItem[] }> {
  const dashboard = { to: "/app", label: t("dashboard"), icon: <LayoutDashboard size={18} />, end: true };
  const grid = { to: "/app/room-grid", label: t("roomGrid"), icon: <Grid3X3 size={18} /> };
  const bookings = { to: "/app/bookings", label: t("bookings"), icon: <CalendarDays size={18} /> };
  const folios = { to: "/app/folios", label: t("folios"), icon: <ReceiptText size={18} /> };
  const reports = { to: "/app/reports", label: t("reports"), icon: <BarChart3 size={18} /> };
  const hk = { to: "/app/housekeeping", label: t("housekeeping"), icon: <Sparkles size={18} /> };
  const maintenance = { to: "/app/maintenance", label: t("maintenance"), icon: <Wrench size={18} /> };
  const consumables = { to: "/app/consumables", label: t("consumables"), icon: <Package size={18} /> };
  const users = { to: "/app/admin/users", label: t("users"), icon: <Users size={18} /> };
  const directories = { to: "/app/admin/directories", label: t("directories"), icon: <BookOpen size={18} /> };
  const audit = { to: "/app/admin/audit", label: t("audit"), icon: <ShieldCheck size={18} /> };
  const backups = { to: "/app/admin/backups", label: t("backups"), icon: <DatabaseBackup size={18} /> };
  const settings = { to: "/app/admin/settings", label: t("settings"), icon: <Settings size={18} /> };
  const employees = { to: "/app/employees", label: t("employees"), icon: <Users size={18} /> };

  if (role === "GUEST") {
    return [
      {
        group: "Личный кабинет",
        items: [
          { to: "/me", label: t("guestHome"), icon: <Home size={18} />, end: true },
          { to: "/me/bookings", label: t("guestBookings"), icon: <CalendarDays size={18} /> },
          { to: "/me/services", label: t("guestServices"), icon: <Sparkles size={18} /> },
          { to: "/me/invoices", label: t("guestInvoices"), icon: <ReceiptText size={18} /> },
          { to: "/me/profile", label: t("guestProfile"), icon: <UserRound size={18} /> },
        ],
      },
    ];
  }
  if (role === "HOUSEKEEPING") {
    return [{ group: "Операции", items: [hk, maintenance, consumables] }];
  }
  if (role === "MANAGER") {
    return [{ group: "Управление", items: [dashboard, grid, bookings, folios, hk, reports] }];
  }
  if (role === "HOTEL_MANAGER") {
    return [
      { group: "Управление", items: [dashboard, reports, grid, bookings, folios, hk] },
      { group: "Администрирование", items: [directories, employees, audit] },
    ];
  }
  return [
    { group: "Управление", items: [dashboard, grid, bookings, folios, hk, reports] },
    { group: "Администрирование", items: [users, directories, audit, backups, maintenance, consumables, settings] },
  ];
}

function HotkeysModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const shortcuts = [
    ["?", "Открыть горячие клавиши"],
    ["N", "Новая бронь"],
    ["F", "Фокус на поиске"],
    ["G", "Шахматка"],
    ["B", "Бронирования"],
    ["R", "Отчёты"],
    ["T", "Переключить тему"],
    ["L", "Переключить язык"],
    ["Esc", "Закрыть окно"],
    ["Ctrl + Enter", "Сохранить / отправить форму"],
  ];
  return (
    <Modal open={open} title="Горячие клавиши" subtitle="Быстрые действия в интерфейсе SunStay" onClose={onClose}>
      <div className="space-y-2">
        {shortcuts.map(([key, label]) => (
          <div key={key} className="flex items-center justify-between gap-4 rounded-xl border border-line bg-surface2 px-3 py-2">
            <span className="text-sm text-muted">{label}</span>
            <kbd className="rounded-lg border border-line bg-surface px-2 py-1 font-mono text-xs font-semibold text-ink">{key}</kbd>
          </div>
        ))}
      </div>
    </Modal>
  );
}

export function AppShell() {
  const { user, logout } = useAuth();
  const { t, toggleLang } = useI18n();
  const { toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [hotkeysOpen, setHotkeysOpen] = useState(false);

  const groups = useMemo(() => navForRole(user?.role_code ?? "MANAGER", t), [user?.role_code, t]);
  const currentTitle = useMemo(() => {
    const all = groups.flatMap((group) => group.items);
    const match = all.find((item) => (item.end ? location.pathname === item.to : location.pathname.startsWith(item.to)));
    return match?.label ?? "SunStay";
  }, [groups, location.pathname]);

  useEffect(() => {
    const onHotkeys = () => setHotkeysOpen(true);
    window.addEventListener("sunstay:open-hotkeys", onHotkeys);
    return () => window.removeEventListener("sunstay:open-hotkeys", onHotkeys);
  }, []);

  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      const typing = target && ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName);
      if (typing || event.metaKey || event.altKey) return;
      const key = event.key.toLowerCase();
      if (event.key === "?") {
        event.preventDefault();
        setHotkeysOpen((value) => !value);
      } else if (key === "n" && user?.permissions.includes("bookings:create")) {
        navigate("/app/bookings?new=1");
      } else if (key === "f") {
        const input = document.getElementById("page-search") as HTMLInputElement | null;
        input?.focus();
      } else if (key === "g") {
        navigate("/app/room-grid");
      } else if (key === "b") {
        navigate("/app/bookings");
      } else if (key === "r") {
        navigate("/app/reports");
      } else if (key === "t") {
        toggleTheme();
      } else if (key === "l") {
        toggleLang();
      } else if (event.key === "Escape") {
        setMobileOpen(false);
        setHotkeysOpen(false);
      } else if (event.ctrlKey && event.key === "Enter") {
        event.preventDefault();
        const form = (document.activeElement as HTMLElement | null)?.closest("form") as HTMLFormElement | null;
        form?.requestSubmit();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [navigate, toggleLang, toggleTheme, user?.permissions]);

  if (!user) return <Navigate to="/login" replace />;

  const sidebar = (
    <aside className="flex h-full flex-col justify-between bg-forest p-4 text-white">
      <div className="space-y-6">
        <Link to={homeForRole(user)} className="flex items-center gap-2.5 px-1">
          <span className="flex h-9 w-9 items-center justify-center rounded-2xl bg-white/10 text-amber">
            <Sun size={18} />
          </span>
          <span className="font-display text-xl font-semibold tracking-tight">SunStay</span>
        </Link>
        <div className="flex items-center gap-3 rounded-xl bg-white/10 p-3">
          <Avatar name={user.full_name} className="bg-white/15 text-white" />
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold">{user.full_name}</p>
            <p className="truncate text-[11px] text-white/60">{ROLE_LABELS[user.role_code] ?? user.role_name}</p>
          </div>
        </div>
        <nav className="space-y-5">
          {groups.map((group) => (
            <div key={group.group}>
              <p className="mb-2 px-3 text-[10px] font-bold uppercase tracking-[0.12em] text-white/45">{group.group}</p>
              <div className="space-y-1">
                {group.items.map((item) => (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.end}
                    onClick={() => setMobileOpen(false)}
                    className={({ isActive }) => cn("sidebar-link", isActive && "active")}
                  >
                    {item.icon}
                    <span>{item.label}</span>
                  </NavLink>
                ))}
              </div>
            </div>
          ))}
        </nav>
      </div>
      <button
        onClick={() => logout().then(() => navigate("/"))}
        className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-white/65 transition hover:bg-white/10 hover:text-white"
      >
        <LogOut size={18} /> {t("logout")}
      </button>
    </aside>
  );

  return (
    <div className="min-h-screen bg-canvas">
      <div className="fixed inset-y-0 left-0 z-50 hidden w-[264px] lg:block">{sidebar}</div>
      {mobileOpen && (
        <div className="fixed inset-0 z-[90] bg-black/40 lg:hidden" onClick={() => setMobileOpen(false)}>
          <div className="h-full w-[280px]" onClick={(event) => event.stopPropagation()}>
            {sidebar}
          </div>
        </div>
      )}
      <div className="lg:pl-[264px]">
        <header className="sticky top-0 z-40 flex h-16 items-center justify-between gap-3 border-b border-line bg-canvas/85 px-4 backdrop-blur-xl md:px-6">
          <div className="flex items-center gap-3">
            <button className="rounded-xl border border-line bg-surface p-2 text-muted lg:hidden" onClick={() => setMobileOpen(true)}>
              <Menu size={18} />
            </button>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-muted">
                SunStay · {user.role_code === "GUEST" ? "личный кабинет" : "рабочая область"}
              </p>
              <p className="font-display text-lg font-semibold leading-tight text-ink">{currentTitle}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="hidden text-xs text-muted xl:block">
              {new Intl.DateTimeFormat("ru-RU", { day: "2-digit", month: "long", year: "numeric" }).format(new Date())}
            </span>
            <button
              onClick={() => setHotkeysOpen(true)}
              className="hidden h-9 w-9 items-center justify-center rounded-xl border border-line bg-surface text-muted hover:text-ink sm:flex"
              title="Горячие клавиши (?)"
            >
              <CircleHelp size={17} />
            </button>
            <LanguageToggle compact />
            <ThemeToggle compact />
            <div className="hidden items-center gap-2 rounded-xl border border-line bg-surface px-2.5 py-1.5 sm:flex">
              <Avatar name={user.full_name} className="h-7 w-7 text-[10px]" />
              <div className="max-w-[140px]">
                <p className="truncate text-xs font-semibold text-ink">{user.full_name}</p>
                <p className="truncate text-[10px] text-muted">{ROLE_LABELS[user.role_code] ?? user.role_name}</p>
              </div>
            </div>
          </div>
        </header>
        <main className="mx-auto max-w-[1500px] animate-fade-in px-4 py-6 md:px-6 md:py-8">
          <Outlet />
        </main>
      </div>
      <HotkeysModal open={hotkeysOpen} onClose={() => setHotkeysOpen(false)} />
    </div>
  );
}

```

## `frontend/src/components/ui.tsx`

```tsx
import {
  AlertCircle,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Inbox,
  Loader2,
  Lock,
  X,
} from "lucide-react";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ButtonHTMLAttributes,
  type InputHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
} from "react";
import { cn, initials, statusClass, statusLabel } from "../lib/utils";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
type ButtonSize = "sm" | "md";

export function Button({
  variant = "primary",
  size = "md",
  className,
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant; size?: ButtonSize }) {
  const variants: Record<ButtonVariant, string> = {
    primary: "btn-primary",
    secondary: "btn-secondary",
    ghost: "btn-ghost",
    danger: "btn-danger",
  };
  return (
    <button
      className={cn(variants[variant], size === "sm" && "btn-sm", className)}
      {...props}
    >
      {children}
    </button>
  );
}

export function Card({ className, children }: { className?: string; children: ReactNode }) {
  return <div className={cn("card p-5", className)}>{children}</div>;
}

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div>
        <h1 className="page-title">{title}</h1>
        {subtitle && <p className="page-subtitle max-w-3xl">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

export function Badge({
  children,
  tone = "neutral",
  className,
}: {
  children: ReactNode;
  tone?: "neutral" | "success" | "warning" | "danger" | "info" | "forest";
  className?: string;
}) {
  const tones = {
    neutral: "bg-surface2 text-muted",
    success: "bg-emerald-500/12 text-emerald-700 dark:text-emerald-300",
    warning: "bg-amber-500/14 text-amber-700 dark:text-amber-300",
    danger: "bg-rose-500/12 text-rose-700 dark:text-rose-300",
    info: "bg-sky-500/12 text-sky-700 dark:text-sky-300",
    forest: "bg-forest/10 text-forest dark:bg-white/10 dark:text-ink",
  };
  return <span className={cn("badge", tones[tone], className)}>{children}</span>;
}

export function StatusPill({ status }: { status?: string | null }) {
  return <span className={cn("status-pill", statusClass(status))}>{statusLabel(status)}</span>;
}

export function KpiCard({
  label,
  value,
  hint,
  icon,
  tone = "forest",
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  icon?: ReactNode;
  tone?: "forest" | "terracotta" | "amber" | "sage";
}) {
  const tones = {
    forest: "bg-forest/10 text-forest dark:bg-white/10 dark:text-ink",
    terracotta: "bg-terracotta/12 text-terracotta",
    amber: "bg-amber/15 text-amber-700 dark:text-amber-300",
    sage: "bg-sage/20 text-forest dark:text-sage",
  };
  return (
    <Card className="flex items-start justify-between gap-4">
      <div>
        <p className="text-[11px] font-bold uppercase tracking-[0.08em] text-muted">{label}</p>
        <p className="kpi-value mt-2">{value}</p>
        {hint && <p className="mt-1 text-xs text-muted">{hint}</p>}
      </div>
      {icon && <span className={cn("flex h-11 w-11 items-center justify-center rounded-2xl", tones[tone])}>{icon}</span>}
    </Card>
  );
}

export function Avatar({ name, className }: { name?: string | null; className?: string }) {
  return (
    <span
      className={cn(
        "flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-forest text-xs font-bold text-white dark:bg-surface2 dark:text-ink",
        className,
      )}
    >
      {initials(name)}
    </span>
  );
}

export function Input({
  label,
  className,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { label?: string }) {
  return (
    <label className="flex flex-col gap-1.5">
      {label && <span className="label">{label}</span>}
      <input className={cn("input", className)} {...props} />
    </label>
  );
}

export function Select({
  label,
  className,
  children,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement> & { label?: string }) {
  return (
    <label className="flex flex-col gap-1.5">
      {label && <span className="label">{label}</span>}
      <select className={cn("input", className)} {...props}>
        {children}
      </select>
    </label>
  );
}

export function Textarea({
  label,
  className,
  ...props
}: TextareaHTMLAttributes<HTMLTextAreaElement> & { label?: string }) {
  return (
    <label className="flex flex-col gap-1.5">
      {label && <span className="label">{label}</span>}
      <textarea className={cn("textarea", className)} {...props} />
    </label>
  );
}

export function Modal({
  open,
  title,
  subtitle,
  onClose,
  children,
  footer,
  size = "md",
}: {
  open: boolean;
  title: string;
  subtitle?: string;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
  size?: "sm" | "md" | "lg";
}) {
  useEffect(() => {
    if (!open) return;
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!open) return null;
  const widths = { sm: "max-w-md", md: "max-w-2xl", lg: "max-w-4xl" };
  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm">
      <div className={cn("card w-full animate-fade-in overflow-hidden", widths[size])}>
        <div className="flex items-start justify-between gap-4 border-b border-line px-5 py-4">
          <div>
            <h2 className="font-display text-xl font-semibold text-ink">{title}</h2>
            {subtitle && <p className="mt-1 text-sm text-muted">{subtitle}</p>}
          </div>
          <button className="rounded-lg p-1.5 text-muted hover:bg-surface2 hover:text-ink" onClick={onClose}>
            <X size={18} />
          </button>
        </div>
        <div className="max-h-[70vh] overflow-y-auto px-5 py-4">{children}</div>
        {footer && <div className="flex flex-wrap justify-end gap-2 border-t border-line px-5 py-4">{footer}</div>}
      </div>
    </div>
  );
}

export function Drawer({
  open,
  title,
  subtitle,
  onClose,
  children,
  footer,
}: {
  open: boolean;
  title: string;
  subtitle?: string;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
}) {
  useEffect(() => {
    if (!open) return;
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-[100] flex justify-end bg-black/35 backdrop-blur-sm">
      <div className="h-full w-full max-w-[520px] animate-slide-in border-l border-line bg-surface shadow-float">
        <div className="flex items-start justify-between gap-4 border-b border-line px-6 py-5">
          <div>
            <h2 className="font-display text-xl font-semibold text-ink">{title}</h2>
            {subtitle && <p className="mt-1 text-sm text-muted">{subtitle}</p>}
          </div>
          <button className="rounded-lg p-1.5 text-muted hover:bg-surface2 hover:text-ink" onClick={onClose}>
            <X size={18} />
          </button>
        </div>
        <div className="h-[calc(100%-145px)] overflow-y-auto px-6 py-5">{children}</div>
        {footer && <div className="flex justify-end gap-2 border-t border-line px-6 py-4">{footer}</div>}
      </div>
    </div>
  );
}

export function Tabs({
  items,
  value,
  onChange,
  className,
}: {
  items: Array<{ value: string; label: string; count?: number }>;
  value: string;
  onChange: (value: string) => void;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-wrap gap-1 rounded-xl border border-line bg-surface2 p-1", className)}>
      {items.map((item) => (
        <button
          key={item.value}
          onClick={() => onChange(item.value)}
          className={cn(
            "rounded-lg px-3 py-2 text-sm font-semibold transition-colors",
            value === item.value
              ? "bg-surface text-ink shadow-sm"
              : "text-muted hover:text-ink",
          )}
        >
          {item.label}
          {typeof item.count === "number" && (
            <span className="ml-1 text-xs text-muted">{item.count}</span>
          )}
        </button>
      ))}
    </div>
  );
}

export function Pagination({
  page,
  pageSize,
  total,
  onPageChange,
}: {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
}) {
  const pages = Math.max(1, Math.ceil(total / pageSize));
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-t border-line px-4 py-3 text-sm text-muted">
      <span>
        Всего: {total} · Страница {page} из {pages}
      </span>
      <div className="flex items-center gap-1">
        <Button variant="ghost" size="sm" disabled={page <= 1} onClick={() => onPageChange(page - 1)}>
          <ChevronLeft size={15} /> Назад
        </Button>
        <Button variant="ghost" size="sm" disabled={page >= pages} onClick={() => onPageChange(page + 1)}>
          Вперёд <ChevronRight size={15} />
        </Button>
      </div>
    </div>
  );
}

export function EmptyState({
  title = "Нет данных",
  description,
  action,
}: {
  title?: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-line px-6 py-12 text-center">
      <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-surface2 text-muted">
        <Inbox size={22} />
      </span>
      <div>
        <p className="font-semibold text-ink">{title}</p>
        {description && <p className="mt-1 text-sm text-muted">{description}</p>}
      </div>
      {action}
    </div>
  );
}

export function Spinner({ label = "Загрузка…" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 px-6 py-12 text-sm text-muted">
      <Loader2 className="animate-spin" size={18} /> {label}
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger">
      <AlertCircle size={18} /> {message}
    </div>
  );
}

type Toast = { id: number; message: string; tone: "success" | "error" | "info" };
type ToastContextValue = { toast: (message: string, tone?: Toast["tone"]) => void };
const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const toast = useCallback((message: string, tone: Toast["tone"] = "info") => {
    const id = Date.now() + Math.random();
    setToasts((current) => [...current, { id, message, tone }]);
    window.setTimeout(() => setToasts((current) => current.filter((item) => item.id !== id)), 4200);
  }, []);
  const value = useMemo(() => ({ toast }), [toast]);
  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="fixed bottom-5 right-5 z-[200] flex w-[min(360px,calc(100vw-2.5rem))] flex-col gap-2">
        {toasts.map((item) => (
          <div
            key={item.id}
            className={cn(
              "flex items-start gap-2 rounded-xl border px-4 py-3 text-sm shadow-float",
              item.tone === "success" && "border-success/30 bg-success/10 text-success",
              item.tone === "error" && "border-danger/30 bg-danger/10 text-danger",
              item.tone === "info" && "border-line bg-surface text-ink",
            )}
          >
            {item.tone === "success" ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
            <span>{item.message}</span>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error("useToast must be used inside ToastProvider");
  return context;
}

export function SensitiveValue({ value, className }: { value?: string | null; className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-1 text-xs text-muted", className)} title="Скрыто">
      <Lock size={11} />
      <span className="select-none blur-[2px]">{value || "—"}</span>
    </span>
  );
}

```

## `frontend/src/index.css`

```css
@import "@fontsource/manrope/400.css";
@import "@fontsource/manrope/500.css";
@import "@fontsource/manrope/600.css";
@import "@fontsource/manrope/700.css";
@import "@fontsource/playfair-display/500.css";
@import "@fontsource/playfair-display/600.css";

@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --canvas: #f7f3ec;
  --surface: #ffffff;
  --surface-2: #fbf8f3;
  --ink: #1e2420;
  --muted: #6e746d;
  --forest: #123b36;
  --forest-dark: #0e2f2b;
  --terracotta: #c96f4a;
  --amber: #e3a857;
  --sage: #9db5a4;
  --success: #2f7d5d;
  --warning: #c58a2e;
  --danger: #b8504e;
  --info: #3d6f8e;
  --border: #e6ded2;
  --table-header: #f3eee6;
  --row-hover: #fbf8f3;
  --input-bg: #ffffff;

  --canvas-rgb: 247 243 236;
  --surface-rgb: 255 255 255;
  --surface2-rgb: 251 248 243;
  --ink-rgb: 30 36 32;
  --muted-rgb: 110 116 109;
  --forest-rgb: 18 59 54;
  --forestDark-rgb: 14 47 43;
  --terracotta-rgb: 201 111 74;
  --amber-rgb: 227 168 87;
  --sage-rgb: 157 181 164;
  --success-rgb: 47 125 93;
  --warning-rgb: 197 138 46;
  --danger-rgb: 184 80 78;
  --info-rgb: 61 111 142;
  --border-rgb: 230 222 210;
  --tableHeader-rgb: 243 238 230;
  --rowHover-rgb: 251 248 243;
  --inputBg-rgb: 255 255 255;
  color-scheme: light;
}

.dark {
  --canvas: #0e1311;
  --surface: #151c18;
  --surface-2: #1b241f;
  --ink: #f3efe7;
  --muted: #a7b0a8;
  --forest: #0a1f1b;
  --forest-dark: #071714;
  --terracotta: #d9825e;
  --amber: #e0a24a;
  --sage: #8faf9b;
  --success: #4caf82;
  --warning: #e0a24a;
  --danger: #d46a67;
  --info: #6fa3c2;
  --border: #2a342e;
  --table-header: #1b241f;
  --row-hover: #1f2a24;
  --input-bg: #121915;

  --canvas-rgb: 14 19 17;
  --surface-rgb: 21 28 24;
  --surface2-rgb: 27 36 31;
  --ink-rgb: 243 239 231;
  --muted-rgb: 167 176 168;
  --forest-rgb: 10 31 27;
  --forestDark-rgb: 7 23 20;
  --terracotta-rgb: 217 130 94;
  --amber-rgb: 224 162 74;
  --sage-rgb: 143 175 155;
  --success-rgb: 76 175 130;
  --warning-rgb: 224 162 74;
  --danger-rgb: 212 106 103;
  --info-rgb: 111 163 194;
  --border-rgb: 42 52 46;
  --tableHeader-rgb: 27 36 31;
  --rowHover-rgb: 31 42 36;
  --inputBg-rgb: 18 25 21;
  color-scheme: dark;
}

@layer base {
  html,
  body,
  #root {
    min-height: 100%;
  }

  body {
    @apply bg-canvas text-ink font-sans antialiased;
    background-image:
      radial-gradient(circle at 85% -10%, rgba(201, 111, 74, 0.08), transparent 34rem),
      radial-gradient(circle at 10% 0%, rgba(157, 181, 164, 0.12), transparent 30rem);
  }

  ::selection {
    @apply bg-terracotta/25;
  }

  ::-webkit-scrollbar {
    width: 10px;
    height: 10px;
  }

  ::-webkit-scrollbar-thumb {
    @apply rounded-full bg-line;
  }
}

@layer components {
  .card {
    @apply rounded-2xl border border-line bg-surface shadow-soft;
  }

  .card-soft {
    @apply rounded-2xl border border-line bg-surface2;
  }

  .page-title {
    @apply font-display text-3xl font-semibold tracking-tight text-ink md:text-4xl;
  }

  .page-subtitle {
    @apply mt-1 text-sm leading-6 text-muted;
  }

  .btn {
    @apply inline-flex min-h-10 items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-terracotta/40 disabled:cursor-not-allowed disabled:opacity-50;
  }

  .btn-primary {
    @apply btn bg-forest text-white hover:bg-forestDark active:scale-[0.98];
  }

  .dark .btn-primary {
    @apply bg-terracotta text-[#1a120e] hover:bg-[#e29270];
  }

  .btn-secondary {
    @apply btn border border-line bg-surface text-ink hover:bg-surface2;
  }

  .btn-ghost {
    @apply btn text-muted hover:bg-surface2 hover:text-ink;
  }

  .btn-danger {
    @apply btn bg-danger text-white hover:opacity-90;
  }

  .btn-sm {
    @apply min-h-8 rounded-lg px-3 py-1.5 text-xs;
  }

  .input {
    @apply h-10 w-full rounded-xl border border-line bg-inputBg px-3 text-sm text-ink placeholder:text-muted/70 focus:border-terracotta focus:outline-none focus:ring-2 focus:ring-terracotta/20;
  }

  .textarea {
    @apply min-h-24 w-full rounded-xl border border-line bg-inputBg px-3 py-2 text-sm text-ink placeholder:text-muted/70 focus:border-terracotta focus:outline-none focus:ring-2 focus:ring-terracotta/20;
  }

  .label {
    @apply text-[11px] font-bold uppercase tracking-[0.08em] text-muted;
  }

  .badge {
    @apply inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide;
  }

  .status-pill {
    @apply inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold;
  }

  .status-pill::before {
    content: "";
    @apply h-1.5 w-1.5 rounded-full bg-current;
  }

  .table-wrap {
    @apply overflow-x-auto rounded-2xl border border-line bg-surface;
  }

  .table-base {
    @apply w-full border-collapse text-left text-sm;
  }

  .table-base thead {
    @apply bg-tableHeader text-[11px] uppercase tracking-[0.08em] text-muted;
  }

  .table-base th {
    @apply whitespace-nowrap px-4 py-3 font-bold;
  }

  .table-base td {
    @apply border-t border-line px-4 py-3 align-middle;
  }

  .table-base tbody tr:hover {
    @apply bg-rowHover;
  }

  .sidebar-link {
    @apply flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-white/70 transition-all duration-150 hover:bg-white/10 hover:text-white;
  }

  .sidebar-link.active {
    @apply bg-white text-forest shadow-sm;
  }

  .dark .sidebar-link.active {
    @apply bg-surface2 text-ink;
  }

  .kpi-value {
    @apply font-display text-3xl font-semibold tabular-nums text-ink;
  }

  .divider {
    @apply h-px w-full bg-line;
  }

  .focus-ring {
    @apply focus:outline-none focus:ring-2 focus:ring-terracotta/40 focus:ring-offset-2 focus:ring-offset-canvas;
  }
}

```

## `frontend/src/lib/api.ts`

```typescript
import axios from "axios";

export const ACCESS_KEY = "sunstay_access_token";
export const REFRESH_KEY = "sunstay_refresh_token";
export const USER_KEY = "sunstay_user";

export const api = axios.create({
  baseURL: "/api",
  timeout: 30000,
});

export const analyticsApi = axios.create({
  baseURL: "/analytics/api",
  timeout: 30000,
});

for (const client of [api, analyticsApi]) {
  client.interceptors.request.use((config) => {
    const token = localStorage.getItem(ACCESS_KEY);
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });
}

export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((item) => item.msg ?? String(item)).join("; ");
    }
    if (error.message) return error.message;
  }
  return "Что-то пошло не так";
}

export async function downloadFile(
  client: typeof api,
  url: string,
  filename: string,
  params?: Record<string, unknown>,
) {
  const response = await client.get(url, {
    params,
    responseType: "blob",
  });
  const blobUrl = URL.createObjectURL(response.data);
  const link = document.createElement("a");
  link.href = blobUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(blobUrl);
}

```

## `frontend/src/lib/auth.tsx`

```tsx
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { ACCESS_KEY, REFRESH_KEY, USER_KEY, api } from "./api";
import { useI18n } from "./i18n";
import { useTheme, type Theme } from "./theme";

export type User = {
  user_id: number;
  role_id: number;
  role_name: string;
  role_code: string;
  full_name: string;
  email: string;
  phone?: string | null;
  guest_id?: number | null;
  permissions: string[];
};

export type UserSettings = {
  theme: Theme;
  language: "ru" | "en";
  date_format: string;
  number_format: string;
  page_size: number;
  saved_filters: Array<Record<string, unknown>>;
};

const DEFAULT_SETTINGS: UserSettings = {
  theme: "light",
  language: "ru",
  date_format: "dd.MM.yyyy",
  number_format: "space_comma",
  page_size: 25,
  saved_filters: [],
};

type AuthContextValue = {
  user: User | null;
  settings: UserSettings;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  register: (payload: Record<string, unknown>) => Promise<User>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  updateSettings: (patch: Partial<UserSettings>) => Promise<void>;
  hasPermission: (permission: string) => boolean;
  isStaff: boolean;
  isGuest: boolean;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const { setTheme } = useTheme();
  const { setLang } = useI18n();
  const [user, setUser] = useState<User | null>(() => {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as User;
    } catch {
      return null;
    }
  });
  const [settings, setSettings] = useState<UserSettings>(DEFAULT_SETTINGS);
  const [loading, setLoading] = useState(true);

  const applySettings = useCallback(
    (next: UserSettings) => {
      setSettings(next);
      setTheme(next.theme ?? "light");
      setLang(next.language === "en" ? "en" : "ru");
    },
    [setLang, setTheme],
  );

  const clearSession = useCallback(() => {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_KEY);
    setUser(null);
    setSettings(DEFAULT_SETTINGS);
  }, []);

  const loadMe = useCallback(async () => {
    const response = await api.get("/auth/me");
    const data = response.data;
    const nextSettings = { ...DEFAULT_SETTINGS, ...(data.settings ?? {}) } as UserSettings;
    setUser(data.user);
    localStorage.setItem(USER_KEY, JSON.stringify(data.user));
    applySettings(nextSettings);
  }, [applySettings]);

  const refreshUser = useCallback(async () => {
    if (!localStorage.getItem(ACCESS_KEY)) return;
    await loadMe();
  }, [loadMe]);

  useEffect(() => {
    let cancelled = false;
    async function bootstrap() {
      const access = localStorage.getItem(ACCESS_KEY);
      const refresh = localStorage.getItem(REFRESH_KEY);
      if (!access) {
        setLoading(false);
        return;
      }
      try {
        await loadMe();
      } catch {
        if (refresh) {
          try {
            const response = await api.post("/auth/refresh", { refresh_token: refresh });
            localStorage.setItem(ACCESS_KEY, response.data.access_token);
            localStorage.setItem(REFRESH_KEY, response.data.refresh_token);
            await loadMe();
          } catch {
            if (!cancelled) clearSession();
          }
        } else if (!cancelled) {
          clearSession();
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    bootstrap();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const response = await api.post("/auth/login", { email, password });
      localStorage.setItem(ACCESS_KEY, response.data.access_token);
      localStorage.setItem(REFRESH_KEY, response.data.refresh_token);
      localStorage.setItem(USER_KEY, JSON.stringify(response.data.user));
      setUser(response.data.user);
      await loadMe();
      return response.data.user as User;
    },
    [loadMe],
  );

  const register = useCallback(
    async (payload: Record<string, unknown>) => {
      const response = await api.post("/auth/register", payload);
      localStorage.setItem(ACCESS_KEY, response.data.access_token);
      localStorage.setItem(REFRESH_KEY, response.data.refresh_token);
      localStorage.setItem(USER_KEY, JSON.stringify(response.data.user));
      setUser(response.data.user);
      await loadMe();
      return response.data.user as User;
    },
    [loadMe],
  );

  const logout = useCallback(async () => {
    const refresh = localStorage.getItem(REFRESH_KEY);
    try {
      if (refresh) await api.post("/auth/logout", { refresh_token: refresh });
    } catch {
      // ignore
    } finally {
      clearSession();
    }
  }, [clearSession]);

  const updateSettings = useCallback(
    async (patch: Partial<UserSettings>) => {
      const next = { ...settings, ...patch };
      const response = await api.put("/settings", next);
      applySettings({ ...DEFAULT_SETTINGS, ...response.data });
    },
    [applySettings, settings],
  );

  const hasPermission = useCallback(
    (permission: string) => Boolean(user?.permissions?.includes(permission)),
    [user],
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      settings,
      loading,
      login,
      register,
      logout,
      refreshUser,
      updateSettings,
      hasPermission,
      isStaff: Boolean(user && user.role_code !== "GUEST"),
      isGuest: user?.role_code === "GUEST",
    }),
    [user, settings, loading, login, register, logout, refreshUser, updateSettings, hasPermission],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}

```

## `frontend/src/lib/i18n.tsx`

```tsx
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export type Lang = "ru" | "en";

const DICT: Record<Lang, Record<string, string>> = {
  ru: {
    dashboard: "Дашборд",
    roomGrid: "Шахматка",
    bookings: "Бронирования",
    folios: "Folio и платежи",
    reports: "Отчёты",
    housekeeping: "Хаускипинг",
    maintenance: "Техзаявки",
    consumables: "Расходники",
    users: "Пользователи и роли",
    directories: "Справочники",
    audit: "Аудит",
    backups: "Бэкапы",
    settings: "Настройки",
    employees: "Сотрудники",
    guestHome: "Главная",
    guestBookings: "Мои брони",
    guestServices: "Услуги",
    guestInvoices: "Счета",
    guestProfile: "Профиль",
    login: "Войти",
    logout: "Выйти",
    register: "Зарегистрироваться",
    book: "Забронировать",
    search: "Поиск",
    apply: "Применить",
    reset: "Сбросить",
    save: "Сохранить",
    cancel: "Отмена",
    close: "Закрыть",
    edit: "Редактировать",
    delete: "Удалить",
    add: "Добавить",
    details: "Подробнее",
    choose: "Выбрать",
    exportCsv: "Экспорт CSV",
    exportPng: "Экспорт PNG",
    downloadPdf: "Скачать PDF",
    confirm: "Подтвердить",
    checkIn: "Заселить",
    checkOut: "Выселить",
    move: "Перенести",
    openFolio: "Открыть folio",
    addPayment: "Добавить платёж",
    refund: "Возврат",
    closeFolio: "Закрыть счёт",
    importCsv: "Импорт CSV",
    createBackup: "Создать копию",
    restore: "Восстановить",
    newBooking: "Новая бронь",
    newTask: "Новое задание",
    newRequest: "Новая заявка",
    writeOff: "Списать",
    start: "Начать",
    complete: "Завершить",
    theme: "Тема",
    light: "Светлая",
    dark: "Тёмная",
    system: "Системная",
    language: "Язык",
    profile: "Профиль",
    dateFormat: "Формат даты",
    numberFormat: "Формат чисел",
    pageSize: "Размер страницы",
    savedFilters: "Сохранённые фильтры",
    hotkeys: "Горячие клавиши",
    saveFilter: "Сохранить фильтр",
    all: "Все",
    status: "Статус",
    actions: "Действия",
    guest: "Гость",
    room: "Номер",
    dates: "Даты",
    total: "Сумма",
    balance: "Баланс",
    charged: "Начислено",
    paid: "Оплачено",
    source: "Источник",
    nights: "ночей",
    loading: "Загрузка…",
    noData: "Нет данных",
    error: "Ошибка",
  },
  en: {
    dashboard: "Dashboard",
    roomGrid: "Room grid",
    bookings: "Bookings",
    folios: "Folio & payments",
    reports: "Reports",
    housekeeping: "Housekeeping",
    maintenance: "Maintenance",
    consumables: "Consumables",
    users: "Users & roles",
    directories: "Directories",
    audit: "Audit",
    backups: "Backups",
    settings: "Settings",
    employees: "Employees",
    guestHome: "Home",
    guestBookings: "My bookings",
    guestServices: "Services",
    guestInvoices: "Invoices",
    guestProfile: "Profile",
    login: "Sign in",
    logout: "Sign out",
    register: "Sign up",
    book: "Book",
    search: "Search",
    apply: "Apply",
    reset: "Reset",
    save: "Save",
    cancel: "Cancel",
    close: "Close",
    edit: "Edit",
    delete: "Delete",
    add: "Add",
    details: "Details",
    choose: "Choose",
    exportCsv: "Export CSV",
    exportPng: "Export PNG",
    downloadPdf: "Download PDF",
    confirm: "Confirm",
    checkIn: "Check in",
    checkOut: "Check out",
    move: "Move",
    openFolio: "Open folio",
    addPayment: "Add payment",
    refund: "Refund",
    closeFolio: "Close folio",
    importCsv: "Import CSV",
    createBackup: "Create backup",
    restore: "Restore",
    newBooking: "New booking",
    newTask: "New task",
    newRequest: "New request",
    writeOff: "Write off",
    start: "Start",
    complete: "Complete",
    theme: "Theme",
    light: "Light",
    dark: "Dark",
    system: "System",
    language: "Language",
    profile: "Profile",
    dateFormat: "Date format",
    numberFormat: "Number format",
    pageSize: "Page size",
    savedFilters: "Saved filters",
    hotkeys: "Hotkeys",
    saveFilter: "Save filter",
    all: "All",
    status: "Status",
    actions: "Actions",
    guest: "Guest",
    room: "Room",
    dates: "Dates",
    total: "Total",
    balance: "Balance",
    charged: "Charged",
    paid: "Paid",
    source: "Source",
    nights: "nights",
    loading: "Loading…",
    noData: "No data",
    error: "Error",
  },
};

type I18nContextValue = {
  lang: Lang;
  setLang: (lang: Lang) => void;
  toggleLang: () => void;
  t: (key: string) => string;
};

const I18nContext = createContext<I18nContextValue | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(() => {
    const saved = localStorage.getItem("sunstay_lang") as Lang | null;
    return saved ?? "ru";
  });

  useEffect(() => {
    localStorage.setItem("sunstay_lang", lang);
    document.documentElement.lang = lang;
  }, [lang]);

  const value = useMemo<I18nContextValue>(
    () => ({
      lang,
      setLang: setLangState,
      toggleLang: () => setLangState(lang === "ru" ? "en" : "ru"),
      t: (key: string) => DICT[lang][key] ?? DICT.ru[key] ?? key,
    }),
    [lang],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (!context) throw new Error("useI18n must be used inside I18nProvider");
  return context;
}

```

## `frontend/src/lib/theme.tsx`

```tsx
import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export type Theme = "light" | "dark" | "system";

type ThemeContextValue = {
  theme: Theme;
  resolvedTheme: "light" | "dark";
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
};

const ThemeContext = createContext<ThemeContextValue | null>(null);

const STORAGE_KEY = "sunstay_theme";

function systemTheme(): "light" | "dark" {
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function resolveTheme(theme: Theme): "light" | "dark" {
  return theme === "system" ? systemTheme() : theme;
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => {
    const saved = localStorage.getItem(STORAGE_KEY) as Theme | null;
    return saved ?? "light";
  });
  const [resolvedTheme, setResolvedTheme] = useState<"light" | "dark">(() => resolveTheme(theme));

  useEffect(() => {
    const next = resolveTheme(theme);
    setResolvedTheme(next);
    document.documentElement.classList.toggle("dark", next === "dark");
    document.documentElement.dataset.theme = next;
    localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  useEffect(() => {
    if (theme !== "system") return;
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = () => {
      const next = systemTheme();
      setResolvedTheme(next);
      document.documentElement.classList.toggle("dark", next === "dark");
    };
    media.addEventListener("change", handler);
    return () => media.removeEventListener("change", handler);
  }, [theme]);

  const value = useMemo<ThemeContextValue>(
    () => ({
      theme,
      resolvedTheme,
      setTheme: setThemeState,
      toggleTheme: () => setThemeState(resolvedTheme === "dark" ? "light" : "dark"),
    }),
    [theme, resolvedTheme],
  );

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) throw new Error("useTheme must be used inside ThemeProvider");
  return context;
}

```

## `frontend/src/lib/utils.ts`

```typescript
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

export function addDaysISO(iso: string, days: number) {
  const date = new Date(`${iso}T12:00:00`);
  date.setDate(date.getDate() + days);
  return date.toISOString().slice(0, 10);
}

export function formatDate(value?: string | null, format = "dd.MM.yyyy") {
  if (!value) return "—";
  const date = new Date(value.length <= 10 ? `${value}T12:00:00` : value);
  if (Number.isNaN(date.getTime())) return String(value);
  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const year = date.getFullYear();
  if (format === "yyyy-MM-dd") return `${year}-${month}-${day}`;
  return `${day}.${month}.${year}`;
}

export function formatDateTime(value?: string | null) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return `${formatDate(value)} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

export function formatMoney(value?: number | string | null, digits = 0) {
  const number = Number(value ?? 0);
  return new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "RUB",
    maximumFractionDigits: digits,
    minimumFractionDigits: digits,
  }).format(Number.isFinite(number) ? number : 0);
}

export function formatNumber(value?: number | string | null) {
  const number = Number(value ?? 0);
  return new Intl.NumberFormat("ru-RU").format(Number.isFinite(number) ? number : 0);
}

export function nightsBetween(checkin?: string | null, checkout?: string | null) {
  if (!checkin || !checkout) return 0;
  const start = new Date(`${checkin}T12:00:00`).getTime();
  const end = new Date(`${checkout}T12:00:00`).getTime();
  return Math.max(0, Math.round((end - start) / 86400000));
}

export function initials(name?: string | null) {
  if (!name) return "SS";
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}

export const BOOKING_STATUS_LABELS: Record<string, string> = {
  NEW: "Новая",
  CONFIRMED: "Подтверждена",
  CHECKED_IN: "Заселён",
  CHECKED_OUT: "Выселен",
  CANCELLED: "Отменена",
  NO_SHOW: "Неявка",
};

export const ROOM_STATUS_LABELS: Record<string, string> = {
  СВОБОДЕН: "Свободен",
  ЗАБРОНИРОВАН: "Забронирован",
  ЗАСЕЛЁН: "Заселён",
  ГРЯЗНЫЙ: "Грязный",
  В_УБОРКЕ: "В уборке",
  ЧИСТЫЙ_ГОТОВ: "Готов",
  БЛОКИРОВАН: "Блокирован",
};

export const TASK_STATUS_LABELS: Record<string, string> = {
  ASSIGNED: "Назначено",
  IN_PROGRESS: "В работе",
  DONE: "Выполнено",
  CANCELLED: "Отменено",
};

export const TASK_TYPE_LABELS: Record<string, string> = {
  DAILY: "Ежедневная",
  POST_CHECKOUT: "После выезда",
  ON_REQUEST: "По запросу",
};

export const PRIORITY_LABELS: Record<string, string> = {
  LOW: "Низкий",
  NORMAL: "Обычный",
  HIGH: "Высокий",
  URGENT: "Срочный",
};

export const MAINTENANCE_STATUS_LABELS: Record<string, string> = {
  OPEN: "Открыта",
  IN_PROGRESS: "В работе",
  DONE: "Выполнена",
  CANCELLED: "Отменена",
};

export const PAYMENT_METHOD_LABELS: Record<string, string> = {
  CARD: "Карта",
  CASH: "Наличные",
  BANK_TRANSFER: "Банковский перевод",
  ONLINE: "Онлайн",
};

export const LINE_TYPE_LABELS: Record<string, string> = {
  ROOM: "Проживание",
  SERVICE: "Услуга",
  DISCOUNT: "Скидка",
  TAX: "Налог",
  ADJUSTMENT: "Корректировка",
};

export const ROLE_LABELS: Record<string, string> = {
  GUEST: "Гость",
  MANAGER: "Менеджер",
  HOUSEKEEPING: "Хаускипинг",
  HOTEL_MANAGER: "Управляющий отелем",
  DB_ADMIN: "Администратор БД",
};

export type StatusTone = "success" | "warning" | "danger" | "info" | "neutral";

export function statusTone(status?: string | null): StatusTone {
  if (!status) return "neutral";
  if (["CONFIRMED", "CHECKED_IN", "DONE", "ЧИСТЫЙ_ГОТОВ", "СВОБОДЕН"].includes(status)) return "success";
  if (["NEW", "ASSIGNED", "OPEN", "В_УБОРКЕ", "ОЖИДАЕТ"].includes(status)) return "warning";
  if (["CANCELLED", "NO_SHOW", "БЛОКИРОВАН", "ГРЯЗНЫЙ"].includes(status)) return "danger";
  if (["IN_PROGRESS", "ЗАБРОНИРОВАН", "ЗАСЕЛЁН", "CHECKED_OUT"].includes(status)) return "info";
  return "neutral";
}

export function statusClass(status?: string | null) {
  const tone = statusTone(status);
  const map: Record<StatusTone, string> = {
    success: "bg-emerald-500/12 text-emerald-700 dark:text-emerald-300",
    warning: "bg-amber-500/14 text-amber-700 dark:text-amber-300",
    danger: "bg-rose-500/12 text-rose-700 dark:text-rose-300",
    info: "bg-sky-500/12 text-sky-700 dark:text-sky-300",
    neutral: "bg-surface2 text-muted",
  };
  return map[tone];
}

export function statusLabel(status?: string | null) {
  if (!status) return "—";
  return (
    BOOKING_STATUS_LABELS[status] ??
    ROOM_STATUS_LABELS[status] ??
    TASK_STATUS_LABELS[status] ??
    MAINTENANCE_STATUS_LABELS[status] ??
    status
  );
}

export function monthLabel(value?: string | null) {
  if (!value) return "—";
  const date = new Date(value.length <= 10 ? `${value}T12:00:00` : value);
  return new Intl.DateTimeFormat("ru-RU", { month: "short", year: "numeric" }).format(date);
}

export function dateRange(start: string, end: string) {
  const days: string[] = [];
  let cursor = start;
  while (cursor <= end) {
    days.push(cursor);
    cursor = addDaysISO(cursor, 1);
  }
  return days;
}

```

## `frontend/src/main.tsx`

```tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "./App";
import { AuthProvider } from "./lib/auth";
import { I18nProvider } from "./lib/i18n";
import { ThemeProvider } from "./lib/theme";
import { ToastProvider } from "./components/ui";
import "./index.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 15000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <I18nProvider>
          <AuthProvider>
            <ToastProvider>
              <BrowserRouter>
                <App />
              </BrowserRouter>
            </ToastProvider>
          </AuthProvider>
        </I18nProvider>
      </ThemeProvider>
    </QueryClientProvider>
  </React.StrictMode>,
);

```

## `frontend/src/pages/AdminPages.tsx`

```tsx
import {
  Activity,
  Ban,
  BookOpen,
  Check,
  DatabaseBackup,
  Download,
  Edit,
  Eye,
  KeyRound,
  Plus,
  RefreshCw,
  Save,
  ShieldCheck,
  Trash2,
  Unlock,
  Upload,
  UserCheck,
  Users,
  X,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, downloadFile, getErrorMessage } from "../lib/api";
import { useAuth } from "../lib/auth";
import { useToast } from "../components/ui";
import {
  Avatar,
  Badge,
  Button,
  Card,
  Drawer,
  EmptyState,
  ErrorState,
  Input,
  Modal,
  PageHeader,
  Pagination,
  Select,
  SensitiveValue,
  Spinner,
  StatusPill,
  Tabs,
  Textarea,
} from "../components/ui";
import { formatDate, formatDateTime, formatMoney, formatNumber, ROLE_LABELS, statusLabel } from "../lib/utils";

type DirectoryField = {
  key: string;
  label: string;
  type?: "text" | "number" | "date" | "textarea" | "select";
  options?: Array<{ value: string | number; label: string }>;
  required?: boolean;
};

const DIRECTORY_PK: Record<string, string> = {
  "room-types": "room_type_id",
  rooms: "room_id",
  amenities: "amenity_id",
  "rate-plans": "rate_id",
  services: "service_id",
  "promo-codes": "promo_id",
  "cancellation-reasons": "reason_id",
};

const DIRECTORY_CONFIG: Record<string, { label: string; fields: DirectoryField[] }> = {
  "room-types": {
    label: "Типы номеров",
    fields: [
      { key: "name", label: "Название", required: true },
      { key: "capacity", label: "Вместимость", type: "number", required: true },
      { key: "description", label: "Описание", type: "textarea" },
    ],
  },
  rooms: {
    label: "Номера",
    fields: [
      { key: "room_number", label: "Номер", required: true },
      { key: "floor", label: "Этаж", type: "number", required: true },
      { key: "room_type_id", label: "Тип", type: "select", required: true },
      { key: "status_id", label: "Статус", type: "select", required: true },
      { key: "block_reason_id", label: "Причина блокировки", type: "select" },
    ],
  },
  amenities: {
    label: "Удобства",
    fields: [{ key: "name", label: "Название", required: true }],
  },
  "rate-plans": {
    label: "Тарифы",
    fields: [
      { key: "room_type_id", label: "Тип номера", type: "select", required: true },
      { key: "name", label: "Название", required: true },
      { key: "season_start", label: "Начало сезона", type: "date", required: true },
      { key: "season_end", label: "Конец сезона", type: "date", required: true },
      { key: "price_per_night", label: "Цена за ночь", type: "number", required: true },
      { key: "cancellation_terms", label: "Условия отмены", type: "textarea" },
    ],
  },
  services: {
    label: "Услуги",
    fields: [
      { key: "unit_id", label: "Единица", type: "select", required: true },
      { key: "name", label: "Название", required: true },
      { key: "price", label: "Цена", type: "number", required: true },
    ],
  },
  "promo-codes": {
    label: "Промокоды",
    fields: [
      { key: "code", label: "Код", required: true },
      { key: "discount_percent", label: "Скидка, %", type: "number", required: true },
      { key: "valid_from", label: "Действует с", type: "date", required: true },
      { key: "valid_to", label: "Действует до", type: "date", required: true },
    ],
  },
  "cancellation-reasons": {
    label: "Причины отмены",
    fields: [{ key: "name", label: "Название", required: true }],
  },
};

function UsersTable({ mode }: { mode: "admin" | "employees" }) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);
  const [createOpen, setCreateOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [resetOpen, setResetOpen] = useState(false);
  const [blockOpen, setBlockOpen] = useState(false);
  const [selected, setSelected] = useState<any>(null);
  const [blockUser, setBlockUser] = useState<any>(null);
  const [blockReasonId, setBlockReasonId] = useState("");
  const [blockCustom, setBlockCustom] = useState("");
  const [form, setForm] = useState({ role_id: "2", full_name: "", email: "", phone: "", password: "" });
  const [resetPassword, setResetPassword] = useState("");
  const [roleValue, setRoleValue] = useState("2");

  const query = useQuery({
    queryKey: ["admin-users", search, roleFilter, statusFilter, page],
    queryFn: () => api.get("/admin/users", {
      params: {
        search: search || undefined,
        role_id: roleFilter || undefined,
        status_filter: statusFilter || undefined,
        page,
        page_size: 25,
      },
    }).then((response) => response.data),
  });
  const rolesQuery = useQuery({
    queryKey: ["admin-roles"],
    queryFn: () => api.get("/admin/roles").then((response) => response.data),
  });
  const statsQuery = useQuery({
    queryKey: ["admin-user-stats"],
    queryFn: () => api.get("/admin/users/stats").then((response) => response.data),
    enabled: mode === "admin",
  });
  const reasonsQuery = useQuery({
    queryKey: ["user-block-reasons"],
    queryFn: () => api.get("/admin/users/block-reasons").then((response) => response.data),
    enabled: mode === "admin",
  });

  const createMutation = useMutation({
    mutationFn: () => api.post("/admin/users", { ...form, role_id: Number(form.role_id) }),
    onSuccess: () => {
      toast("Пользователь создан", "success");
      setCreateOpen(false);
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      queryClient.invalidateQueries({ queryKey: ["admin-user-stats"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const editMutation = useMutation({
    mutationFn: () => api.patch(`/admin/users/${selected.user_id}`, {
      role_id: Number(roleValue),
      full_name: form.full_name,
      email: form.email,
      phone: form.phone,
    }),
    onSuccess: () => {
      toast("Пользователь обновлён", "success");
      setEditOpen(false);
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const blockMutation = useMutation({
    mutationFn: ({ id, reason_id, custom_reason }: { id: number; reason_id: number | null; custom_reason: string | null }) =>
      api.post(`/admin/users/${id}/block`, { reason_id, custom_reason }),
    onSuccess: () => {
      toast("Пользователь заблокирован", "success");
      setBlockOpen(false);
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      queryClient.invalidateQueries({ queryKey: ["admin-user-stats"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const unblockMutation = useMutation({
    mutationFn: (id: number) => api.post(`/admin/users/${id}/unblock`),
    onSuccess: () => {
      toast("Пользователь разблокирован", "success");
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      queryClient.invalidateQueries({ queryKey: ["admin-user-stats"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const resetMutation = useMutation({
    mutationFn: () => api.post(`/admin/users/${selected.user_id}/reset-password`, { new_password: resetPassword }),
    onSuccess: () => {
      toast("Пароль обновлён", "success");
      setResetOpen(false);
      setResetPassword("");
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const roleMutation = useMutation({
    mutationFn: () => api.patch(`/admin/users/${selected.user_id}/role`, { role_id: Number(roleValue) }),
    onSuccess: () => {
      toast("Роль обновлена", "success");
      setEditOpen(false);
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  const items = query.data?.items ?? [];
  const total = query.data?.total ?? 0;
  const roles = rolesQuery.data ?? [];
  const stats = statsQuery.data?.summary ?? {};
  const reasons = reasonsQuery.data ?? [];
  const editableRoles = mode === "employees" ? roles.filter((role: any) => [2, 3].includes(role.role_id)) : roles;

  function openCreate() {
    setForm({ role_id: "2", full_name: "", email: "", phone: "", password: "" });
    setCreateOpen(true);
  }

  function openEdit(userRow: any) {
    setSelected(userRow);
    setForm({
      role_id: String(userRow.role_id),
      full_name: userRow.full_name ?? "",
      email: userRow.email ?? "",
      phone: userRow.phone ?? "",
      password: "",
    });
    setRoleValue(String(userRow.role_id));
    setEditOpen(true);
  }

  function openBlock(userRow: any) {
    setBlockUser(userRow);
    setBlockReasonId("");
    setBlockCustom("");
    setBlockOpen(true);
  }

  function submitBlock() {
    if (!blockReasonId && !blockCustom.trim()) {
      toast("Укажите причину блокировки", "error");
      return;
    }
    blockMutation.mutate({
      id: blockUser.user_id,
      reason_id: blockReasonId ? Number(blockReasonId) : null,
      custom_reason: blockCustom.trim() || null,
    });
  }

  return (
    <div>
      {mode === "admin" && (
        <div className="mb-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div><p className="label">Всего</p><p className="kpi-value mt-2">{stats.total ?? 0}</p></div>
              <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-forest/10 text-forest dark:bg-white/10 dark:text-ink"><Users size={19} /></span>
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div><p className="label">Онлайн</p><p className="kpi-value mt-2">{stats.online ?? 0}</p></div>
              <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-emerald-500/12 text-emerald-600"><Activity size={19} /></span>
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div><p className="label">Активные</p><p className="kpi-value mt-2">{stats.active ?? 0}</p></div>
              <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-sky-500/12 text-sky-600"><UserCheck size={19} /></span>
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div><p className="label">Заблокированные</p><p className="kpi-value mt-2">{stats.blocked ?? 0}</p></div>
              <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-rose-500/12 text-rose-600"><Ban size={19} /></span>
            </div>
          </Card>
        </div>
      )}

      <Card className="mb-4 flex flex-wrap items-end gap-2">
        <Input
          label="Поиск"
          value={search}
          onChange={(event) => { setSearch(event.target.value); setPage(1); }}
          placeholder="ФИО, email, телефон"
          className="min-w-[220px]"
        />
        {mode === "admin" && (
          <Select label="Роль" value={roleFilter} onChange={(event) => { setRoleFilter(event.target.value); setPage(1); }}>
            <option value="">Все роли</option>
            {roles.map((role: any) => <option key={role.role_id} value={role.role_id}>{role.name}</option>)}
          </Select>
        )}
        {mode === "admin" && (
          <Select label="Статус" value={statusFilter} onChange={(event) => { setStatusFilter(event.target.value); setPage(1); }}>
            <option value="">Все</option>
            <option value="online">Онлайн</option>
            <option value="active">Активные</option>
            <option value="blocked">Заблокированные</option>
          </Select>
        )}
        <Button variant="secondary" onClick={() => query.refetch()}><RefreshCw size={14} /> Обновить</Button>
        {mode === "admin" && <Button onClick={openCreate}><Plus size={15} /> Добавить пользователя</Button>}
      </Card>

      {query.isLoading && <Spinner />}
      {query.isError && <ErrorState message={getErrorMessage(query.error)} />}
      {!query.isLoading && !query.isError && (
        <div className="table-wrap">
          <table className="table-base">
            <thead><tr><th>Сотрудник</th><th>Роль</th><th>Контакты</th><th>Статус</th><th>Последняя активность</th><th /></tr></thead>
            <tbody>
              {items.map((userRow: any) => (
                <tr key={userRow.user_id}>
                  <td>
                    <div className="flex items-center gap-3">
                      <Avatar name={userRow.full_name} className="h-9 w-9 text-[10px]" />
                      <div><p className="font-semibold">{userRow.full_name}</p><p className="text-xs text-muted">{userRow.email}</p></div>
                    </div>
                  </td>
                  <td><Badge tone={userRow.role_id === 5 ? "danger" : userRow.role_id === 4 ? "warning" : "info"}>{userRow.role_name}</Badge></td>
                  <td>
                    <SensitiveValue value={userRow.phone} />
                    <p className="mt-1 text-xs text-muted">{userRow.email}</p>
                  </td>
                  <td>
                    {!userRow.is_active ? (
                      <div><Badge tone="danger">Заблокирован</Badge><p className="mt-1 max-w-[220px] text-xs text-muted">{userRow.block_reason ?? "Причина не указана"}</p></div>
                    ) : userRow.is_online ? (
                      <Badge tone="success">Онлайн</Badge>
                    ) : (
                      <Badge tone="neutral">Не в сети</Badge>
                    )}
                  </td>
                  <td>{userRow.last_seen_at ? formatDateTime(userRow.last_seen_at) : "—"}</td>
                  <td className="text-right">
                    <div className="flex justify-end gap-1">
                      {mode === "admin" && <Button variant="ghost" size="sm" onClick={() => openEdit(userRow)}><Edit size={14} /></Button>}
                      {mode === "employees" && <Button variant="ghost" size="sm" onClick={() => openEdit(userRow)}>Роль</Button>}
                      {mode === "admin" && <Button variant="ghost" size="sm" onClick={() => { setSelected(userRow); setResetOpen(true); }}><KeyRound size={14} /></Button>}
                      {mode === "admin" && (
                        userRow.is_active
                          ? <Button variant="ghost" size="sm" onClick={() => openBlock(userRow)}><Ban size={14} /></Button>
                          : <Button variant="ghost" size="sm" onClick={() => unblockMutation.mutate(userRow.user_id)}><Unlock size={14} /></Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pagination page={page} pageSize={25} total={total} onPageChange={setPage} />
        </div>
      )}

      <Modal open={createOpen} title="Новый пользователь" onClose={() => setCreateOpen(false)} footer={<><Button variant="secondary" onClick={() => setCreateOpen(false)}>Отмена</Button><Button onClick={() => createMutation.mutate()} disabled={createMutation.isPending}>Создать</Button></>}>
        <div className="space-y-3">
          <Select label="Роль" value={form.role_id} onChange={(event) => setForm({ ...form, role_id: event.target.value })}>
            {roles.map((role: any) => <option key={role.role_id} value={role.role_id}>{role.name}</option>)}
          </Select>
          <Input label="ФИО" value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} />
          <Input label="Email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
          <Input label="Телефон" value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} />
          <Input label="Пароль" type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} />
        </div>
      </Modal>

      <Modal open={editOpen} title={mode === "employees" ? "Назначение роли" : "Редактировать пользователя"} onClose={() => setEditOpen(false)} footer={<><Button variant="secondary" onClick={() => setEditOpen(false)}>Отмена</Button>{mode === "employees" ? <Button onClick={() => roleMutation.mutate()} disabled={roleMutation.isPending}>Сохранить роль</Button> : <Button onClick={() => editMutation.mutate()} disabled={editMutation.isPending}>Сохранить</Button>}</>}>
        <div className="space-y-3">
          {mode === "admin" && <Input label="ФИО" value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} />}
          {mode === "admin" && <Input label="Email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />}
          {mode === "admin" && <Input label="Телефон" value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} />}
          <Select label="Роль" value={roleValue} onChange={(event) => setRoleValue(event.target.value)}>
            {editableRoles.map((role: any) => <option key={role.role_id} value={role.role_id}>{role.name}</option>)}
          </Select>
        </div>
      </Modal>

      <Modal open={resetOpen} title="Сброс пароля" onClose={() => setResetOpen(false)} footer={<><Button variant="secondary" onClick={() => setResetOpen(false)}>Отмена</Button><Button onClick={() => resetMutation.mutate()} disabled={resetMutation.isPending || resetPassword.length < 8}>Сбросить</Button></>}>
        <Input label="Новый пароль" type="password" value={resetPassword} onChange={(event) => setResetPassword(event.target.value)} />
      </Modal>

      <Modal open={blockOpen} title="Блокировка пользователя" subtitle={blockUser?.full_name} onClose={() => setBlockOpen(false)} footer={<><Button variant="secondary" onClick={() => setBlockOpen(false)}>Отмена</Button><Button variant="danger" onClick={submitBlock} disabled={blockMutation.isPending}>Заблокировать</Button></>}>
        <div className="space-y-3">
          <Select label="Причина" value={blockReasonId} onChange={(event) => setBlockReasonId(event.target.value)}>
            <option value="">Выберите причину</option>
            {reasons.map((reason: any) => <option key={reason.reason_id} value={reason.reason_id}>{reason.name}</option>)}
          </Select>
          <Input label="Своя причина" value={blockCustom} onChange={(event) => setBlockCustom(event.target.value)} placeholder="Можно указать свой текст" />
          <p className="text-xs text-muted">Если выбрана причина из списка, своя причина необязательна.</p>
        </div>
      </Modal>
    </div>
  );
}

function PermissionsMatrix() {
  const { user } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [roleId, setRoleId] = useState("2");
  const [selected, setSelected] = useState<string[]>([]);
  const rolesQuery = useQuery({ queryKey: ["admin-roles"], queryFn: () => api.get("/admin/roles").then((response) => response.data) });
  const permissionsQuery = useQuery({ queryKey: ["admin-permissions"], queryFn: () => api.get("/admin/permissions").then((response) => response.data) });
  const roles = useMemo(() => rolesQuery.data ?? [], [rolesQuery.data]);
  const permissions = useMemo(() => permissionsQuery.data ?? [], [permissionsQuery.data]);
  const grouped = useMemo(() => {
    const map: Record<string, any[]> = {};
    for (const permission of permissions) (map[permission.module] ??= []).push(permission);
    return map;
  }, [permissions]);

  useEffect(() => {
    const role = roles.find((item: any) => String(item.role_id) === roleId);
    const next = role?.permissions ?? [];
    setSelected((current) => (current.join("|") === next.join("|") ? current : next));
  }, [roleId, roles]);

  const saveMutation = useMutation({
    mutationFn: () => api.put(`/admin/roles/${roleId}/permissions`, { permission_codes: selected }),
    onSuccess: () => { toast("Права сохранены", "success"); queryClient.invalidateQueries({ queryKey: ["admin-roles"] }); },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  if (user?.role_code !== "DB_ADMIN") return null;

  return (
    <Card className="mt-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="font-display text-2xl font-semibold">Матрица полномочий</h2>
          <p className="text-sm text-muted">Изменения применяются на сервере сразу после сохранения.</p>
        </div>
        <div className="flex items-end gap-2">
          <Select label="Роль" value={roleId} onChange={(event) => setRoleId(event.target.value)}>
            {roles.map((role: any) => <option key={role.role_id} value={role.role_id}>{role.name}</option>)}
          </Select>
          <Button onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending}><Save size={15} /> Сохранить права</Button>
        </div>
      </div>
      <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {Object.entries(grouped).map(([module, items]) => (
          <div key={module} className="rounded-xl border border-line p-3">
            <p className="mb-2 text-[11px] font-bold uppercase tracking-[0.08em] text-muted">{module}</p>
            <div className="space-y-1.5">
              {items.map((permission: any) => (
                <label key={permission.code} className="flex items-center gap-2 text-xs text-muted">
                  <input
                    type="checkbox"
                    className="h-4 w-4 accent-terracotta"
                    checked={selected.includes(permission.code)}
                    onChange={(event) => setSelected((current) => event.target.checked ? [...current, permission.code] : current.filter((code) => code !== permission.code))}
                  />
                  <span>{permission.description}</span>
                </label>
              ))}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

export function AdminUsersPage() {
  return (
    <div>
      <PageHeader title="Пользователи и роли" subtitle="Учётные записи сотрудников, роли и матрица полномочий." />
      <UsersTable mode="admin" />
      <PermissionsMatrix />
    </div>
  );
}

export function EmployeesPage() {
  return (
    <div>
      <PageHeader title="Сотрудники" subtitle="Назначение ролей Менеджера и Хаускипинга." />
      <UsersTable mode="employees" />
    </div>
  );
}

function DirectoryPageContent() {
  const { user } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [entity, setEntity] = useState("room-types");
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [form, setForm] = useState<Record<string, any>>({});
  const [importOpen, setImportOpen] = useState(false);
  const [importPreview, setImportPreview] = useState<any>(null);
  const [importFile, setImportFile] = useState<File | null>(null);
  const config = DIRECTORY_CONFIG[entity];
  const allowedTabs = user?.role_code === "HOTEL_MANAGER"
    ? ["rooms", "rate-plans", "services", "promo-codes"]
    : Object.keys(DIRECTORY_CONFIG);
  const activeTabs = allowedTabs.map((key) => ({ value: key, label: DIRECTORY_CONFIG[key].label }));

  useEffect(() => {
    if (!allowedTabs.includes(entity)) setEntity(allowedTabs[0]);
  }, [allowedTabs, entity]);

  const query = useQuery({
    queryKey: ["admin-directory", entity],
    queryFn: () => api.get(`/admin/directories/${entity}`).then((response) => response.data),
  });
  const roomTypesQuery = useQuery({ queryKey: ["admin-directory", "room-types"], queryFn: () => api.get("/admin/directories/room-types").then((response) => response.data), enabled: ["rooms", "rate-plans"].includes(entity) });
  const roomStatusesQuery = useQuery({ queryKey: ["admin-directory", "room-statuses"], queryFn: () => api.get("/admin/directories/room-statuses").then((response) => response.data), enabled: entity === "rooms" });
  const blockReasonsQuery = useQuery({ queryKey: ["admin-directory", "block-reasons"], queryFn: () => api.get("/admin/directories/block-reasons").then((response) => response.data), enabled: entity === "rooms" });
  const serviceUnitsQuery = useQuery({ queryKey: ["admin-directory", "service-units"], queryFn: () => api.get("/admin/directories/service-units").then((response) => response.data), enabled: entity === "services" });

  const createMutation = useMutation({
    mutationFn: () => api.post(`/admin/directories/${entity}`, form),
    onSuccess: () => { toast("Запись добавлена", "success"); setModalOpen(false); queryClient.invalidateQueries({ queryKey: ["admin-directory", entity] }); },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const updateMutation = useMutation({
    mutationFn: () => api.patch(`/admin/directories/${entity}/${editing[DIRECTORY_PK[entity]]}`, form),
    onSuccess: () => { toast("Запись обновлена", "success"); setModalOpen(false); queryClient.invalidateQueries({ queryKey: ["admin-directory", entity] }); },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const deleteMutation = useMutation({
    mutationFn: (item: any) => api.delete(`/admin/directories/${entity}/${item[DIRECTORY_PK[entity]]}`),
    onSuccess: () => { toast("Запись удалена", "success"); queryClient.invalidateQueries({ queryKey: ["admin-directory", entity] }); },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const importPreviewMutation = useMutation({
    mutationFn: (file: File) => {
      const data = new FormData();
      data.append("file", file);
      return api.post("/imports/rates/preview", data, { headers: { "Content-Type": "multipart/form-data" } }).then((response) => response.data);
    },
    onSuccess: (data) => { setImportPreview(data); toast(`Проверено строк: ${data.total}, ошибок: ${data.errors}`, data.errors ? "info" : "success"); },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const importCommitMutation = useMutation({
    mutationFn: () => api.post("/imports/rates/commit", { filename: importFile?.name, rows: importPreview.rows }),
    onSuccess: () => { toast("Тарифы загружены", "success"); setImportOpen(false); setImportPreview(null); setImportFile(null); queryClient.invalidateQueries({ queryKey: ["admin-directory", "rate-plans"] }); },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  function idKey() {
    return DIRECTORY_PK[entity];
  }

  function openCreate() {
    setEditing(null);
    setForm({});
    setModalOpen(true);
  }

  function openEdit(item: any) {
    setEditing(item);
    const next: Record<string, any> = {};
    for (const field of config.fields) next[field.key] = item[field.key] ?? "";
    setForm(next);
    setModalOpen(true);
  }

  function optionsFor(field: DirectoryField) {
    if (field.key === "room_type_id") return (roomTypesQuery.data ?? []).map((item: any) => ({ value: item.room_type_id, label: item.name }));
    if (field.key === "status_id") return (roomStatusesQuery.data ?? []).map((item: any) => ({ value: item.status_id, label: item.name }));
    if (field.key === "block_reason_id") return [{ value: "", label: "Не блокирован" }, ...(blockReasonsQuery.data ?? []).map((item: any) => ({ value: item.reason_id, label: item.name }))];
    if (field.key === "unit_id") return (serviceUnitsQuery.data ?? []).map((item: any) => ({ value: item.unit_id, label: item.name }));
    return field.options ?? [];
  }

  const items = query.data ?? [];
  const columns = config.fields.filter((field) => field.key !== "description" && field.key !== "cancellation_terms");

  return (
    <div>
      <PageHeader
        title="Справочники отеля"
        subtitle="Типы номеров, номера, тарифы, услуги и промокоды."
        actions={
          <>
            {entity === "rate-plans" && <Button variant="secondary" onClick={() => setImportOpen(true)}><Upload size={15} /> Импорт CSV</Button>}
            <Button onClick={openCreate}><Plus size={15} /> Добавить</Button>
          </>
        }
      />
      <Tabs className="mb-4" value={entity} onChange={setEntity} items={activeTabs} />
      {query.isLoading && <Spinner />}
      {query.isError && <ErrorState message={getErrorMessage(query.error)} />}
      {!query.isLoading && !query.isError && (
        <div className="table-wrap">
          <table className="table-base">
            <thead><tr>{columns.map((field) => <th key={field.key}>{field.label}</th>)}<th /></tr></thead>
            <tbody>
              {items.map((item: any) => (
                <tr key={item[idKey()]}>
                  {columns.map((field) => {
                    let value = item[field.key];
                    if (field.key === "room_type_id") value = (roomTypesQuery.data ?? []).find((roomType: any) => roomType.room_type_id === value)?.name ?? value;
                    if (field.key === "status_id") value = (roomStatusesQuery.data ?? []).find((status: any) => status.status_id === value)?.name ?? value;
                    if (field.key === "unit_id") value = (serviceUnitsQuery.data ?? []).find((unit: any) => unit.unit_id === value)?.name ?? value;
                    if (field.key === "block_reason_id") value = value ? value : "—";
                    if (field.type === "number" && ["price_per_night", "price"].includes(field.key)) value = formatMoney(value);
                    return <td key={field.key}>{String(value ?? "—")}</td>;
                  })}
                  <td className="text-right">
                    <div className="flex justify-end gap-1">
                      <Button variant="ghost" size="sm" onClick={() => openEdit(item)}><Edit size={14} /></Button>
                      <Button variant="ghost" size="sm" onClick={() => { if (window.confirm("Удалить запись?")) deleteMutation.mutate(item); }}><Trash2 size={14} /></Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!items.length && <EmptyState />}
        </div>
      )}

      <Modal open={modalOpen} title={editing ? "Редактировать запись" : "Добавить запись"} onClose={() => setModalOpen(false)} footer={<><Button variant="secondary" onClick={() => setModalOpen(false)}>Отмена</Button><Button onClick={() => editing ? updateMutation.mutate() : createMutation.mutate()} disabled={createMutation.isPending || updateMutation.isPending}><Save size={15} /> Сохранить</Button></>}>
        <div className="space-y-3">
          {config.fields.map((field) => {
            if (field.type === "select") {
              return (
                <Select key={field.key} label={field.label} value={form[field.key] ?? ""} onChange={(event) => setForm({ ...form, [field.key]: event.target.value })}>
                  <option value="">Выберите</option>
                  {optionsFor(field).map((option: { value: string | number; label: string }) => <option key={option.value} value={option.value}>{option.label}</option>)}
                </Select>
              );
            }
            if (field.type === "textarea") {
              return <Textarea key={field.key} label={field.label} value={form[field.key] ?? ""} onChange={(event) => setForm({ ...form, [field.key]: event.target.value })} />;
            }
            return <Input key={field.key} label={field.label} type={field.type ?? "text"} value={form[field.key] ?? ""} onChange={(event) => setForm({ ...form, [field.key]: field.type === "number" ? Number(event.target.value) : event.target.value })} />;
          })}
        </div>
      </Modal>

      <Modal open={importOpen} title="Импорт тарифов из CSV" subtitle="CSV: room_type, name, season_start, season_end, price_per_night, cancellation_terms" onClose={() => setImportOpen(false)} size="lg" footer={<><Button variant="secondary" onClick={() => setImportOpen(false)}>Отмена</Button><Button onClick={() => importCommitMutation.mutate()} disabled={!importPreview?.rows?.some((row: any) => row.status === "ok") || importCommitMutation.isPending}>Загрузить</Button></>}>
        <div className="space-y-4">
          <input type="file" accept=".csv,text/csv" onChange={(event) => { const file = event.target.files?.[0]; if (file) { setImportFile(file); importPreviewMutation.mutate(file); } }} className="input py-2" />
          {importPreview && (
            <div className="space-y-2">
              <div className="flex gap-3 text-sm"><span>Всего: {importPreview.total}</span><span className="text-success">OK: {importPreview.valid}</span><span className="text-danger">Ошибок: {importPreview.errors}</span></div>
              <div className="max-h-72 overflow-auto rounded-xl border border-line">
                <table className="table-base">
                  <thead><tr><th>Строка</th><th>Тип</th><th>Название</th><th>Цена</th><th>Статус</th><th>Ошибка</th></tr></thead>
                  <tbody>
                    {importPreview.rows.map((row: any) => (
                      <tr key={row.row}>
                        <td>{row.row}</td><td>{row.room_type}</td><td>{row.name}</td><td>{formatMoney(row.price_per_night)}</td>
                        <td>{row.status === "ok" ? <span className="text-success">OK</span> : <span className="text-danger">Ошибка</span>}</td>
                        <td className="text-xs text-muted">{row.error ?? ""}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
}

export function AdminDirectoriesPage() {
  return <DirectoryPageContent />;
}

export function AdminAuditPage() {
  const [tab, setTab] = useState("data");
  const [roleFilter, setRoleFilter] = useState("");
  const [userSearch, setUserSearch] = useState("");
  const [tableName, setTableName] = useState("");
  const [action, setAction] = useState("");
  const [errorsOnly, setErrorsOnly] = useState(false);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<any>(null);

  const eventType = tab === "login" ? "LOGIN_SECURITY" : tab === "system" ? "AUTO_RELEASE" : "DATA_CHANGE";
  const params = {
    role_id: roleFilter || undefined,
    user_search: userSearch || undefined,
    table_name: tableName || undefined,
    action: action || undefined,
    event_type: eventType,
    is_error: errorsOnly ? true : undefined,
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
  };

  const rolesQuery = useQuery({
    queryKey: ["admin-roles"],
    queryFn: () => api.get("/admin/roles").then((response) => response.data),
  });
  const query = useQuery({
    queryKey: ["admin-audit", tab, roleFilter, userSearch, tableName, action, errorsOnly, dateFrom, dateTo, page],
    queryFn: () => api.get("/admin/audit", { params: { ...params, page, page_size: 25 } }).then((response) => response.data),
  });
  const roles = rolesQuery.data ?? [];
  const items = query.data?.items ?? [];
  const total = query.data?.total ?? 0;

  function resetFilters() {
    setRoleFilter("");
    setUserSearch("");
    setTableName("");
    setAction("");
    setErrorsOnly(false);
    setDateFrom("");
    setDateTo("");
    setPage(1);
  }

  return (
    <div>
      <PageHeader
        title="Журнал аудита"
        subtitle="Кто, когда и что изменил. Ошибки подсвечиваются красным."
        actions={
          <Button
            variant="secondary"
            onClick={() => downloadFile(api, "/admin/audit/export", "audit.csv", params)}
          >
            <Download size={15} /> Экспорт CSV
          </Button>
        }
      />

      <Tabs
        className="mb-4"
        value={tab}
        onChange={(value) => { setTab(value); setPage(1); }}
        items={[
          { value: "data", label: "Изменения данных" },
          { value: "login", label: "Пользователи и вход" },
          { value: "system", label: "Системные события" },
        ]}
      />

      <Card className="mb-4 flex flex-wrap items-end gap-2">
        <Select label="Роль" value={roleFilter} onChange={(event) => { setRoleFilter(event.target.value); setPage(1); }}>
          <option value="">Все роли</option>
          {roles.map((role: any) => <option key={role.role_id} value={role.role_id}>{role.name}</option>)}
        </Select>
        <Input
          label="Пользователь"
          value={userSearch}
          onChange={(event) => { setUserSearch(event.target.value); setPage(1); }}
          placeholder="Имя или email"
        />
        <Input
          label="Таблица"
          value={tableName}
          onChange={(event) => { setTableName(event.target.value); setPage(1); }}
          placeholder="bookings"
        />
        <Select label="Действие" value={action} onChange={(event) => { setAction(event.target.value); setPage(1); }}>
          <option value="">Все</option>
          <option value="INSERT">INSERT</option>
          <option value="UPDATE">UPDATE</option>
          <option value="DELETE">DELETE</option>
          <option value="LOGIN_SUCCESS">LOGIN_SUCCESS</option>
          <option value="LOGIN_FAILED">LOGIN_FAILED</option>
          <option value="LOGIN_BLOCKED">LOGIN_BLOCKED</option>
          <option value="AUTO_RELEASE">AUTO_RELEASE</option>
          <option value="ERROR">ERROR</option>
        </Select>
        <label className="flex h-10 items-center gap-2 text-sm text-muted">
          <input type="checkbox" checked={errorsOnly} onChange={(event) => { setErrorsOnly(event.target.checked); setPage(1); }} className="h-4 w-4 accent-terracotta" />
          Только ошибки
        </label>
        <Input label="С даты" type="date" value={dateFrom} onChange={(event) => { setDateFrom(event.target.value); setPage(1); }} />
        <Input label="По дату" type="date" value={dateTo} onChange={(event) => { setDateTo(event.target.value); setPage(1); }} />
        <Button variant="secondary" onClick={() => setPage(1)}>Применить</Button>
        <Button variant="ghost" onClick={resetFilters}>Сбросить</Button>
      </Card>

      {query.isLoading && <Spinner />}
      {query.isError && <ErrorState message={getErrorMessage(query.error)} />}
      {!query.isLoading && !query.isError && (
        <div className="table-wrap">
          <table className="table-base">
            <thead>
              <tr>
                <th>Дата</th><th>Пользователь</th><th>Роль</th><th>Действие</th>
                <th>Объект</th><th>Ошибка</th><th>IP</th><th />
              </tr>
            </thead>
            <tbody>
              {items.map((item: any) => (
                <tr key={item.log_id} className={item.is_error ? "bg-rose-500/10" : undefined}>
                  <td>{formatDateTime(item.changed_at)}</td>
                  <td>{item.user_name ?? "—"}</td>
                  <td>{item.role_name ?? "—"}</td>
                  <td>
                    <Badge tone={item.is_error ? "danger" : item.action === "DELETE" ? "danger" : item.action === "INSERT" ? "success" : "warning"}>
                      {item.event_type === "LOGIN_SECURITY" ? item.action : item.action}
                    </Badge>
                  </td>
                  <td>{item.table_name} {item.record_id ? `#${item.record_id}` : ""}</td>
                  <td className="max-w-[260px]">
                    {item.is_error
                      ? <span className="text-xs font-semibold text-rose-600 dark:text-rose-300">{item.error_message ?? "Ошибка"}</span>
                      : <span className="text-xs text-muted">—</span>}
                  </td>
                  <td className="text-xs text-muted">{item.ip_address ?? "—"}</td>
                  <td className="text-right">
                    <Button variant="ghost" size="sm" onClick={() => setSelected(item)}>
                      <Eye size={14} /> Детали
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pagination page={page} pageSize={25} total={total} onPageChange={setPage} />
        </div>
      )}

      <Drawer
        open={Boolean(selected)}
        title={selected?.event_type === "LOGIN_SECURITY" ? "Событие входа" : "Детализация изменений"}
        subtitle={selected ? `${selected.table_name}${selected.record_id ? ` #${selected.record_id}` : ""} · ${selected.action}` : ""}
        onClose={() => setSelected(null)}
      >
        {selected && (
          <div className="space-y-4">
            {selected.is_error && (
              <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-700 dark:text-rose-300">
                <p className="font-semibold">Ошибка</p>
                <p className="mt-1">{selected.error_message ?? "Без описания"}</p>
              </div>
            )}
            {selected.event_type === "LOGIN_SECURITY" ? (
              <div className="space-y-2 rounded-xl border border-line p-3 text-sm">
                <p><span className="text-muted">Событие:</span> {selected.action}</p>
                <p><span className="text-muted">Пользователь:</span> {selected.user_name ?? "—"}</p>
                <p><span className="text-muted">IP:</span> {selected.ip_address ?? "—"}</p>
                <p><span className="text-muted">User-Agent:</span> {selected.user_agent ?? "—"}</p>
                <p><span className="text-muted">Request ID:</span> {selected.request_id ?? "—"}</p>
                <p><span className="text-muted">Данные:</span> {selected.new_value ?? "—"}</p>
              </div>
            ) : (
              <>
                <div><p className="label mb-2">Было</p><pre className="max-h-64 overflow-auto rounded-xl bg-surface2 p-3 text-xs">{selected.old_value ? JSON.stringify(JSON.parse(selected.old_value), null, 2) : "—"}</pre></div>
                <div><p className="label mb-2">Стало</p><pre className="max-h-64 overflow-auto rounded-xl bg-surface2 p-3 text-xs">{selected.new_value ? JSON.stringify(JSON.parse(selected.new_value), null, 2) : "—"}</pre></div>
                <div className="rounded-xl border border-line p-3 text-xs text-muted">
                  <p>IP: {selected.ip_address ?? "—"}</p>
                  <p>User-Agent: {selected.user_agent ?? "—"}</p>
                  <p>Request ID: {selected.request_id ?? "—"}</p>
                </div>
              </>
            )}
          </div>
        )}
      </Drawer>
    </div>
  );
}

export function AdminBackupsPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [restoreOpen, setRestoreOpen] = useState(false);
  const backupsQuery = useQuery({
    queryKey: ["admin-backups"],
    queryFn: () => api.get("/admin/backups").then((response) => response.data),
  });
  const monitoringQuery = useQuery({
    queryKey: ["admin-monitoring"],
    queryFn: () => api.get("/admin/monitoring").then((response) => response.data),
  });
  const createMutation = useMutation({
    mutationFn: () => api.post("/admin/backups"),
    onSuccess: () => {
      toast("Резервная копия обновлена", "success");
      queryClient.invalidateQueries({ queryKey: ["admin-backups"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const restoreMutation = useMutation({
    mutationFn: () => api.post("/admin/backups/restore"),
    onSuccess: () => {
      toast("База восстановлена", "success");
      setRestoreOpen(false);
      queryClient.invalidateQueries();
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  const data = backupsQuery.data ?? {};
  const file = data.file;
  const settings = data.settings ?? {};
  const summary = monitoringQuery.data?.summary ?? {};
  const tables = monitoringQuery.data?.tables ?? [];
  const enabled = settings["backup.enabled"] !== false;
  const schedule = settings["backup.schedule_time"] ?? "03:00";
  const lastStatus = settings["backup.last_status"] ?? "never";
  const lastError = settings["backup.last_error"];

  return (
    <div>
      <PageHeader
        title="Резервное копирование и мониторинг"
        subtitle="Одна актуальная копия, обновляется по расписанию или вручную."
        actions={
          <>
            <Button variant="secondary" onClick={() => { monitoringQuery.refetch(); backupsQuery.refetch(); }}>
              <RefreshCw size={15} /> Обновить
            </Button>
            <Button variant="secondary" onClick={() => downloadFile(api, "/admin/backups/download", "sunstay_latest.dump")}>
              <Download size={15} /> Скачать копию
            </Button>
            <Button onClick={() => createMutation.mutate()} disabled={createMutation.isPending}>
              <DatabaseBackup size={15} /> Создать сейчас
            </Button>
          </>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card><p className="label">Размер БД</p><p className="kpi-value mt-2">{formatNumber((summary.db_size ?? 0) / 1024 / 1024)} МБ</p></Card>
        <Card><p className="label">Активные соединения</p><p className="kpi-value mt-2">{summary.active_connections ?? 0}</p></Card>
        <Card>
          <p className="label">Последняя копия</p>
          <p className="mt-2 text-sm font-semibold">{file ? formatDateTime(file.updated_at) : "—"}</p>
          <p className="mt-1 text-xs text-muted">{file ? `${formatNumber(file.size / 1024)} КБ` : "Копия ещё не создана"}</p>
        </Card>
        <Card>
          <p className="label">Расписание</p>
          <p className="mt-2 text-sm font-semibold">{enabled ? `Ежедневно в ${schedule}` : "Выключено"}</p>
          <p className={`mt-1 text-xs ${lastStatus === "error" ? "text-rose-600" : "text-muted"}`}>
            Статус: {lastStatus === "success" ? "успешно" : lastStatus === "error" ? "ошибка" : "ещё не запускалось"}
          </p>
        </Card>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-[1.2fr_1fr]">
        <Card>
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="font-display text-2xl font-semibold">Актуальная копия</h2>
              <p className="text-sm text-muted">Файл перезаписывается при каждом запуске.</p>
            </div>
            <Badge tone={file ? "success" : "warning"}>{file ? "готова" : "нет копии"}</Badge>
          </div>
          <div className="mt-5 rounded-xl bg-surface2 p-4 text-sm">
            <p className="font-mono text-xs">{file?.filename ?? "sunstay_latest.dump"}</p>
            <p className="mt-2 text-muted">Обновлено: {file ? formatDateTime(file.updated_at) : "—"}</p>
            <p className="text-muted">Размер: {file ? `${formatNumber(file.size / 1024)} КБ` : "—"}</p>
            {lastError && <p className="mt-2 text-rose-600">{lastError}</p>}
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <Button variant="secondary" onClick={() => downloadFile(api, "/admin/backups/download", "sunstay_latest.dump")}>
              <Download size={15} /> Скачать
            </Button>
            <Button variant="danger" onClick={() => setRestoreOpen(true)} disabled={!file}>
              <RefreshCw size={15} /> Восстановить
            </Button>
          </div>
          <p className="mt-4 text-xs leading-5 text-muted">
            Восстановление заменит текущие данные. Используйте только на учебном стенде.
          </p>
        </Card>

        <Card>
          <h2 className="font-display text-2xl font-semibold">Телеметрия инфраструктуры</h2>
          <div className="mt-4 space-y-2">
            {tables.map((table: any) => (
              <div key={table.relname} className="flex items-center justify-between rounded-xl border border-line px-3 py-2 text-sm">
                <span>{table.relname}</span>
                <span className="text-muted">{formatNumber(table.n_live_tup)} строк · {formatNumber(table.size / 1024)} КБ</span>
              </div>
            ))}
          </div>
          {monitoringQuery.isError && <ErrorState message={getErrorMessage(monitoringQuery.error)} />}
        </Card>
      </div>

      <Modal
        open={restoreOpen}
        title="Восстановление базы"
        subtitle={file?.filename ?? ""}
        onClose={() => setRestoreOpen(false)}
        footer={<><Button variant="secondary" onClick={() => setRestoreOpen(false)}>Отмена</Button><Button variant="danger" onClick={() => restoreMutation.mutate()} disabled={restoreMutation.isPending}>Подтвердить восстановление</Button></>}
      >
        <p className="text-sm text-muted">Текущие данные будут заменены содержимым актуальной копии.</p>
      </Modal>
    </div>
  );
}

export function AdminSettingsPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["admin-settings"], queryFn: () => api.get("/admin/settings").then((response) => response.data) });
  const [form, setForm] = useState<Record<string, any>>({});
  useEffect(() => {
    if (!query.data) return;
    const next: Record<string, any> = {};
    for (const row of query.data) next[row.key] = row.value;
    setForm(next);
  }, [query.data]);
  const mutation = useMutation({
    mutationFn: () => api.put("/admin/settings", form),
    onSuccess: () => { toast("Настройки сохранены", "success"); queryClient.invalidateQueries({ queryKey: ["admin-settings"] }); },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  if (query.isLoading) return <Spinner />;
  if (query.isError) return <ErrorState message={getErrorMessage(query.error)} />;

  return (
    <div>
      <PageHeader title="Параметры системы" subtitle="Отель, оформление, безопасность и резервное копирование." actions={<Button onClick={() => mutation.mutate()} disabled={mutation.isPending}><Save size={15} /> Сохранить</Button>} />
      <div className="grid gap-5 xl:grid-cols-2">
        <Card className="space-y-4">
          <h2 className="font-display text-2xl font-semibold">1. Отель</h2>
          <Input label="Название" value={form["hotel.name"] ?? ""} onChange={(event) => setForm({ ...form, "hotel.name": event.target.value })} />
          <Input label="Адрес" value={form["hotel.address"] ?? ""} onChange={(event) => setForm({ ...form, "hotel.address": event.target.value })} />
          <Input label="Телефон" value={form["hotel.phone"] ?? ""} onChange={(event) => setForm({ ...form, "hotel.phone": event.target.value })} />
          <Input label="Email" value={form["hotel.email"] ?? ""} onChange={(event) => setForm({ ...form, "hotel.email": event.target.value })} />
        </Card>
        <Card className="space-y-4">
          <h2 className="font-display text-2xl font-semibold">2. Оформление</h2>
          <Select label="Тема по умолчанию" value={form["app.default_theme"] ?? "light"} onChange={(event) => setForm({ ...form, "app.default_theme": event.target.value })}>
            <option value="light">Светлая</option><option value="dark">Тёмная</option><option value="system">Системная</option>
          </Select>
          <Select label="Язык по умолчанию" value={form["app.default_language"] ?? "ru"} onChange={(event) => setForm({ ...form, "app.default_language": event.target.value })}>
            <option value="ru">Русский</option><option value="en">English</option>
          </Select>
        </Card>
        <Card className="space-y-4">
          <h2 className="font-display text-2xl font-semibold">3. Безопасность</h2>
          <Input label="Таймаут сессии, мин" type="number" value={form["security.session_timeout_minutes"] ?? 120} onChange={(event) => setForm({ ...form, "security.session_timeout_minutes": Number(event.target.value) })} />
          <Input label="Максимум попыток входа" type="number" value={form["security.max_login_attempts"] ?? 5} onChange={(event) => setForm({ ...form, "security.max_login_attempts": Number(event.target.value) })} />
        </Card>
        <Card className="space-y-4">
          <h2 className="font-display text-2xl font-semibold">4. Резервное копирование</h2>
          <Select label="Включено" value={String(form["backup.enabled"] ?? true)} onChange={(event) => setForm({ ...form, "backup.enabled": event.target.value === "true" })}>
            <option value="true">Да</option>
            <option value="false">Нет</option>
          </Select>
          <Input label="Время обновления" type="time" value={form["backup.schedule_time"] ?? "03:00"} onChange={(event) => setForm({ ...form, "backup.schedule_time": event.target.value })} />
          <div className="rounded-xl bg-surface2 p-3 text-xs text-muted">
            <p>Одна копия <span className="font-mono">sunstay_latest.dump</span> перезаписывается при каждом запуске.</p>
            <p className="mt-1">Последний запуск: {form["backup.last_run_at"] ? formatDateTime(form["backup.last_run_at"]) : "—"}</p>
            <p>Статус: {form["backup.last_status"] ?? "never"}</p>
          </div>
          <p className="text-xs text-muted">Создать копию вручную и скачать её можно на странице «Бэкапы».</p>
        </Card>
      </div>
    </div>
  );
}

```

## `frontend/src/pages/GuestPages.tsx`

```tsx
import {
  ArrowRight,
  BedDouble,
  CalendarDays,
  CheckCircle2,
  Circle,
  Download,
  Keyboard,
  Mail,
  Minus,
  Phone,
  Plus,
  ReceiptText,
  Save,
  ShieldCheck,
  Sparkles,
  Trash2,
  UserRound,
} from "lucide-react";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, downloadFile, getErrorMessage } from "../lib/api";
import { useAuth } from "../lib/auth";
import { useI18n } from "../lib/i18n";
import { useToast } from "../components/ui";
import { Button, Card, Drawer, EmptyState, ErrorState, Input, KpiCard, Modal, PageHeader, Select, Spinner, StatusPill, Tabs } from "../components/ui";
import { formatDate, formatDateTime, formatMoney, LINE_TYPE_LABELS, PAYMENT_METHOD_LABELS, statusLabel } from "../lib/utils";

function GuestPage({ children }: { children: ReactNode }) {
  return <>{children}</>;
}

export function GuestDashboardPage() {
  const { user } = useAuth();
  const firstName = user?.full_name?.split(" ")[0] ?? "гость";
  const query = useQuery({
    queryKey: ["guest-dashboard"],
    queryFn: () => api.get("/guest/dashboard").then((response) => response.data),
  });
  if (query.isLoading) return <Spinner />;
  if (query.isError) return <ErrorState message={getErrorMessage(query.error)} />;
  const data = query.data;
  const upcoming = data.upcoming;

  return (
    <GuestPage>
      <PageHeader
        title={`Добрый день, ${firstName}`}
        subtitle="Ваши бронирования, счета и дополнительные услуги в одном месте."
        actions={<Link to="/search" className="btn-primary">Забронировать ещё</Link>}
      />
      <div className="grid gap-5 lg:grid-cols-[1.5fr_1fr]">
        <div className="space-y-5">
          {upcoming ? (
            <Card className="overflow-hidden p-0">
              <div className="grid md:grid-cols-[220px_1fr]">
                <div className="relative min-h-48 bg-gradient-to-br from-[#c8d5c8] via-[#8faF9b] to-[#2f5147]">
                  <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_20%,rgba(255,255,255,0.35),transparent_12rem)]" />
                  <span className="absolute bottom-4 left-4 rounded-full bg-black/25 px-3 py-1 text-[11px] font-semibold text-white">SunStay</span>
                </div>
                <div className="p-6">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <p className="label text-terracotta">Ближайшая поездка</p>
                      <h2 className="mt-2 font-display text-3xl font-semibold">{upcoming.room_type}, №{upcoming.room_number}</h2>
                      <p className="mt-1 text-sm text-muted">{formatDate(upcoming.checkin_date)} — {formatDate(upcoming.checkout_date)}</p>
                    </div>
                    <StatusPill status={upcoming.status} />
                  </div>
                  <div className="mt-5 flex flex-wrap gap-2">
                    <Link to={`/me/bookings/${upcoming.booking_id}`} className="btn-primary">Подробнее</Link>
                    <Link to={`/me/services?booking=${upcoming.booking_id}`} className="btn-secondary">Заказать услугу</Link>
                    <Link to="/me/invoices" className="btn-ghost">Мои счета</Link>
                  </div>
                </div>
              </div>
            </Card>
          ) : (
            <Card>
              <EmptyState title="Нет предстоящих поездок" description="Выберите номер и оформите бронирование онлайн." action={<Link to="/search" className="btn-primary">Найти номер</Link>} />
            </Card>
          )}

          <Card>
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-display text-2xl font-semibold">История бронирований</h2>
              <Link to="/me/bookings" className="text-sm font-semibold text-terracotta">Все брони →</Link>
            </div>
            {(data.recent_bookings ?? []).length ? (
              <div className="space-y-2">
                {data.recent_bookings.map((booking: any) => (
                  <Link key={booking.booking_id} to={`/me/bookings/${booking.booking_id}`} className="flex items-center justify-between gap-3 rounded-xl border border-line px-4 py-3 text-sm hover:bg-surface2">
                    <div>
                      <p className="font-semibold text-ink">#{booking.booking_id} · {booking.room_type}, №{booking.room_number}</p>
                      <p className="text-xs text-muted">{formatDate(booking.checkin_date)} — {formatDate(booking.checkout_date)}</p>
                    </div>
                    <StatusPill status={booking.status} />
                  </Link>
                ))}
              </div>
            ) : <EmptyState />}
          </Card>
        </div>

        <div className="space-y-5">
          <Card>
            <p className="label">Баланс по последнему счёту</p>
            {data.folio ? (
              <>
                <p className="mt-3 font-display text-3xl font-semibold">{formatMoney(data.folio.balance)}</p>
                <div className="mt-4 space-y-2 text-sm text-muted">
                  <div className="flex justify-between"><span>Начислено</span><span>{formatMoney(data.folio.charged_total)}</span></div>
                  <div className="flex justify-between"><span>Оплачено</span><span>{formatMoney(data.folio.paid_total)}</span></div>
                </div>
                <Link to="/me/invoices" className="btn-secondary mt-4 w-full">Открыть счета</Link>
              </>
            ) : <p className="mt-3 text-sm text-muted">Счетов пока нет.</p>}
          </Card>
          <Card>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="font-display text-xl font-semibold">Рекомендуем</h2>
              <Sparkles size={18} className="text-terracotta" />
            </div>
            <div className="space-y-2">
              {(data.recommended_services ?? []).map((service: any) => (
                <div key={service.service_id} className="flex items-center justify-between gap-3 rounded-xl bg-surface2 px-3 py-2 text-sm">
                  <span>{service.name}</span>
                  <span className="font-semibold">{formatMoney(service.price)}</span>
                </div>
              ))}
            </div>
            <Link to="/me/services" className="btn-primary mt-4 w-full">Заказать услугу</Link>
          </Card>
        </div>
      </div>
    </GuestPage>
  );
}

export function GuestBookingsPage() {
  const [tab, setTab] = useState("all");
  const [cancelId, setCancelId] = useState<number | null>(null);
  const [reasonId, setReasonId] = useState<number | "">("");
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const bookingsQuery = useQuery({
    queryKey: ["guest-bookings"],
    queryFn: () => api.get("/guest/bookings").then((response) => response.data),
  });
  const reasonsQuery = useQuery({
    queryKey: ["cancellation-reasons"],
    queryFn: () => api.get("/public/cancellation-reasons").then((response) => response.data),
  });
  const cancelMutation = useMutation({
    mutationFn: () => api.post(`/guest/bookings/${cancelId}/cancel`, null, { params: { reason_id: reasonId || undefined } }),
    onSuccess: () => {
      toast("Бронирование отменено", "success");
      setCancelId(null);
      queryClient.invalidateQueries({ queryKey: ["guest-bookings"] });
      queryClient.invalidateQueries({ queryKey: ["guest-dashboard"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  const items = bookingsQuery.data ?? [];
  const filtered = useMemo(() => {
    if (tab === "upcoming") return items.filter((item: any) => ["NEW", "CONFIRMED", "CHECKED_IN"].includes(item.status));
    if (tab === "history") return items.filter((item: any) => item.status === "CHECKED_OUT");
    if (tab === "cancelled") return items.filter((item: any) => ["CANCELLED", "NO_SHOW"].includes(item.status));
    return items;
  }, [items, tab]);

  if (bookingsQuery.isLoading) return <Spinner />;
  if (bookingsQuery.isError) return <ErrorState message={getErrorMessage(bookingsQuery.error)} />;

  return (
    <div>
      <PageHeader title="Мои бронирования" subtitle="Предстоящие поездки, история проживаний и отмены." actions={<Link to="/search" className="btn-primary">Новая бронь</Link>} />
      <Tabs
        className="mb-4"
        value={tab}
        onChange={setTab}
        items={[
          { value: "all", label: "Все", count: items.length },
          { value: "upcoming", label: "Предстоящие" },
          { value: "history", label: "История" },
          { value: "cancelled", label: "Отменённые" },
        ]}
      />
      {!filtered.length ? <EmptyState title="Бронирований нет" /> : (
        <div className="space-y-3">
          {filtered.map((booking: any) => (
            <Card key={booking.booking_id} className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <p className="font-display text-xl font-semibold">#{booking.booking_id}</p>
                  <StatusPill status={booking.status} />
                </div>
                <p className="mt-1 text-sm text-muted">{booking.room_type}, №{booking.room_number} · {formatDate(booking.checkin_date)} — {formatDate(booking.checkout_date)}</p>
                <p className="mt-1 text-xs text-muted">Источник: {booking.source} · Баланс: {formatMoney(booking.balance)}</p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Link to={`/me/bookings/${booking.booking_id}`} className="btn-secondary btn-sm">Подробнее</Link>
                {["NEW", "CONFIRMED"].includes(booking.status) && (
                  <Button variant="ghost" size="sm" onClick={() => setCancelId(booking.booking_id)}>Отменить</Button>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
      <Modal
        open={Boolean(cancelId)}
        title="Отмена бронирования"
        subtitle="Укажите причину — менеджер увидит её в системе."
        onClose={() => setCancelId(null)}
        footer={<><Button variant="secondary" onClick={() => setCancelId(null)}>Не отменять</Button><Button variant="danger" onClick={() => cancelMutation.mutate()} disabled={cancelMutation.isPending}>Подтвердить отмену</Button></>}
      >
        <Select label="Причина отмены" value={reasonId} onChange={(event) => setReasonId(event.target.value ? Number(event.target.value) : "")}>
          <option value="">Без причины</option>
          {(reasonsQuery.data ?? []).map((reason: any) => <option key={reason.reason_id} value={reason.reason_id}>{reason.name}</option>)}
        </Select>
      </Modal>
    </div>
  );
}

export function GuestBookingDetailPage() {
  const { id } = useParams();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [cancelOpen, setCancelOpen] = useState(false);
  const [reasonId, setReasonId] = useState<number | "">("");
  const query = useQuery({
    queryKey: ["guest-booking", id],
    queryFn: () => api.get(`/guest/bookings/${id}`).then((response) => response.data),
    enabled: Boolean(id),
  });
  const reasonsQuery = useQuery({
    queryKey: ["cancellation-reasons"],
    queryFn: () => api.get("/public/cancellation-reasons").then((response) => response.data),
  });
  const cancelMutation = useMutation({
    mutationFn: () => api.post(`/guest/bookings/${id}/cancel`, null, { params: { reason_id: reasonId || undefined } }),
    onSuccess: () => {
      toast("Бронирование отменено", "success");
      setCancelOpen(false);
      queryClient.invalidateQueries({ queryKey: ["guest-booking", id] });
      queryClient.invalidateQueries({ queryKey: ["guest-bookings"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  if (query.isLoading) return <Spinner />;
  if (query.isError) return <ErrorState message={getErrorMessage(query.error)} />;
  const { booking, services, folio, timeline } = query.data;

  return (
    <div>
      <PageHeader
        title={`Бронирование #${booking.booking_id}`}
        subtitle={`${booking.room_type}, номер ${booking.room_number} · ${formatDate(booking.checkin_date)} — ${formatDate(booking.checkout_date)}`}
        actions={<Link to="/me/bookings" className="btn-secondary">Назад</Link>}
      />
      <div className="grid gap-5 lg:grid-cols-[1.4fr_1fr]">
        <div className="space-y-5">
          <Card>
            <div className="flex items-center justify-between gap-3">
              <h2 className="font-display text-2xl font-semibold">Статус</h2>
              <StatusPill status={booking.status} />
            </div>
            <div className="mt-5 space-y-3">
              {timeline.map((step: any, index: number) => (
                <div key={step.label} className="flex items-start gap-3">
                  <span className={`mt-0.5 flex h-7 w-7 items-center justify-center rounded-full ${step.done ? "bg-success/15 text-success" : "bg-surface2 text-muted"}`}>
                    {step.done ? <CheckCircle2 size={16} /> : <Circle size={16} />}
                  </span>
                  <div>
                    <p className="text-sm font-semibold text-ink">{step.label}</p>
                    <p className="text-xs text-muted">{step.date ? formatDateTime(step.date) : "Ожидается"}</p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
          <Card>
            <h2 className="font-display text-2xl font-semibold">Услуги</h2>
            {services.length ? (
              <div className="mt-4 space-y-2">
                {services.map((service: any) => (
                  <div key={service.order_id} className="flex items-center justify-between rounded-xl border border-line px-4 py-3 text-sm">
                    <span>{service.name} × {service.quantity}</span>
                    <span className="font-semibold">{formatMoney(service.total)}</span>
                  </div>
                ))}
              </div>
            ) : <p className="mt-3 text-sm text-muted">Дополнительные услуги не заказаны.</p>}
          </Card>
        </div>
        <div className="space-y-5">
          <Card>
            <h2 className="font-display text-2xl font-semibold">Проживание</h2>
            <div className="mt-4 space-y-2 text-sm text-muted">
              <div className="flex justify-between"><span>Заезд</span><span>{formatDate(booking.checkin_date)}</span></div>
              <div className="flex justify-between"><span>Выезд</span><span>{formatDate(booking.checkout_date)}</span></div>
              <div className="flex justify-between"><span>Гостей</span><span>{booking.adults + booking.children}</span></div>
              <div className="flex justify-between"><span>Тариф</span><span>{booking.rate_name}</span></div>
            </div>
            {folio && (
              <div className="mt-4 rounded-xl bg-surface2 p-4">
                <p className="label">Баланс folio</p>
                <p className="mt-2 font-display text-2xl font-semibold">{formatMoney(folio.balance)}</p>
                <div className="mt-2 flex justify-between text-xs text-muted"><span>Начислено</span><span>{formatMoney(folio.charged_total)}</span></div>
                <div className="flex justify-between text-xs text-muted"><span>Оплачено</span><span>{formatMoney(folio.paid_total)}</span></div>
              </div>
            )}
          </Card>
          <Card className="space-y-2">
            <Link to={`/me/services?booking=${booking.booking_id}`} className="btn-primary w-full">Заказать услугу</Link>
            {folio && <Button variant="secondary" className="w-full" onClick={() => downloadFile(api, `/guest/folios/${folio.folio_id}/pdf`, `folio-${folio.folio_id}.pdf`)}><Download size={15} /> Скачать счёт</Button>}
            {["NEW", "CONFIRMED"].includes(booking.status) && <Button variant="ghost" className="w-full" onClick={() => setCancelOpen(true)}>Отменить</Button>}
          </Card>
        </div>
      </div>
      <Modal
        open={cancelOpen}
        title="Отмена бронирования"
        subtitle="Укажите причину отмены."
        onClose={() => setCancelOpen(false)}
        footer={<><Button variant="secondary" onClick={() => setCancelOpen(false)}>Не отменять</Button><Button variant="danger" onClick={() => cancelMutation.mutate()} disabled={cancelMutation.isPending}>Подтвердить отмену</Button></>}
      >
        <Select label="Причина" value={reasonId} onChange={(event) => setReasonId(event.target.value ? Number(event.target.value) : "")}>
          <option value="">Без причины</option>
          {(reasonsQuery.data ?? []).map((reason: any) => <option key={reason.reason_id} value={reason.reason_id}>{reason.name}</option>)}
        </Select>
      </Modal>
    </div>
  );
}

export function GuestInvoicesPage() {
  const [folioId, setFolioId] = useState<number | null>(null);
  const listQuery = useQuery({
    queryKey: ["guest-folios"],
    queryFn: () => api.get("/guest/folios").then((response) => response.data),
  });
  const detailQuery = useQuery({
    queryKey: ["guest-folio", folioId],
    queryFn: () => api.get(`/guest/folios/${folioId}`).then((response) => response.data),
    enabled: Boolean(folioId),
  });
  if (listQuery.isLoading) return <Spinner />;
  if (listQuery.isError) return <ErrorState message={getErrorMessage(listQuery.error)} />;
  const items = listQuery.data ?? [];

  return (
    <div>
      <PageHeader title="Счета и платежи" subtitle="Начисления, оплаты и закрытые folio по вашим проживаниям." />
      {!items.length ? <EmptyState title="Счетов пока нет" description="Они появятся после заселения." /> : (
        <div className="table-wrap">
          <table className="table-base">
            <thead><tr><th>Folio</th><th>Бронь</th><th>Период</th><th>Начислено</th><th>Оплачено</th><th>Баланс</th><th>Статус</th><th /></tr></thead>
            <tbody>
              {items.map((folio: any) => (
                <tr key={folio.folio_id}>
                  <td className="font-semibold">#{folio.folio_id}</td>
                  <td>#{folio.booking_id}</td>
                  <td>{formatDate(folio.opened_at)} — {folio.closed_at ? formatDate(folio.closed_at) : "открыт"}</td>
                  <td>{formatMoney(folio.charged_total)}</td>
                  <td>{formatMoney(folio.paid_total)}</td>
                  <td className="font-semibold">{formatMoney(folio.balance)}</td>
                  <td><StatusPill status={folio.status === "OPEN" ? "ASSIGNED" : "DONE"} /></td>
                  <td className="text-right">
                    <Button variant="ghost" size="sm" onClick={() => setFolioId(folio.folio_id)}>Открыть</Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <Drawer
        open={Boolean(folioId)}
        title={`Счёт Folio #${folioId ?? ""}`}
        subtitle="Детализация начислений и платежей"
        onClose={() => setFolioId(null)}
        footer={<Button variant="secondary" onClick={() => folioId && downloadFile(api, `/guest/folios/${folioId}/pdf`, `folio-${folioId}.pdf`)}><Download size={15} /> Скачать PDF</Button>}
      >
        {detailQuery.isLoading && <Spinner />}
        {detailQuery.isError && <ErrorState message={getErrorMessage(detailQuery.error)} />}
        {detailQuery.data && (
          <div className="space-y-5">
            <div className="rounded-2xl bg-surface2 p-4">
              <p className="label">Баланс</p>
              <p className="mt-1 font-display text-3xl font-semibold">{formatMoney(detailQuery.data.folio.balance)}</p>
            </div>
            <div>
              <h3 className="font-display text-xl font-semibold">Начисления</h3>
              <div className="mt-2 space-y-2">
                {detailQuery.data.charges.map((line: any) => (
                  <div key={line.line_id} className="flex justify-between gap-3 rounded-xl border border-line px-3 py-2 text-sm">
                    <div><p>{line.description}</p><p className="text-xs text-muted">{LINE_TYPE_LABELS[line.line_type] ?? line.line_type} · {formatDate(line.charge_date)}</p></div>
                    <span className="font-semibold">{formatMoney(line.amount)}</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h3 className="font-display text-xl font-semibold">Платежи</h3>
              <div className="mt-2 space-y-2">
                {detailQuery.data.payments.map((payment: any) => (
                  <div key={payment.payment_id} className="flex justify-between gap-3 rounded-xl border border-line px-3 py-2 text-sm">
                    <div><p>{PAYMENT_METHOD_LABELS[payment.method] ?? payment.method}</p><p className="text-xs text-muted">{formatDateTime(payment.paid_at)}</p></div>
                    <span className="font-semibold text-success">{formatMoney(payment.amount)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </Drawer>
    </div>
  );
}

export function GuestServicesPage() {
  const [params] = useSearchParams();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const bookingsQuery = useQuery({
    queryKey: ["guest-bookings"],
    queryFn: () => api.get("/guest/bookings").then((response) => response.data),
  });
  const servicesQuery = useQuery({
    queryKey: ["public-services"],
    queryFn: () => api.get("/public/services").then((response) => response.data),
  });
  const activeBookings = (bookingsQuery.data ?? []).filter((booking: any) => booking.status === "CHECKED_IN");
  const [bookingId, setBookingId] = useState<number | null>(() => (params.get("booking") ? Number(params.get("booking")) : null));
  useEffect(() => {
    if (!bookingId && activeBookings.length) setBookingId(activeBookings[0].booking_id);
  }, [activeBookings, bookingId]);
  const [cart, setCart] = useState<Record<number, number>>({});
  const total = (servicesQuery.data ?? []).reduce((sum: number, service: any) => sum + Number(service.price) * (cart[service.service_id] ?? 0), 0);
  const orderMutation = useMutation({
    mutationFn: async () => {
      const entries = Object.entries(cart).filter(([, quantity]) => quantity > 0);
      for (const [serviceId, quantity] of entries) {
        await api.post(`/guest/bookings/${bookingId}/services`, { service_id: Number(serviceId), quantity });
      }
    },
    onSuccess: () => {
      toast("Услуги добавлены в счёт", "success");
      setCart({});
      queryClient.invalidateQueries({ queryKey: ["guest-dashboard"] });
      queryClient.invalidateQueries({ queryKey: ["guest-bookings"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  if (bookingsQuery.isLoading || servicesQuery.isLoading) return <Spinner />;
  if (bookingsQuery.isError) return <ErrorState message={getErrorMessage(bookingsQuery.error)} />;

  return (
    <div>
      <PageHeader title="Дополнительные услуги" subtitle="Завтраки, парковка, трансфер и СПА — всё добавляется в folio." />
      {!activeBookings.length ? (
        <Card><EmptyState title="Нет активного проживания" description="Заказать услуги можно после заселения." action={<Link to="/me/bookings" className="btn-secondary">Мои брони</Link>} /></Card>
      ) : (
        <div className="grid gap-5 lg:grid-cols-[1fr_320px]">
          <div className="grid gap-4 sm:grid-cols-2">
            {(servicesQuery.data ?? []).map((service: any) => (
              <Card key={service.service_id} className="flex flex-col justify-between">
                <div>
                  <div className="flex items-start justify-between gap-3">
                    <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-terracotta/12 text-terracotta"><Sparkles size={20} /></span>
                    <span className="font-display text-xl font-semibold">{formatMoney(service.price)}</span>
                  </div>
                  <h3 className="mt-4 font-display text-2xl font-semibold">{service.name}</h3>
                  <p className="mt-1 text-xs text-muted">Единица: {service.unit}</p>
                </div>
                <div className="mt-4 flex items-center justify-between">
                  <div className="flex items-center gap-2 rounded-xl border border-line p-1">
                    <button className="rounded-lg p-1.5 text-muted hover:bg-surface2" onClick={() => setCart((current) => ({ ...current, [service.service_id]: Math.max(0, (current[service.service_id] ?? 0) - 1) }))}><Minus size={15} /></button>
                    <span className="w-7 text-center text-sm font-semibold">{cart[service.service_id] ?? 0}</span>
                    <button className="rounded-lg p-1.5 text-muted hover:bg-surface2" onClick={() => setCart((current) => ({ ...current, [service.service_id]: (current[service.service_id] ?? 0) + 1 }))}><Plus size={15} /></button>
                  </div>
                  <Button size="sm" variant="secondary" onClick={() => setCart((current) => ({ ...current, [service.service_id]: (current[service.service_id] ?? 0) + 1 }))}>Добавить</Button>
                </div>
              </Card>
            ))}
          </div>
          <Card className="h-fit space-y-4">
            <p className="label">Заказ</p>
            <Select label="Бронь" value={bookingId ?? ""} onChange={(event) => setBookingId(Number(event.target.value))}>
              {activeBookings.map((booking: any) => <option key={booking.booking_id} value={booking.booking_id}>#{booking.booking_id} · {booking.room_type}, №{booking.room_number}</option>)}
            </Select>
            <div className="space-y-2 text-sm">
              {Object.entries(cart).filter(([, quantity]) => quantity > 0).map(([serviceId, quantity]) => {
                const service = (servicesQuery.data ?? []).find((item: any) => item.service_id === Number(serviceId));
                if (!service) return null;
                return <div key={serviceId} className="flex justify-between"><span className="text-muted">{service.name} × {quantity}</span><span>{formatMoney(Number(service.price) * quantity)}</span></div>;
              })}
              {!Object.values(cart).some((quantity) => quantity > 0) && <p className="text-muted">Выберите услуги слева.</p>}
            </div>
            <div className="divider" />
            <div className="flex justify-between font-semibold"><span>Итого</span><span>{formatMoney(total)}</span></div>
            <Button className="w-full" disabled={!bookingId || !Object.values(cart).some((quantity) => quantity > 0) || orderMutation.isPending} onClick={() => orderMutation.mutate()}>Оформить заказ</Button>
            <Button variant="ghost" className="w-full" onClick={() => setCart({})}>Отмена</Button>
          </Card>
        </div>
      )}
    </div>
  );
}

export function GuestProfilePage() {
  const { user, settings, updateSettings } = useAuth();
  const { setLang } = useI18n();
  const { toast } = useToast();
  const [form, setForm] = useState(settings);
  useEffect(() => setForm(settings), [settings]);
  const saveMutation = useMutation({
    mutationFn: () => updateSettings(form),
    onSuccess: () => {
      toast("Настройки сохранены", "success");
      setLang(form.language);
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  return (
    <div>
      <PageHeader
        title="Профиль и оформление"
        subtitle="Настройки хранятся на сервере и применяются при следующем входе."
        actions={<Button onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending}><Save size={15} /> Сохранить</Button>}
      />
      <div className="grid gap-5 lg:grid-cols-[1fr_1fr]">
        <Card className="space-y-4">
          <h2 className="font-display text-2xl font-semibold">Данные профиля</h2>
          <Input label="ФИО" value={user?.full_name ?? ""} readOnly />
          <Input label="Email" value={user?.email ?? ""} readOnly />
          <Input label="Телефон" value={user?.phone ?? ""} readOnly />
          <p className="text-xs text-muted">Данные профиля изменяются через менеджера отеля.</p>
        </Card>
        <Card className="space-y-5">
          <h2 className="font-display text-2xl font-semibold">Отображение</h2>
          <div>
            <p className="label mb-2">Тема</p>
            <div className="grid grid-cols-3 gap-2">
              {[
                { value: "light", label: "Светлая" },
                { value: "dark", label: "Тёмная" },
                { value: "system", label: "Системная" },
              ].map((item) => (
                <button key={item.value} onClick={() => setForm({ ...form, theme: item.value as any })} className={`rounded-xl border px-3 py-2 text-sm font-semibold ${form.theme === item.value ? "border-terracotta bg-terracotta/10 text-terracotta" : "border-line text-muted"}`}>{item.label}</button>
              ))}
            </div>
          </div>
          <Select label="Язык" value={form.language} onChange={(event) => setForm({ ...form, language: event.target.value as "ru" | "en" })}>
            <option value="ru">Русский</option>
            <option value="en">English</option>
          </Select>
          <Select label="Формат даты" value={form.date_format} onChange={(event) => setForm({ ...form, date_format: event.target.value })}>
            <option value="dd.MM.yyyy">dd.MM.yyyy</option>
            <option value="yyyy-MM-dd">yyyy-MM-dd</option>
          </Select>
          <Select label="Формат чисел" value={form.number_format} onChange={(event) => setForm({ ...form, number_format: event.target.value })}>
            <option value="space_comma">1 234,56</option>
            <option value="comma_dot">1,234.56</option>
          </Select>
          <Select label="Размер страницы" value={form.page_size} onChange={(event) => setForm({ ...form, page_size: Number(event.target.value) })}>
            <option value={10}>10</option>
            <option value={25}>25</option>
            <option value={50}>50</option>
          </Select>
          <div>
            <div className="mb-2 flex items-center justify-between">
              <p className="label">Сохранённые фильтры</p>
              <button className="text-xs font-semibold text-terracotta" onClick={() => window.dispatchEvent(new Event("sunstay:open-hotkeys"))}>Горячие клавиши ?</button>
            </div>
            <div className="space-y-2">
              {(form.saved_filters ?? []).length ? form.saved_filters.map((filter, index) => (
                <div key={index} className="flex items-center justify-between gap-2 rounded-xl border border-line px-3 py-2 text-sm">
                  <span>{String(filter.name ?? `Фильтр ${index + 1}`)}</span>
                  <button className="text-muted hover:text-danger" onClick={() => setForm({ ...form, saved_filters: form.saved_filters.filter((_, i) => i !== index) })}><Trash2 size={15} /></button>
                </div>
              )) : <p className="text-sm text-muted">Пока нет сохранённых фильтров.</p>}
            </div>
          </div>
          <Button className="w-full" onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending}><Save size={15} /> Сохранить настройки</Button>
        </Card>
      </div>
    </div>
  );
}

```

## `frontend/src/pages/ManagerPages.tsx`

```tsx
import {
  AlertTriangle,
  ArrowLeftRight,
  ArrowRight,
  BedDouble,
  CalendarDays,
  Check,
  ChevronLeft,
  ChevronRight,
  CircleDollarSign,
  Download,
  Filter,
  LogIn,
  LogOut,
  Moon,
  Plus,
  ReceiptText,
  RefreshCw,
  Save,
  Search,
  Upload,
  Users,
  X,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, downloadFile, getErrorMessage } from "../lib/api";
import { useAuth } from "../lib/auth";
import { useToast } from "../components/ui";
import {
  Avatar,
  Button,
  Card,
  Drawer,
  EmptyState,
  ErrorState,
  Input,
  KpiCard,
  Modal,
  PageHeader,
  Pagination,
  Select,
  SensitiveValue,
  Spinner,
  StatusPill,
  Tabs,
  Textarea,
} from "../components/ui";
import {
  addDaysISO,
  BOOKING_STATUS_LABELS,
  cn,
  dateRange,
  formatDate,
  formatDateTime,
  formatMoney,
  formatNumber,
  LINE_TYPE_LABELS,
  PAYMENT_METHOD_LABELS,
  statusClass,
  statusLabel,
  todayISO,
} from "../lib/utils";

function NewGuestForm({ onCreated }: { onCreated: (guest: any) => void }) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [form, setForm] = useState({ full_name: "", document_number: "", phone: "", email: "", pdn_consent: true });
  const mutation = useMutation({
    mutationFn: () => api.post("/manager/guests", form).then((response) => response.data),
    onSuccess: (guest) => {
      toast("Гость создан", "success");
      queryClient.invalidateQueries({ queryKey: ["manager-guests"] });
      onCreated(guest);
      setForm({ full_name: "", document_number: "", phone: "", email: "", pdn_consent: true });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  return (
    <div className="space-y-3 rounded-xl border border-line bg-surface2 p-4">
      <div className="grid gap-3 sm:grid-cols-2">
        <Input label="ФИО" value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} />
        <Input label="Документ" value={form.document_number} onChange={(event) => setForm({ ...form, document_number: event.target.value })} />
        <Input label="Телефон" value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} />
        <Input label="Email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
      </div>
      <label className="flex items-center gap-2 text-xs text-muted">
        <input type="checkbox" checked={form.pdn_consent} onChange={(event) => setForm({ ...form, pdn_consent: event.target.checked })} className="h-4 w-4 accent-terracotta" />
        Согласие на обработку ПДн
      </label>
      <Button size="sm" variant="secondary" onClick={() => mutation.mutate()} disabled={mutation.isPending || !form.full_name || !form.document_number}>Создать гостя</Button>
    </div>
  );
}

function NewBookingModal({
  open,
  onClose,
  defaultRoomId,
  defaultDate,
}: {
  open: boolean;
  onClose: () => void;
  defaultRoomId?: number;
  defaultDate?: string;
}) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [guestId, setGuestId] = useState<number | "">("");
  const [roomId, setRoomId] = useState<number | "">(defaultRoomId ?? "");
  const [rateId, setRateId] = useState<number | "">("");
  const [checkin, setCheckin] = useState(defaultDate ?? addDaysISO(todayISO(), 1));
  const [checkout, setCheckout] = useState(addDaysISO(defaultDate ?? addDaysISO(todayISO(), 1), 2));
  const [adults, setAdults] = useState(1);
  const [children, setChildren] = useState(0);
  const [arrivalTime, setArrivalTime] = useState("14:00");
  const [holdMinutes, setHoldMinutes] = useState(60);
  const [source, setSource] = useState("SITE");
  const [guestSearch, setGuestSearch] = useState("");
  const [showGuestForm, setShowGuestForm] = useState(false);

  const guestsQuery = useQuery({ queryKey: ["manager-guests"], queryFn: () => api.get("/manager/guests").then((response) => response.data) });
  const roomsQuery = useQuery({ queryKey: ["manager-rooms"], queryFn: () => api.get("/manager/rooms").then((response) => response.data) });
  const ratesQuery = useQuery({ queryKey: ["manager-rates"], queryFn: () => api.get("/manager/rates").then((response) => response.data) });

  useEffect(() => {
    if (defaultRoomId) setRoomId(defaultRoomId);
    if (defaultDate) {
      setCheckin(defaultDate);
      setCheckout(addDaysISO(defaultDate, 2));
    }
  }, [defaultRoomId, defaultDate]);

  const selectedRoom = (roomsQuery.data ?? []).find((room: any) => room.room_id === Number(roomId));
  const rates = (ratesQuery.data ?? []).filter((rate: any) => !selectedRoom || rate.room_type_id === selectedRoom.room_type_id);
  useEffect(() => {
    if (rates.length && !rates.some((rate: any) => rate.rate_id === Number(rateId))) {
      setRateId(rates[0].rate_id);
    }
  }, [rates, rateId]);

  const guests = (guestsQuery.data ?? []).filter((guest: any) => {
    if (!guestSearch) return true;
    const query = guestSearch.toLowerCase();
    return guest.full_name.toLowerCase().includes(query) || guest.document_number.includes(guestSearch) || (guest.phone ?? "").includes(guestSearch);
  });

  const mutation = useMutation({
    mutationFn: () => api.post("/manager/bookings", {
      guest_id: Number(guestId),
      room_id: Number(roomId),
      rate_id: Number(rateId),
      checkin_date: checkin,
      checkout_date: checkout,
      adults,
      children,
      arrival_time: arrivalTime,
      hold_minutes: holdMinutes,
      source,
    }).then((response) => response.data),
    onSuccess: () => {
      toast("Бронирование создано", "success");
      queryClient.invalidateQueries({ queryKey: ["manager-bookings"] });
      queryClient.invalidateQueries({ queryKey: ["manager-dashboard"] });
      onClose();
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  return (
    <Modal
      open={open}
      title="Новая бронь"
      subtitle="Создание брони для существующего или нового гостя"
      onClose={onClose}
      size="lg"
      footer={<><Button variant="secondary" onClick={onClose}>Отмена</Button><Button onClick={() => mutation.mutate()} disabled={mutation.isPending || !guestId || !roomId || !rateId}>Создать бронь</Button></>}
    >
      <div className="grid gap-5 lg:grid-cols-2">
        <div className="space-y-4">
          <div className="flex items-end gap-2">
            <Input label="Поиск гостя" value={guestSearch} onChange={(event) => setGuestSearch(event.target.value)} placeholder="ФИО, документ, телефон" />
            <Button variant="secondary" size="sm" onClick={() => setShowGuestForm((value) => !value)}><Plus size={14} /> Гость</Button>
          </div>
          {showGuestForm && <NewGuestForm onCreated={(guest) => { setGuestId(guest.guest_id); setShowGuestForm(false); }} />}
          <Select label="Гость" value={guestId} onChange={(event) => setGuestId(Number(event.target.value))}>
            <option value="">Выберите гостя</option>
            {guests.map((guest: any) => <option key={guest.guest_id} value={guest.guest_id}>{guest.full_name} · {guest.document_number}</option>)}
          </Select>
          <Select label="Номер" value={roomId} onChange={(event) => setRoomId(Number(event.target.value))}>
            <option value="">Выберите номер</option>
            {(roomsQuery.data ?? []).map((room: any) => <option key={room.room_id} value={room.room_id}>№{room.room_number} · {room.room_type} · {room.status}</option>)}
          </Select>
          <Select label="Тариф" value={rateId} onChange={(event) => setRateId(Number(event.target.value))}>
            <option value="">Выберите тариф</option>
            {rates.map((rate: any) => <option key={rate.rate_id} value={rate.rate_id}>{rate.name} · {formatMoney(rate.price_per_night)}</option>)}
          </Select>
        </div>
        <div className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2">
            <Input label="Заезд" type="date" value={checkin} onChange={(event) => setCheckin(event.target.value)} />
            <Input label="Выезд" type="date" value={checkout} onChange={(event) => setCheckout(event.target.value)} />
            <Input label="Взрослые" type="number" min={1} value={adults} onChange={(event) => setAdults(Number(event.target.value))} />
            <Input label="Дети" type="number" min={0} value={children} onChange={(event) => setChildren(Number(event.target.value))} />
            <Input label="Время заезда" type="time" value={arrivalTime} onChange={(event) => setArrivalTime(event.target.value)} />
            <Input label="Держать бронь, мин" type="number" min={5} max={1440} value={holdMinutes} onChange={(event) => setHoldMinutes(Number(event.target.value))} />
          </div>
          <Select label="Источник" value={source} onChange={(event) => setSource(event.target.value)}>
            <option value="SITE">Сайт</option>
            <option value="PHONE">Телефон</option>
            <option value="WALK_IN">Walk-in</option>
            <option value="OTA">OTA</option>
          </Select>
          <div className="rounded-xl bg-surface2 p-4 text-sm text-muted">
            <p>Ночей: <span className="font-semibold text-ink">{Math.max(0, Math.round((new Date(checkout).getTime() - new Date(checkin).getTime()) / 86400000))}</span></p>
            <p className="mt-1">Стоимость рассчитывается сервером по тарифу и промокоду.</p>
          </div>
        </div>
      </div>
    </Modal>
  );
}

export function ManagerDashboardPage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [auditOpen, setAuditOpen] = useState(false);
  const [businessDate, setBusinessDate] = useState(todayISO());
  const query = useQuery({
    queryKey: ["manager-dashboard"],
    queryFn: () => api.get("/manager/dashboard").then((response) => response.data),
  });
  const nightAudit = useMutation({
    mutationFn: () => api.post("/manager/night-audit", { business_date: businessDate }).then((response) => response.data),
    onSuccess: (data) => {
      toast(`Ночной аудит завершён: начислено ${data.totals?.posted_count ?? 0}, no-show ${data.totals?.no_show_count ?? 0}`, "success");
      setAuditOpen(false);
      queryClient.invalidateQueries({ queryKey: ["manager-dashboard"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  if (query.isLoading) return <Spinner />;
  if (query.isError) return <ErrorState message={getErrorMessage(query.error)} />;
  const data = query.data;
  const kpi = data.kpi ?? {};
  const occupancy = data.occupancy ?? [];
  const roomStatus = data.room_status ?? [];
  const recentOccupancy = occupancy.filter((row: any) => row.report_date >= addDaysISO(todayISO(), -6) && row.report_date <= todayISO());
  const pieColors = ["#123B36", "#C96F4A", "#E3A857", "#9DB5A4", "#3D6F8E", "#B8504E", "#6E746D"];

  return (
    <div>
      <PageHeader
        title="Операционный обзор"
        subtitle="Загрузка, заезды, выезды и состояние номерного фонда на сегодня."
        actions={
          <>
            <Button variant="secondary" onClick={() => navigate("/app/bookings?new=1")}><Plus size={15} /> Новая бронь</Button>
            <Button variant="secondary" onClick={() => navigate("/app/room-grid")}><CalendarDays size={15} /> Шахматка</Button>
            <Button onClick={() => setAuditOpen(true)}><Moon size={15} /> Ночной аудит</Button>
          </>
        }
      />
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Загрузка" value={`${kpi.occupancy_pct ?? 0}%`} hint={`${kpi.occupied_rooms ?? 0} из ${kpi.total_rooms ?? 0} номеров`} icon={<BedDouble size={20} />} />
        <KpiCard label="ADR" value={formatMoney(kpi.adr_today ?? 0)} hint="Средняя цена номера" icon={<CircleDollarSign size={20} />} tone="terracotta" />
        <KpiCard label="RevPAR" value={formatMoney(kpi.revpar_today ?? 0)} hint="Доход на доступный номер" icon={<ReceiptText size={20} />} tone="amber" />
        <KpiCard label="Выручка сегодня" value={formatMoney(kpi.payments_today ?? 0)} hint={`Заезды: ${kpi.arrivals_today ?? 0} · Выезды: ${kpi.departures_today ?? 0}`} icon={<Users size={20} />} tone="sage" />
      </div>

      <div className="mt-5 grid items-start gap-5 xl:grid-cols-[1.5fr_1fr]">
        <Card>
          <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="font-display text-2xl font-semibold">Загрузка по дням</h2>
              <p className="text-sm text-muted">Последние 7 дней</p>
            </div>
            <Button variant="ghost" size="sm" onClick={() => query.refetch()}><RefreshCw size={14} /> Обновить</Button>
          </div>
          <div className="mb-4 flex items-end justify-between gap-4 rounded-xl bg-surface2 p-4">
            <div>
              <p className="font-display text-4xl font-semibold">{kpi.occupancy_pct ?? 0}%</p>
              <p className="text-sm text-muted">{kpi.occupied_rooms ?? 0} из {kpi.total_rooms ?? 0} номеров</p>
            </div>
            <div className="w-40">
              <div className="h-2 rounded-full bg-surface">
                <div className="h-2 rounded-full bg-terracotta" style={{ width: `${Math.min(100, Number(kpi.occupancy_pct ?? 0))}%` }} />
              </div>
            </div>
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={recentOccupancy}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="report_date" tickFormatter={(value) => formatDate(value).slice(0, 5)} tick={{ fontSize: 11, fill: "var(--muted)" }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: "var(--muted)" }} unit="%" />
                <Tooltip
                  formatter={(value, _name, item: any) => [`${value}% (${item.payload.rooms_occupied}/${item.payload.rooms_available})`, "Загрузка"]}
                  labelFormatter={(value) => formatDate(value)}
                />
                <Bar dataKey="occupancy_pct" fill="#C96F4A" radius={[6, 6, 0, 0]} maxBarSize={42} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
        <Card>
          <h2 className="font-display text-2xl font-semibold">Статусы номеров</h2>
          <div className="mt-2 h-60">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={roomStatus} dataKey="rooms" nameKey="status" innerRadius={55} outerRadius={85} paddingAngle={3}>
                  {roomStatus.map((entry: any, index: number) => <Cell key={entry.status} fill={pieColors[index % pieColors.length]} />)}
                </Pie>
                <Tooltip formatter={(value) => [`${value} номеров`, "Количество"]} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs text-muted">
            {roomStatus.map((item: any, index: number) => (
              <span key={item.status} className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full" style={{ background: pieColors[index % pieColors.length] }} /> {statusLabel(item.status)} · {item.rooms}</span>
            ))}
          </div>
        </Card>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-2">
        <Card>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-display text-2xl font-semibold">Заезды сегодня</h2>
            <Button variant="ghost" size="sm" onClick={() => navigate("/app/bookings")}>Все <ChevronRight size={14} /></Button>
          </div>
          {data.arrivals?.length ? data.arrivals.map((item: any) => (
            <div key={item.booking_id} className="flex items-center justify-between gap-3 border-t border-line py-3 first:border-t-0">
              <div><p className="text-sm font-semibold">{item.guest_name}</p><p className="text-xs text-muted">№{item.room_number} · {formatDate(item.checkin_date)}</p></div>
              <Button variant="ghost" size="sm" onClick={() => navigate(`/app/bookings/${item.booking_id}`)}>Открыть</Button>
            </div>
          )) : <p className="py-6 text-sm text-muted">Заездов на сегодня нет.</p>}
        </Card>
        <Card>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="font-display text-2xl font-semibold">Выезды сегодня</h2>
            <Button variant="ghost" size="sm" onClick={() => navigate("/app/bookings")}>Все <ChevronRight size={14} /></Button>
          </div>
          {data.departures?.length ? data.departures.map((item: any) => (
            <div key={item.booking_id} className="flex items-center justify-between gap-3 border-t border-line py-3 first:border-t-0">
              <div><p className="text-sm font-semibold">{item.guest_name}</p><p className="text-xs text-muted">№{item.room_number} · {formatDate(item.checkout_date)}</p></div>
              <Button variant="ghost" size="sm" onClick={() => navigate(`/app/bookings/${item.booking_id}`)}>Открыть</Button>
            </div>
          )) : <p className="py-6 text-sm text-muted">Выездов на сегодня нет.</p>}
        </Card>
      </div>

      <Modal
        open={auditOpen}
        title="Ночной аудит"
        subtitle="Начисление проживания и фиксация закрытия бизнес-дня"
        onClose={() => setAuditOpen(false)}
        footer={<><Button variant="secondary" onClick={() => setAuditOpen(false)}>Отмена</Button><Button onClick={() => nightAudit.mutate()} disabled={nightAudit.isPending}><Moon size={15} /> Запустить</Button></>}
      >
        <Input label="Бизнес-дата" type="date" value={businessDate} onChange={(event) => setBusinessDate(event.target.value)} />
        <p className="mt-3 text-sm text-muted">Операция атомарная: при ошибке все начисления откатываются.</p>
      </Modal>
    </div>
  );
}

const BOOKING_DOT_COLORS: Record<string, string> = {
  NEW: "bg-amber-500",
  CONFIRMED: "bg-emerald-500",
  CHECKED_IN: "bg-sky-500",
  CHECKED_OUT: "bg-slate-400",
  CANCELLED: "bg-rose-500",
};

export function RoomGridPage() {
  const navigate = useNavigate();
  const [start, setStart] = useState(todayISO());
  const [floor, setFloor] = useState("all");
  const [status, setStatus] = useState("all");
  const [newOpen, setNewOpen] = useState(false);
  const [defaultRoom, setDefaultRoom] = useState<number | undefined>();
  const [defaultDate, setDefaultDate] = useState<string | undefined>();
  const end = addDaysISO(start, 7);
  const query = useQuery({
    queryKey: ["room-grid", start, end],
    queryFn: () => api.get("/manager/room-grid", { params: { start, end } }).then((response) => response.data),
  });
  const days = dateRange(start, addDaysISO(end, -1));
  const rooms = (query.data?.rooms ?? []).filter((room: any) => (floor === "all" || String(room.floor) === floor) && (status === "all" || room.status === status));
  const bookings = query.data?.bookings ?? [];
  const floorOptions = Array.from(new Set((query.data?.rooms ?? []).map((room: any) => room.floor))).sort((a: any, b: any) => a - b);
  const statusOptions = Array.from(new Set((query.data?.rooms ?? []).map((room: any) => room.status)));

  function bookingFor(roomId: number, day: string) {
    return bookings.find((booking: any) => booking.room_id === roomId && day >= booking.checkin_date && day < booking.checkout_date);
  }

  function openNew(roomId: number, day: string) {
    setDefaultRoom(roomId);
    setDefaultDate(day);
    setNewOpen(true);
  }

  return (
    <div>
      <PageHeader
        title="Шахматка номеров"
        subtitle="Визуальная сетка номеров и броней. Нажмите на свободную ячейку, чтобы создать бронь."
        actions={<Button onClick={() => { setDefaultRoom(undefined); setDefaultDate(undefined); setNewOpen(true); }}><Plus size={15} /> Новая бронь</Button>}
      />
      <Card className="mb-4 flex flex-wrap items-center gap-3">
        <Button variant="secondary" size="sm" onClick={() => setStart(addDaysISO(start, -7))}><ChevronLeft size={14} /> Неделя</Button>
        <Button variant="secondary" size="sm" onClick={() => setStart(todayISO())}>Сегодня</Button>
        <Button variant="secondary" size="sm" onClick={() => setStart(addDaysISO(start, 7))}>Неделя <ChevronRight size={14} /></Button>
        <span className="text-sm font-semibold text-ink">{formatDate(days[0])} — {formatDate(days[days.length - 1])}</span>
        <div className="ml-auto flex flex-wrap gap-2">
          <Select value={floor} onChange={(event) => setFloor(event.target.value)}>
            <option value="all">Все этажи</option>
            {floorOptions.map((value: any) => <option key={value} value={value}>{value} этаж</option>)}
          </Select>
          <Select value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="all">Все статусы</option>
            {statusOptions.map((value: any) => <option key={value} value={value}>{statusLabel(value)}</option>)}
          </Select>
        </div>
      </Card>
      {query.isLoading && <Spinner />}
      {query.isError && <ErrorState message={getErrorMessage(query.error)} />}
      {!query.isLoading && !query.isError && (
        <div className="overflow-x-auto rounded-2xl border border-line bg-surface">
          <table className="w-full min-w-[980px] border-collapse text-sm">
            <thead>
              <tr className="bg-tableHeader text-[10px] uppercase tracking-[0.08em] text-muted">
                <th className="sticky left-0 z-10 min-w-[170px] bg-tableHeader px-4 py-3 text-left">Номер</th>
                {days.map((day) => (
                  <th key={day} className="min-w-[120px] border-l border-line px-2 py-3 text-center">
                    <p>{new Intl.DateTimeFormat("ru-RU", { weekday: "short" }).format(new Date(`${day}T12:00:00`))}</p>
                    <p className="mt-1 text-xs font-bold text-ink">{formatDate(day).slice(0, 5)}</p>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rooms.map((room: any) => (
                <tr key={room.room_id} className="border-t border-line">
                  <td className="sticky left-0 z-10 bg-surface px-4 py-2.5">
                    <p className="font-semibold text-ink">№{room.room_number}</p>
                    <p className="text-[11px] text-muted">{room.room_type} · {statusLabel(room.status)}</p>
                  </td>
                  {days.map((day) => {
                    const booking = bookingFor(room.room_id, day);
                    if (booking) {
                      return (
                        <td key={day} className="border-l border-line p-1 align-middle">
                          <button
                            className="flex h-9 w-full items-center justify-center rounded-lg transition hover:bg-surface2"
                            onClick={() => navigate(`/app/bookings/${booking.booking_id}`)}
                            title={`Бронь #${booking.booking_id} · ${statusLabel(booking.status)}`}
                          >
                            <span className={cn("h-3 w-3 rounded-full", BOOKING_DOT_COLORS[booking.status] ?? "bg-muted")} />
                          </button>
                        </td>
                      );
                    }
                    return (
                      <td key={day} className="border-l border-line p-1">
                        <button
                          className="group flex h-9 w-full items-center justify-center rounded-lg border border-dashed border-transparent text-transparent transition hover:border-line hover:bg-surface2 hover:text-muted"
                          onClick={() => openNew(room.room_id, day)}
                          title="Создать бронь"
                        >
                          <Plus size={14} />
                        </button>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="mt-3 flex flex-wrap gap-3 text-xs text-muted">
        {["NEW", "CONFIRMED", "CHECKED_IN", "CHECKED_OUT", "CANCELLED"].map((statusValue) => (
          <span key={statusValue} className="flex items-center gap-2"><span className={cn("h-2.5 w-2.5 rounded-full", BOOKING_DOT_COLORS[statusValue] ?? "bg-muted")} /> {statusLabel(statusValue)}</span>
        ))}
      </div>
      <NewBookingModal open={newOpen} onClose={() => setNewOpen(false)} defaultRoomId={defaultRoom} defaultDate={defaultDate} />
    </div>
  );
}

export function BookingsRegistryPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const { settings, updateSettings } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [status, setStatus] = useState("all");
  const [search, setSearch] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(settings.page_size || 25);
  const [selected, setSelected] = useState<number[]>([]);
  const [newOpen, setNewOpen] = useState(searchParams.get("new") === "1");
  const filters = { status: status === "all" ? undefined : status, search: search || undefined, date_from: dateFrom || undefined, date_to: dateTo || undefined, page, page_size: pageSize };

  const query = useQuery({
    queryKey: ["manager-bookings", filters],
    queryFn: () => api.get("/manager/bookings", { params: filters }).then((response) => response.data),
  });
  const bulkMutation = useMutation({
    mutationFn: async (action: "confirm" | "cancel") => {
      for (const bookingId of selected) {
        if (action === "confirm") await api.post(`/manager/bookings/${bookingId}/confirm`);
        else await api.post(`/manager/bookings/${bookingId}/cancel`);
      }
    },
    onSuccess: () => {
      toast(`Операция выполнена для ${selected.length} броней`, "success");
      setSelected([]);
      queryClient.invalidateQueries({ queryKey: ["manager-bookings"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  useEffect(() => {
    if (searchParams.get("new") === "1") setNewOpen(true);
  }, [searchParams]);

  const items = query.data?.items ?? [];
  const total = query.data?.total ?? 0;
  const allSelected = items.length > 0 && items.every((item: any) => selected.includes(item.booking_id));

  function toggleAll() {
    setSelected(allSelected ? [] : items.map((item: any) => item.booking_id));
  }

  function saveFilter() {
    const name = window.prompt("Название фильтра", `Брони: ${status === "all" ? "все" : statusLabel(status)}`);
    if (!name) return;
    const next = [...(settings.saved_filters ?? []), { name, status, search, date_from: dateFrom, date_to: dateTo }];
    updateSettings({ saved_filters: next }).then(() => toast("Фильтр сохранён", "success")).catch((error) => toast(getErrorMessage(error), "error"));
  }

  function applySavedFilter(index: number) {
    const filter = (settings.saved_filters ?? [])[index];
    if (!filter) return;
    setStatus(String(filter.status ?? "all"));
    setSearch(String(filter.search ?? ""));
    setDateFrom(String(filter.date_from ?? ""));
    setDateTo(String(filter.date_to ?? ""));
    setPage(1);
  }

  return (
    <div>
      <PageHeader
        title="Реестр бронирований"
        subtitle="Поиск, фильтры и массовые операции с бронями."
        actions={
          <>
            <Button variant="secondary" onClick={() => downloadFile(api, "/manager/bookings/export", "bookings.csv", { ...filters, page: undefined, page_size: undefined })}><Download size={15} /> Экспорт CSV</Button>
            <Button onClick={() => setNewOpen(true)}><Plus size={15} /> Новая бронь</Button>
          </>
        }
      />
      <Card className="mb-4 space-y-3">
        <div className="flex flex-wrap items-end gap-2">
          <Input label="Поиск" id="page-search" value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} placeholder="Гость, документ, номер" className="min-w-[220px]" />
          <Input label="С даты" type="date" value={dateFrom} onChange={(event) => { setDateFrom(event.target.value); setPage(1); }} />
          <Input label="По дату" type="date" value={dateTo} onChange={(event) => { setDateTo(event.target.value); setPage(1); }} />
          <Button variant="secondary" onClick={() => setPage(1)}><Filter size={14} /> Применить</Button>
          <Button variant="ghost" onClick={() => { setSearch(""); setDateFrom(""); setDateTo(""); setStatus("all"); setPage(1); }}>Сбросить</Button>
          <Button variant="ghost" onClick={saveFilter}><Save size={14} /> Сохранить фильтр</Button>
          {(settings.saved_filters ?? []).length > 0 && (
            <Select label="Сохранённые фильтры" onChange={(event) => event.target.value && applySavedFilter(Number(event.target.value))}>
              <option value="">Выбрать</option>
              {(settings.saved_filters ?? []).map((filter, index) => <option key={index} value={index}>{String(filter.name ?? `Фильтр ${index + 1}`)}</option>)}
            </Select>
          )}
          <Select label="Строк" value={pageSize} onChange={(event) => { setPageSize(Number(event.target.value)); setPage(1); }}>
            <option value={10}>10</option><option value={25}>25</option><option value={50}>50</option>
          </Select>
        </div>
        <Tabs
          value={status}
          onChange={(value) => { setStatus(value); setPage(1); }}
          items={[
            { value: "all", label: "Все" },
            { value: "NEW", label: "Новые" },
            { value: "CONFIRMED", label: "Подтверждённые" },
            { value: "CHECKED_IN", label: "Заселённые" },
            { value: "CANCELLED", label: "Отменённые" },
          ]}
        />
      </Card>
      {selected.length > 0 && (
        <Card className="mb-4 flex flex-wrap items-center gap-2 border-terracotta/30 bg-terracotta/8">
          <span className="text-sm font-semibold">Выбрано: {selected.length}</span>
          <Button size="sm" variant="secondary" onClick={() => bulkMutation.mutate("confirm")} disabled={bulkMutation.isPending}><Check size={14} /> Подтвердить выбранные</Button>
          <Button size="sm" variant="danger" onClick={() => bulkMutation.mutate("cancel")} disabled={bulkMutation.isPending}><X size={14} /> Отменить выбранные</Button>
        </Card>
      )}
      {query.isLoading && <Spinner />}
      {query.isError && <ErrorState message={getErrorMessage(query.error)} />}
      {!query.isLoading && !query.isError && (
        <div className="table-wrap">
          <table className="table-base">
            <thead>
              <tr>
                <th className="w-10"><input type="checkbox" checked={allSelected} onChange={toggleAll} className="h-4 w-4 accent-terracotta" /></th>
                <th>№</th><th>Гость</th><th>Номер</th><th>Заезд</th><th>Выезд</th><th>Статус</th><th>Сумма</th><th>Источник</th><th /></tr>
            </thead>
            <tbody>
              {items.map((booking: any) => (
                <tr key={booking.booking_id}>
                  <td><input type="checkbox" checked={selected.includes(booking.booking_id)} onChange={(event) => setSelected((current) => event.target.checked ? [...current, booking.booking_id] : current.filter((id) => id !== booking.booking_id))} className="h-4 w-4 accent-terracotta" /></td>
                  <td className="font-semibold">#{booking.booking_id}</td>
                  <td><p className="font-medium">{booking.guest_name}</p><p className="text-xs text-muted"><SensitiveValue value={booking.document_number} /></p></td>
                  <td>{booking.room_number}<p className="text-xs text-muted">{booking.room_type}</p></td>
                  <td>{formatDate(booking.checkin_date)}</td>
                  <td>{formatDate(booking.checkout_date)}</td>
                  <td><StatusPill status={booking.status} /></td>
                  <td className="font-semibold">{formatMoney(booking.balance)}</td>
                  <td>{booking.source}</td>
                  <td className="text-right"><Button variant="ghost" size="sm" onClick={() => navigate(`/app/bookings/${booking.booking_id}`)}>Открыть</Button></td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pagination page={page} pageSize={pageSize} total={total} onPageChange={setPage} />
        </div>
      )}
      <NewBookingModal open={newOpen} onClose={() => { setNewOpen(false); searchParams.delete("new"); setSearchParams(searchParams); }} />
    </div>
  );
}

export function BookingDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [checkInOpen, setCheckInOpen] = useState(false);
  const [checkOutOpen, setCheckOutOpen] = useState(false);
  const [cancelOpen, setCancelOpen] = useState(false);
  const [moveOpen, setMoveOpen] = useState(false);
  const [holdOpen, setHoldOpen] = useState(false);
  const [holdForm, setHoldForm] = useState({ arrival_time: "14:00", hold_minutes: 60 });
  const [checkInForm, setCheckInForm] = useState({ document_number: "", deposit_amount: 0, payment_method: "CARD" });
  const [checkOutForm, setCheckOutForm] = useState({ payment_amount: 0, payment_method: "CARD" });
  const [reasonId, setReasonId] = useState<number | "">("");
  const [moveForm, setMoveForm] = useState({ room_id: "", checkin_date: "", checkout_date: "" });

  const query = useQuery({
    queryKey: ["manager-booking", id],
    queryFn: () => api.get(`/manager/bookings/${id}`).then((response) => response.data),
    enabled: Boolean(id),
  });
  const roomsQuery = useQuery({ queryKey: ["manager-rooms"], queryFn: () => api.get("/manager/rooms").then((response) => response.data) });
  const reasonsQuery = useQuery({ queryKey: ["manager-cancellation-reasons"], queryFn: () => api.get("/manager/cancellation-reasons").then((response) => response.data) });

  useEffect(() => {
    if (query.data?.booking) {
      setCheckInForm((current) => ({ ...current, document_number: query.data.booking.document_number ?? "" }));
      setMoveForm({ room_id: String(query.data.booking.room_id), checkin_date: query.data.booking.checkin_date, checkout_date: query.data.booking.checkout_date });
      setHoldForm({
        arrival_time: String(query.data.booking.arrival_time ?? "14:00").slice(0, 5),
        hold_minutes: Number(query.data.booking.hold_minutes ?? 60),
      });
    }
  }, [query.data]);

  const actionMutation = useMutation({
    mutationFn: async ({ action, payload }: { action: string; payload?: any }) => {
      if (action === "confirm") return api.post(`/manager/bookings/${id}/confirm`);
      if (action === "check-in") return api.post(`/manager/bookings/${id}/check-in`, payload);
      if (action === "check-out") return api.post(`/manager/bookings/${id}/check-out`, payload);
      if (action === "cancel") return api.post(`/manager/bookings/${id}/cancel`, null, { params: { reason_id: payload?.reason_id || undefined } });
      if (action === "move") return api.post(`/manager/bookings/${id}/move`, payload);
      return Promise.resolve();
    },
    onSuccess: () => {
      toast("Операция выполнена", "success");
      setCheckInOpen(false);
      setCheckOutOpen(false);
      setCancelOpen(false);
      setMoveOpen(false);
      setHoldOpen(false);
      queryClient.invalidateQueries({ queryKey: ["manager-booking", id] });
      queryClient.invalidateQueries({ queryKey: ["manager-bookings"] });
      queryClient.invalidateQueries({ queryKey: ["manager-dashboard"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  if (query.isLoading) return <Spinner />;
  if (query.isError) return <ErrorState message={getErrorMessage(query.error)} />;
  const { booking, checkin, checkout, services, folio } = query.data;
  const canCheckIn = booking.status === "CONFIRMED";
  const canCheckOut = booking.status === "CHECKED_IN";
  const canCancel = ["NEW", "CONFIRMED"].includes(booking.status);

  return (
    <div>
      <PageHeader
        title={`Бронирование #${booking.booking_id}`}
        subtitle={`${booking.guest_name} · ${booking.room_type}, номер ${booking.room_number}`}
        actions={
          <>
            <Button variant="secondary" onClick={() => navigate("/app/bookings")}>Назад</Button>
            {booking.status === "NEW" && <Button onClick={() => actionMutation.mutate({ action: "confirm" })}><Check size={15} /> Подтвердить</Button>}
            {canCheckIn && <Button onClick={() => setCheckInOpen(true)}><LogIn size={15} /> Заселить</Button>}
            {canCheckOut && <Button onClick={() => setCheckOutOpen(true)}><LogOut size={15} /> Выселить</Button>}
            {canCancel && <Button variant="danger" onClick={() => setCancelOpen(true)}><X size={15} /> Отменить</Button>}
          </>
        }
      />
      <div className="grid gap-5 xl:grid-cols-[1.4fr_1fr]">
        <div className="space-y-5">
          <Card>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="label">Статус брони</p>
                <div className="mt-2"><StatusPill status={booking.status} /></div>
              </div>
              <div className="text-right">
                <p className="label">Баланс</p>
                <p className="font-display text-3xl font-semibold">{formatMoney(folio?.balance ?? 0)}</p>
              </div>
            </div>
            <div className="mt-5 grid gap-4 sm:grid-cols-2">
              <div className="rounded-xl bg-surface2 p-4"><p className="label">Гость</p><p className="mt-2 font-semibold">{booking.guest_name}</p><p className="text-sm text-muted"><SensitiveValue value={booking.document_number} /></p><p className="text-sm text-muted"><SensitiveValue value={booking.guest_phone} /></p><p className="text-sm text-muted">{booking.guest_email}</p></div>
              <div className="rounded-xl bg-surface2 p-4"><p className="label">Проживание</p><p className="mt-2 text-sm text-muted">Заезд: {formatDate(booking.checkin_date)}</p><p className="text-sm text-muted">Выезд: {formatDate(booking.checkout_date)}</p><p className="text-sm text-muted">Время заезда: {String(booking.arrival_time ?? "—").slice(0, 5)}</p><p className="text-sm text-muted">Держать до: {booking.hold_until ? formatDateTime(booking.hold_until) : "—"}</p><p className="text-sm text-muted">Тариф: {booking.rate_name}</p><p className="text-sm text-muted">Гостей: {booking.adults + booking.children}</p></div>
            </div>
          </Card>
          <Card>
            <h2 className="font-display text-2xl font-semibold">Услуги</h2>
            {services.length ? services.map((service: any) => (
              <div key={service.order_id} className="mt-2 flex items-center justify-between rounded-xl border border-line px-4 py-3 text-sm">
                <div><p>{service.name} × {service.quantity}</p><p className="text-xs text-muted">{formatDateTime(service.ordered_at)}</p></div>
                <span className="font-semibold">{formatMoney(service.total)}</span>
              </div>
            )) : <p className="mt-3 text-sm text-muted">Услуги не заказаны.</p>}
          </Card>
          <Card>
            <h2 className="font-display text-2xl font-semibold">Timeline</h2>
            <div className="mt-4 space-y-3 text-sm">
              <div className="flex items-center gap-3"><span className="h-2.5 w-2.5 rounded-full bg-success" /><span>Создана · {formatDateTime(booking.created_at)}</span></div>
              {checkin && <div className="flex items-center gap-3"><span className="h-2.5 w-2.5 rounded-full bg-success" /><span>Заселение · {formatDateTime(checkin.actual_checkin_at)}</span></div>}
              {checkout && <div className="flex items-center gap-3"><span className="h-2.5 w-2.5 rounded-full bg-success" /><span>Выселение · {formatDateTime(checkout.actual_checkout_at)}</span></div>}
              {!checkin && <div className="flex items-center gap-3 text-muted"><span className="h-2.5 w-2.5 rounded-full bg-line" /><span>Заселение ожидается</span></div>}
            </div>
          </Card>
        </div>
        <div className="space-y-5">
          <Card className="space-y-2">
            <Button variant="secondary" className="w-full" onClick={() => setMoveOpen(true)}><ArrowLeftRight size={15} /> Перенести</Button>
            <Button variant="secondary" className="w-full" onClick={() => setHoldOpen(true)}>Изменить удержание</Button>
            {folio && <Button variant="secondary" className="w-full" onClick={() => navigate(`/app/folios?folio=${folio.folio_id}`)}><ReceiptText size={15} /> Открыть folio</Button>}
            {canCheckIn && <Button className="w-full" onClick={() => setCheckInOpen(true)}><LogIn size={15} /> Заселить</Button>}
            {canCheckOut && <Button className="w-full" onClick={() => setCheckOutOpen(true)}><LogOut size={15} /> Выселить</Button>}
          </Card>
          {folio && (
            <Card>
              <p className="label">Folio</p>
              <p className="mt-2 font-display text-3xl font-semibold">{formatMoney(folio.balance)}</p>
              <div className="mt-3 space-y-1 text-sm text-muted"><div className="flex justify-between"><span>Начислено</span><span>{formatMoney(folio.charged_total)}</span></div><div className="flex justify-between"><span>Оплачено</span><span>{formatMoney(folio.paid_total)}</span></div></div>
              <Button variant="secondary" className="mt-4 w-full" onClick={() => navigate(`/app/folios?folio=${folio.folio_id}`)}>Открыть счёт</Button>
            </Card>
          )}
        </div>
      </div>

      <Modal open={checkInOpen} title="Заселение гостя" subtitle="Проверьте документ и при необходимости примите депозит." onClose={() => setCheckInOpen(false)} footer={<><Button variant="secondary" onClick={() => setCheckInOpen(false)}>Отмена</Button><Button onClick={() => actionMutation.mutate({ action: "check-in", payload: checkInForm })} disabled={actionMutation.isPending}>Подтвердить заселение</Button></>}>
        <div className="space-y-3">
          <Input label="Документ гостя" value={checkInForm.document_number} onChange={(event) => setCheckInForm({ ...checkInForm, document_number: event.target.value })} />
          <Input label="Депозит" type="number" value={checkInForm.deposit_amount} onChange={(event) => setCheckInForm({ ...checkInForm, deposit_amount: Number(event.target.value) })} />
          <Select label="Способ оплаты" value={checkInForm.payment_method} onChange={(event) => setCheckInForm({ ...checkInForm, payment_method: event.target.value })}>
            <option value="CARD">Карта</option><option value="CASH">Наличные</option><option value="BANK_TRANSFER">Банковский перевод</option><option value="ONLINE">Онлайн</option>
          </Select>
        </div>
      </Modal>

      <Modal open={checkOutOpen} title="Выселение гостя" subtitle="Финальный платёж и закрытие folio." onClose={() => setCheckOutOpen(false)} footer={<><Button variant="secondary" onClick={() => setCheckOutOpen(false)}>Отмена</Button><Button onClick={() => actionMutation.mutate({ action: "check-out", payload: checkOutForm })} disabled={actionMutation.isPending}>Подтвердить выселение</Button></>}>
        <div className="space-y-3">
          <Input label="Сумма к оплате" type="number" value={checkOutForm.payment_amount} onChange={(event) => setCheckOutForm({ ...checkOutForm, payment_amount: Number(event.target.value) })} />
          <Select label="Способ оплаты" value={checkOutForm.payment_method} onChange={(event) => setCheckOutForm({ ...checkOutForm, payment_method: event.target.value })}>
            <option value="CARD">Карта</option><option value="CASH">Наличные</option><option value="BANK_TRANSFER">Банковский перевод</option><option value="ONLINE">Онлайн</option>
          </Select>
        </div>
      </Modal>

      <Modal open={cancelOpen} title="Отмена брони" onClose={() => setCancelOpen(false)} footer={<><Button variant="secondary" onClick={() => setCancelOpen(false)}>Не отменять</Button><Button variant="danger" onClick={() => actionMutation.mutate({ action: "cancel", payload: { reason_id: reasonId } })} disabled={actionMutation.isPending}>Подтвердить отмену</Button></>}>
        <Select label="Причина" value={reasonId} onChange={(event) => setReasonId(event.target.value ? Number(event.target.value) : "")}>
          <option value="">Без причины</option>
          {(reasonsQuery.data ?? []).map((reason: any) => <option key={reason.reason_id} value={reason.reason_id}>{reason.name}</option>)}
        </Select>
      </Modal>

      <Modal open={moveOpen} title="Перенос брони" onClose={() => setMoveOpen(false)} footer={<><Button variant="secondary" onClick={() => setMoveOpen(false)}>Отмена</Button><Button onClick={() => actionMutation.mutate({ action: "move", payload: { room_id: Number(moveForm.room_id), checkin_date: moveForm.checkin_date, checkout_date: moveForm.checkout_date } })} disabled={actionMutation.isPending}>Перенести</Button></>}>
        <div className="space-y-3">
          <Select label="Номер" value={moveForm.room_id} onChange={(event) => setMoveForm({ ...moveForm, room_id: event.target.value })}>
            {(roomsQuery.data ?? []).map((room: any) => <option key={room.room_id} value={room.room_id}>№{room.room_number} · {room.room_type}</option>)}
          </Select>
          <Input label="Заезд" type="date" value={moveForm.checkin_date} onChange={(event) => setMoveForm({ ...moveForm, checkin_date: event.target.value })} />
          <Input label="Выезд" type="date" value={moveForm.checkout_date} onChange={(event) => setMoveForm({ ...moveForm, checkout_date: event.target.value })} />
        </div>
      </Modal>
      <Modal open={holdOpen} title="Удержание брони" subtitle="Время заезда и срок, до которого номер держится за гостем" onClose={() => setHoldOpen(false)} footer={<><Button variant="secondary" onClick={() => setHoldOpen(false)}>Отмена</Button><Button onClick={() => actionMutation.mutate({ action: "hold", payload: holdForm })} disabled={actionMutation.isPending}>Сохранить</Button></>}>
        <div className="space-y-3">
          <Input label="Время заезда" type="time" value={holdForm.arrival_time} onChange={(event) => setHoldForm({ ...holdForm, arrival_time: event.target.value })} />
          <Input label="Держать, мин" type="number" min={5} max={1440} value={holdForm.hold_minutes} onChange={(event) => setHoldForm({ ...holdForm, hold_minutes: Number(event.target.value) })} />
          <p className="text-xs text-muted">Если гость не заселится до указанного времени, бронь автоматически отменится.</p>
        </div>
      </Modal>
    </div>
  );
}

export function FolioPaymentsPage() {
  const [searchParams] = useSearchParams();
  const initialFolio = searchParams.get("folio") ? Number(searchParams.get("folio")) : null;
  const [folioId, setFolioId] = useState<number | null>(initialFolio);
  const [status, setStatus] = useState("all");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [paymentOpen, setPaymentOpen] = useState(false);
  const [refundOpen, setRefundOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [paymentForm, setPaymentForm] = useState({ amount: 0, method: "CARD", payment_type: "PAYMENT" });
  const [refundForm, setRefundForm] = useState({ payment_id: "", amount: 0, reason: "" });
  const [importFile, setImportFile] = useState<File | null>(null);
  const [importPreview, setImportPreview] = useState<any>(null);
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const listQuery = useQuery({
    queryKey: ["manager-folios", status, search, page],
    queryFn: () => api.get("/manager/folios", { params: { status: status === "all" ? undefined : status, search: search || undefined, page, page_size: 25 } }).then((response) => response.data),
  });
  const detailQuery = useQuery({
    queryKey: ["manager-folio", folioId],
    queryFn: () => api.get(`/manager/folios/${folioId}`).then((response) => response.data),
    enabled: Boolean(folioId),
  });

  const actionMutation = useMutation({
    mutationFn: async ({ action, payload }: { action: string; payload?: any }) => {
      if (action === "payment") return api.post(`/manager/folios/${folioId}/payments`, payload);
      if (action === "refund") return api.post(`/manager/payments/${payload.payment_id}/refunds`, payload);
      if (action === "close") return api.post(`/manager/folios/${folioId}/close`);
      return Promise.resolve();
    },
    onSuccess: () => {
      toast("Операция выполнена", "success");
      setPaymentOpen(false);
      setRefundOpen(false);
      queryClient.invalidateQueries({ queryKey: ["manager-folio", folioId] });
      queryClient.invalidateQueries({ queryKey: ["manager-folios"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  const importPreviewMutation = useMutation({
    mutationFn: (file: File) => {
      const data = new FormData();
      data.append("file", file);
      return api.post("/imports/bank-statement/preview", data, { headers: { "Content-Type": "multipart/form-data" } }).then((response) => response.data);
    },
    onSuccess: (data) => { setImportPreview(data); toast(`Проверено строк: ${data.total}, ошибок: ${data.errors}`, data.errors ? "info" : "success"); },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const importCommitMutation = useMutation({
    mutationFn: () => api.post("/imports/bank-statement/commit", { filename: importFile?.name, rows: importPreview.rows }).then((response) => response.data),
    onSuccess: () => {
      toast("Выписка загружена", "success");
      setImportOpen(false);
      setImportPreview(null);
      setImportFile(null);
      queryClient.invalidateQueries({ queryKey: ["manager-folios"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  const items = listQuery.data?.items ?? [];
  const total = listQuery.data?.total ?? 0;

  return (
    <div>
      <PageHeader
        title="Folio и платежи"
        subtitle="Начисления, оплаты, возвраты и импорт банковской выписки."
        actions={<Button onClick={() => setImportOpen(true)}><Upload size={15} /> Импорт выписки CSV</Button>}
      />
      <Card className="mb-4 flex flex-wrap items-end gap-2">
        <Input label="Поиск" value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} placeholder="Гость, номер, folio" className="min-w-[220px]" />
        <Select label="Статус" value={status} onChange={(event) => { setStatus(event.target.value); setPage(1); }}>
          <option value="all">Все</option><option value="OPEN">Открытые</option><option value="CLOSED">Закрытые</option>
        </Select>
        <Button variant="secondary" onClick={() => setPage(1)}><Filter size={14} /> Применить</Button>
      </Card>
      {listQuery.isLoading && <Spinner />}
      {listQuery.isError && <ErrorState message={getErrorMessage(listQuery.error)} />}
      {!listQuery.isLoading && !listQuery.isError && (
        <div className="table-wrap">
          <table className="table-base">
            <thead><tr><th>Folio</th><th>Бронь</th><th>Гость</th><th>Номер</th><th>Начислено</th><th>Оплачено</th><th>Баланс</th><th>Статус</th><th /></tr></thead>
            <tbody>
              {items.map((folio: any) => (
                <tr key={folio.folio_id}>
                  <td className="font-semibold">#{folio.folio_id}</td>
                  <td>#{folio.booking_id}</td>
                  <td>{folio.guest_name}</td>
                  <td>{folio.room_number}</td>
                  <td>{formatMoney(folio.charged_total)}</td>
                  <td>{formatMoney(folio.paid_total)}</td>
                  <td className="font-semibold">{formatMoney(folio.balance)}</td>
                  <td><span className={cn("badge", folio.status === "OPEN" ? "bg-emerald-500/12 text-emerald-700" : "bg-surface2 text-muted")}>{folio.status === "OPEN" ? "Открыт" : "Закрыт"}</span></td>
                  <td className="text-right"><Button variant="ghost" size="sm" onClick={() => setFolioId(folio.folio_id)}>Открыть</Button></td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pagination page={page} pageSize={25} total={total} onPageChange={setPage} />
        </div>
      )}
      <Drawer
        open={Boolean(folioId)}
        title={`Folio #${folioId ?? ""}`}
        subtitle={detailQuery.data?.folio ? `${detailQuery.data.folio.guest_name} · №${detailQuery.data.folio.room_number}` : "Детали счёта"}
        onClose={() => setFolioId(null)}
        footer={
          <div className="flex flex-wrap justify-end gap-2">
            <Button variant="secondary" size="sm" onClick={() => folioId && downloadFile(api, `/manager/folios/${folioId}/pdf`, `folio-${folioId}.pdf`)}><Download size={14} /> PDF</Button>
            <Button variant="secondary" size="sm" onClick={() => setRefundOpen(true)}>Возврат</Button>
            <Button variant="secondary" size="sm" onClick={() => setPaymentOpen(true)}>Платёж</Button>
            <Button size="sm" onClick={() => actionMutation.mutate({ action: "close" })}>Закрыть счёт</Button>
          </div>
        }
      >
        {detailQuery.isLoading && <Spinner />}
        {detailQuery.isError && <ErrorState message={getErrorMessage(detailQuery.error)} />}
        {detailQuery.data && (
          <div className="space-y-5">
            <div className="rounded-2xl bg-surface2 p-4">
              <p className="label">Баланс</p>
              <p className="mt-1 font-display text-3xl font-semibold">{formatMoney(detailQuery.data.folio.balance)}</p>
              <div className="mt-2 flex justify-between text-xs text-muted"><span>Начислено</span><span>{formatMoney(detailQuery.data.folio.charged_total)}</span></div>
              <div className="flex justify-between text-xs text-muted"><span>Оплачено</span><span>{formatMoney(detailQuery.data.folio.paid_total)}</span></div>
            </div>
            <div>
              <h3 className="font-display text-xl font-semibold">Начисления</h3>
              <div className="mt-2 space-y-2">
                {detailQuery.data.charges.map((line: any) => (
                  <div key={line.line_id} className="flex justify-between gap-3 rounded-xl border border-line px-3 py-2 text-sm">
                    <div><p>{line.description}</p><p className="text-xs text-muted">{LINE_TYPE_LABELS[line.line_type] ?? line.line_type} · {formatDate(line.charge_date)}</p></div>
                    <span className="font-semibold">{formatMoney(line.amount)}</span>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <h3 className="font-display text-xl font-semibold">Платежи</h3>
              <div className="mt-2 space-y-2">
                {detailQuery.data.payments.map((payment: any) => (
                  <div key={payment.payment_id} className="flex items-center justify-between gap-3 rounded-xl border border-line px-3 py-2 text-sm">
                    <div><p>{PAYMENT_METHOD_LABELS[payment.method] ?? payment.method} · {payment.payment_type}</p><p className="text-xs text-muted">{formatDateTime(payment.paid_at)}</p></div>
                    <div className="text-right"><p className="font-semibold text-success">{formatMoney(payment.amount)}</p><button className="text-xs text-terracotta" onClick={() => { setRefundForm({ payment_id: String(payment.payment_id), amount: 0, reason: "" }); setRefundOpen(true); }}>Возврат</button></div>
                  </div>
                ))}
              </div>
            </div>
            {detailQuery.data.refunds?.length > 0 && (
              <div>
                <h3 className="font-display text-xl font-semibold">Возвраты</h3>
                {detailQuery.data.refunds.map((refund: any) => <div key={refund.refund_id} className="mt-2 flex justify-between rounded-xl border border-line px-3 py-2 text-sm"><span>{refund.reason}</span><span className="font-semibold text-danger">−{formatMoney(refund.amount)}</span></div>)}
              </div>
            )}
          </div>
        )}
      </Drawer>

      <Modal open={paymentOpen} title="Добавить платёж" onClose={() => setPaymentOpen(false)} footer={<><Button variant="secondary" onClick={() => setPaymentOpen(false)}>Отмена</Button><Button onClick={() => actionMutation.mutate({ action: "payment", payload: paymentForm })} disabled={actionMutation.isPending}>Сохранить</Button></>}>
        <div className="space-y-3">
          <Input label="Сумма" type="number" value={paymentForm.amount} onChange={(event) => setPaymentForm({ ...paymentForm, amount: Number(event.target.value) })} />
          <Select label="Способ" value={paymentForm.method} onChange={(event) => setPaymentForm({ ...paymentForm, method: event.target.value })}>
            <option value="CARD">Карта</option><option value="CASH">Наличные</option><option value="BANK_TRANSFER">Банковский перевод</option><option value="ONLINE">Онлайн</option>
          </Select>
          <Select label="Тип" value={paymentForm.payment_type} onChange={(event) => setPaymentForm({ ...paymentForm, payment_type: event.target.value })}>
            <option value="PAYMENT">Платёж</option><option value="DEPOSIT">Предоплата</option>
          </Select>
        </div>
      </Modal>

      <Modal open={refundOpen} title="Возврат платежа" onClose={() => setRefundOpen(false)} footer={<><Button variant="secondary" onClick={() => setRefundOpen(false)}>Отмена</Button><Button variant="danger" onClick={() => actionMutation.mutate({ action: "refund", payload: refundForm })} disabled={actionMutation.isPending}>Подтвердить возврат</Button></>}>
        <div className="space-y-3">
          <Input label="ID платежа" value={refundForm.payment_id} onChange={(event) => setRefundForm({ ...refundForm, payment_id: event.target.value })} />
          <Input label="Сумма" type="number" value={refundForm.amount} onChange={(event) => setRefundForm({ ...refundForm, amount: Number(event.target.value) })} />
          <Textarea label="Причина" value={refundForm.reason} onChange={(event) => setRefundForm({ ...refundForm, reason: event.target.value })} />
        </div>
      </Modal>

      <Modal open={importOpen} title="Импорт банковской выписки" subtitle="CSV: date, amount, method, booking_id или folio_id, external_ref" onClose={() => setImportOpen(false)} size="lg" footer={<><Button variant="secondary" onClick={() => setImportOpen(false)}>Отмена</Button><Button onClick={() => importCommitMutation.mutate()} disabled={!importPreview?.rows?.some((row: any) => row.status === "ok") || importCommitMutation.isPending}>Загрузить</Button></>}>
        <div className="space-y-4">
          <input type="file" accept=".csv,text/csv" onChange={(event) => { const file = event.target.files?.[0]; if (file) { setImportFile(file); importPreviewMutation.mutate(file); } }} className="input py-2" />
          {importPreview && (
            <div className="space-y-2">
              <div className="flex gap-3 text-sm"><span>Всего: {importPreview.total}</span><span className="text-success">OK: {importPreview.valid}</span><span className="text-danger">Ошибок: {importPreview.errors}</span></div>
              <div className="max-h-72 overflow-auto rounded-xl border border-line">
                <table className="table-base">
                  <thead><tr><th>Строка</th><th>Дата</th><th>Сумма</th><th>Folio</th><th>Статус</th><th>Ошибка</th></tr></thead>
                  <tbody>
                    {importPreview.rows.map((row: any) => (
                      <tr key={row.row}>
                        <td>{row.row}</td><td>{row.date}</td><td>{formatMoney(row.amount)}</td><td>{row.folio_id ?? "—"}</td>
                        <td>{row.status === "ok" ? <span className="text-success">OK</span> : <span className="text-danger">Ошибка</span>}</td>
                        <td className="text-xs text-muted">{row.error ?? ""}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
}

```

## `frontend/src/pages/OperationsPages.tsx`

```tsx
import {
  AlertTriangle,
  Check,
  ClipboardList,
  Package,
  Play,
  Plus,
  Sparkles,
  Wrench,
  X,
} from "lucide-react";
import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, getErrorMessage } from "../lib/api";
import { useToast } from "../components/ui";
import {
  Badge,
  Button,
  Card,
  Drawer,
  EmptyState,
  ErrorState,
  Input,
  Modal,
  PageHeader,
  Select,
  Spinner,
  StatusPill,
  Tabs,
  Textarea,
} from "../components/ui";
import {
  formatDateTime,
  formatNumber,
  MAINTENANCE_STATUS_LABELS,
  PRIORITY_LABELS,
  statusLabel,
  TASK_STATUS_LABELS,
  TASK_TYPE_LABELS,
} from "../lib/utils";

const TASK_COLUMNS = [
  { status: "ASSIGNED", label: "Назначено", tone: "bg-amber-500/10" },
  { status: "IN_PROGRESS", label: "В работе", tone: "bg-sky-500/10" },
  { status: "DONE", label: "Выполнено", tone: "bg-emerald-500/10" },
  { status: "CANCELLED", label: "Отменено", tone: "bg-surface2" },
];

export function HousekeepingBoardPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [floor, setFloor] = useState("all");
  const [assignee, setAssignee] = useState("all");
  const [newOpen, setNewOpen] = useState(false);
  const [newForm, setNewForm] = useState({ room_id: "", staff_id: "", task_type: "DAILY", priority: "NORMAL" });
  const [selectedTask, setSelectedTask] = useState<any>(null);
  const [writeOffOpen, setWriteOffOpen] = useState(false);
  const [writeOffForm, setWriteOffForm] = useState({ consumable_id: "", quantity: 1 });

  const tasksQuery = useQuery({
    queryKey: ["housekeeping-tasks", floor, assignee],
    queryFn: () => api.get("/housekeeping/tasks", { params: { floor: floor === "all" ? undefined : floor, assignee_id: assignee === "all" ? undefined : assignee } }).then((response) => response.data),
  });
  const staffQuery = useQuery({ queryKey: ["housekeeping-staff"], queryFn: () => api.get("/housekeeping/staff").then((response) => response.data) });
  const roomsQuery = useQuery({ queryKey: ["housekeeping-rooms"], queryFn: () => api.get("/housekeeping/rooms").then((response) => response.data) });
  const consumablesQuery = useQuery({ queryKey: ["housekeeping-consumables"], queryFn: () => api.get("/housekeeping/consumables").then((response) => response.data) });

  const actionMutation = useMutation({
    mutationFn: async ({ taskId, action }: { taskId: number; action: string }) => {
      if (action === "start") {
        await api.post(`/housekeeping/tasks/${taskId}/start`);
        return;
      }
      if (action === "complete") {
        await api.post(`/housekeeping/tasks/${taskId}/complete`);
        return;
      }
      if (action === "cancel") {
        await api.post(`/housekeeping/tasks/${taskId}/cancel`);
      }
    },
    onSuccess: () => {
      toast("Задание обновлено", "success");
      setSelectedTask(null);
      queryClient.invalidateQueries({ queryKey: ["housekeeping-tasks"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  const createMutation = useMutation({
    mutationFn: () => api.post("/housekeeping/tasks", {
      room_id: Number(newForm.room_id),
      staff_id: newForm.staff_id ? Number(newForm.staff_id) : null,
      task_type: newForm.task_type,
      priority: newForm.priority,
    }),
    onSuccess: () => {
      toast("Задание создано", "success");
      setNewOpen(false);
      setNewForm({ room_id: "", staff_id: "", task_type: "DAILY", priority: "NORMAL" });
      queryClient.invalidateQueries({ queryKey: ["housekeeping-tasks"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  const writeOffMutation = useMutation({
    mutationFn: () => api.post(`/housekeeping/tasks/${selectedTask?.task_id}/consumables`, {
      consumable_id: Number(writeOffForm.consumable_id),
      quantity: Number(writeOffForm.quantity),
    }),
    onSuccess: () => {
      toast("Расходник списан", "success");
      setWriteOffOpen(false);
      setWriteOffForm({ consumable_id: "", quantity: 1 });
      queryClient.invalidateQueries({ queryKey: ["housekeeping-tasks"] });
      queryClient.invalidateQueries({ queryKey: ["housekeeping-consumables"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  const tasks = tasksQuery.data ?? [];
  const grouped = useMemo(() => {
    const map: Record<string, any[]> = {};
    for (const column of TASK_COLUMNS) map[column.status] = [];
    for (const task of tasks) (map[task.status] ??= []).push(task);
    return map;
  }, [tasks]);

  return (
    <div>
      <PageHeader
        title="Доска хаускипинга"
        subtitle="Задания на уборку, статусы номеров и списание расходников."
        actions={<Button onClick={() => setNewOpen(true)}><Plus size={15} /> Новое задание</Button>}
      />
      <Card className="mb-4 flex flex-wrap items-end gap-2">
        <Select label="Этаж" value={floor} onChange={(event) => setFloor(event.target.value)}>
          <option value="all">Все этажи</option>
          <option value="1">1 этаж</option>
          <option value="2">2 этаж</option>
          <option value="3">3 этаж</option>
        </Select>
        <Select label="Исполнитель" value={assignee} onChange={(event) => setAssignee(event.target.value)}>
          <option value="all">Все</option>
          {(staffQuery.data ?? []).map((member: any) => <option key={member.user_id} value={member.user_id}>{member.full_name}</option>)}
        </Select>
        <Button variant="ghost" onClick={() => { setFloor("all"); setAssignee("all"); }}>Сбросить</Button>
      </Card>
      {tasksQuery.isLoading && <Spinner />}
      {tasksQuery.isError && <ErrorState message={getErrorMessage(tasksQuery.error)} />}
      {!tasksQuery.isLoading && !tasksQuery.isError && (
        <div className="grid gap-4 xl:grid-cols-4">
          {TASK_COLUMNS.map((column) => (
            <div key={column.status} className="rounded-2xl border border-line bg-surface2 p-3">
              <div className="mb-3 flex items-center justify-between">
                <p className="text-sm font-bold">{column.label}</p>
                <span className="badge bg-surface text-muted">{grouped[column.status]?.length ?? 0}</span>
              </div>
              <div className="space-y-2">
                {(grouped[column.status] ?? []).map((task: any) => (
                  <button key={task.task_id} className="w-full rounded-xl border border-line bg-surface p-3 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-soft" onClick={() => setSelectedTask(task)}>
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="font-semibold text-ink">№{task.room_number} · {TASK_TYPE_LABELS[task.task_type] ?? task.task_type}</p>
                        <p className="mt-1 text-xs text-muted">{task.assignee_name ?? "Не назначен"} · {formatDateTime(task.assigned_at)}</p>
                      </div>
                      <Badge tone={task.priority === "URGENT" || task.priority === "HIGH" ? "danger" : "neutral"}>{PRIORITY_LABELS[task.priority] ?? task.priority}</Badge>
                    </div>
                    <div className="mt-3 flex items-center justify-between">
                      <StatusPill status={task.status} />
                      <span className="text-xs text-muted">{statusLabel(task.room_status)}</span>
                    </div>
                  </button>
                ))}
                {!grouped[column.status]?.length && <p className="px-2 py-6 text-center text-xs text-muted">Пусто</p>}
              </div>
            </div>
          ))}
        </div>
      )}

      <Drawer
        open={Boolean(selectedTask)}
        title={selectedTask ? `Задание #${selectedTask.task_id}` : "Задание"}
        subtitle={selectedTask ? `Номер ${selectedTask.room_number} · ${selectedTask.room_type}` : ""}
        onClose={() => setSelectedTask(null)}
        footer={selectedTask && (
          <div className="flex flex-wrap justify-end gap-2">
            {selectedTask.status === "ASSIGNED" && <Button size="sm" onClick={() => actionMutation.mutate({ taskId: selectedTask.task_id, action: "start" })}><Play size={14} /> Начать</Button>}
            {["ASSIGNED", "IN_PROGRESS"].includes(selectedTask.status) && <Button size="sm" onClick={() => actionMutation.mutate({ taskId: selectedTask.task_id, action: "complete" })}><Check size={14} /> Завершить</Button>}
            {["ASSIGNED", "IN_PROGRESS"].includes(selectedTask.status) && <Button size="sm" variant="ghost" onClick={() => actionMutation.mutate({ taskId: selectedTask.task_id, action: "cancel" })}><X size={14} /> Отменить</Button>}
            <Button size="sm" variant="secondary" onClick={() => setWriteOffOpen(true)}><Package size={14} /> Списать расходники</Button>
          </div>
        )}
      >
        {selectedTask && (
          <div className="space-y-4">
            <div className="rounded-2xl bg-surface2 p-4 text-sm">
              <div className="flex justify-between"><span className="text-muted">Статус</span><StatusPill status={selectedTask.status} /></div>
              <div className="mt-2 flex justify-between"><span className="text-muted">Тип</span><span>{TASK_TYPE_LABELS[selectedTask.task_type] ?? selectedTask.task_type}</span></div>
              <div className="mt-2 flex justify-between"><span className="text-muted">Приоритет</span><span>{PRIORITY_LABELS[selectedTask.priority] ?? selectedTask.priority}</span></div>
              <div className="mt-2 flex justify-between"><span className="text-muted">Назначено</span><span>{formatDateTime(selectedTask.assigned_at)}</span></div>
              {selectedTask.completed_at && <div className="mt-2 flex justify-between"><span className="text-muted">Завершено</span><span>{formatDateTime(selectedTask.completed_at)}</span></div>}
            </div>
            <div>
              <p className="label mb-2">Чек-лист</p>
              <div className="space-y-2 text-sm text-muted">
                <label className="flex items-center gap-2"><input type="checkbox" className="h-4 w-4 accent-terracotta" /> Проверить чистоту номера</label>
                <label className="flex items-center gap-2"><input type="checkbox" className="h-4 w-4 accent-terracotta" /> Заменить бельё и полотенца</label>
                <label className="flex items-center gap-2"><input type="checkbox" className="h-4 w-4 accent-terracotta" /> Пополнить расходники</label>
                <label className="flex items-center gap-2"><input type="checkbox" className="h-4 w-4 accent-terracotta" /> Проверить технику</label>
              </div>
            </div>
          </div>
        )}
      </Drawer>

      <Modal open={newOpen} title="Новое задание" onClose={() => setNewOpen(false)} footer={<><Button variant="secondary" onClick={() => setNewOpen(false)}>Отмена</Button><Button onClick={() => createMutation.mutate()} disabled={createMutation.isPending || !newForm.room_id}>Создать</Button></>}>
        <div className="space-y-3">
          <Select label="Номер" value={newForm.room_id} onChange={(event) => setNewForm({ ...newForm, room_id: event.target.value })}>
            <option value="">Выберите номер</option>
            {(roomsQuery.data ?? []).map((room: any) => <option key={room.room_id} value={room.room_id}>№{room.room_number} · {room.room_type} · {room.status}</option>)}
          </Select>
          <Select label="Исполнитель" value={newForm.staff_id} onChange={(event) => setNewForm({ ...newForm, staff_id: event.target.value })}>
            <option value="">Не назначен</option>
            {(staffQuery.data ?? []).map((member: any) => <option key={member.user_id} value={member.user_id}>{member.full_name}</option>)}
          </Select>
          <Select label="Тип задания" value={newForm.task_type} onChange={(event) => setNewForm({ ...newForm, task_type: event.target.value })}>
            <option value="DAILY">Ежедневная уборка</option>
            <option value="POST_CHECKOUT">После выезда</option>
            <option value="ON_REQUEST">По запросу</option>
          </Select>
          <Select label="Приоритет" value={newForm.priority} onChange={(event) => setNewForm({ ...newForm, priority: event.target.value })}>
            <option value="LOW">Низкий</option><option value="NORMAL">Обычный</option><option value="HIGH">Высокий</option><option value="URGENT">Срочный</option>
          </Select>
        </div>
      </Modal>

      <Modal open={writeOffOpen} title="Списание расходников" subtitle={selectedTask ? `Задание #${selectedTask.task_id}` : ""} onClose={() => setWriteOffOpen(false)} footer={<><Button variant="secondary" onClick={() => setWriteOffOpen(false)}>Отмена</Button><Button onClick={() => writeOffMutation.mutate()} disabled={writeOffMutation.isPending || !writeOffForm.consumable_id}>Подтвердить списание</Button></>}>
        <div className="space-y-3">
          <Select label="Материал" value={writeOffForm.consumable_id} onChange={(event) => setWriteOffForm({ ...writeOffForm, consumable_id: event.target.value })}>
            <option value="">Выберите материал</option>
            {(consumablesQuery.data ?? []).map((item: any) => <option key={item.consumable_id} value={item.consumable_id}>{item.name} · остаток {formatNumber(item.stock_quantity)} {item.unit}</option>)}
          </Select>
          <Input label="Количество" type="number" min={0.1} step={0.1} value={writeOffForm.quantity} onChange={(event) => setWriteOffForm({ ...writeOffForm, quantity: Number(event.target.value) })} />
        </div>
      </Modal>
    </div>
  );
}

export function MaintenancePage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState("OPEN");
  const [newOpen, setNewOpen] = useState(false);
  const [form, setForm] = useState({ room_id: "", description: "", priority: "NORMAL", assigned_to: "" });
  const query = useQuery({ queryKey: ["maintenance", tab], queryFn: () => api.get("/housekeeping/maintenance", { params: { status: tab === "all" ? undefined : tab } }).then((response) => response.data) });
  const roomsQuery = useQuery({ queryKey: ["housekeeping-rooms"], queryFn: () => api.get("/housekeeping/rooms").then((response) => response.data) });
  const staffQuery = useQuery({ queryKey: ["housekeeping-staff"], queryFn: () => api.get("/housekeeping/staff").then((response) => response.data) });

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) => api.patch(`/housekeeping/maintenance/${id}/status`, { status }),
    onSuccess: () => { toast("Статус заявки обновлён", "success"); queryClient.invalidateQueries({ queryKey: ["maintenance"] }); },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const createMutation = useMutation({
    mutationFn: () => api.post("/housekeeping/maintenance", {
      room_id: Number(form.room_id),
      description: form.description,
      priority: form.priority,
      assigned_to: form.assigned_to ? Number(form.assigned_to) : null,
    }),
    onSuccess: () => {
      toast("Заявка создана", "success");
      setNewOpen(false);
      setForm({ room_id: "", description: "", priority: "NORMAL", assigned_to: "" });
      queryClient.invalidateQueries({ queryKey: ["maintenance"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  return (
    <div>
      <PageHeader title="Заявки на техобслуживание" subtitle="Неисправности номеров, приоритеты и назначение исполнителей." actions={<Button onClick={() => setNewOpen(true)}><Plus size={15} /> Новая заявка</Button>} />
      <Tabs className="mb-4" value={tab} onChange={setTab} items={[
        { value: "all", label: "Все" },
        { value: "OPEN", label: "Открытые" },
        { value: "IN_PROGRESS", label: "В работе" },
        { value: "DONE", label: "Выполненные" },
        { value: "CANCELLED", label: "Отменённые" },
      ]} />
      {query.isLoading && <Spinner />}
      {query.isError && <ErrorState message={getErrorMessage(query.error)} />}
      {!query.isLoading && !query.isError && (
        <div className="table-wrap">
          <table className="table-base">
            <thead><tr><th>Номер</th><th>Проблема</th><th>Приоритет</th><th>Статус</th><th>Исполнитель</th><th>Создана</th><th /></tr></thead>
            <tbody>
              {(query.data ?? []).map((request: any) => (
                <tr key={request.request_id}>
                  <td className="font-semibold">№{request.room_number}<p className="text-xs text-muted">{request.floor} этаж</p></td>
                  <td className="max-w-[320px]">{request.description}</td>
                  <td><Badge tone={request.priority === "URGENT" || request.priority === "HIGH" ? "danger" : "neutral"}>{PRIORITY_LABELS[request.priority] ?? request.priority}</Badge></td>
                  <td><StatusPill status={request.status} /></td>
                  <td>{request.assignee_name ?? "—"}</td>
                  <td>{formatDateTime(request.created_at)}</td>
                  <td className="text-right">
                    <div className="flex justify-end gap-1">
                      {request.status === "OPEN" && <Button variant="ghost" size="sm" onClick={() => statusMutation.mutate({ id: request.request_id, status: "IN_PROGRESS" })}><Play size={14} /> В работу</Button>}
                      {["OPEN", "IN_PROGRESS"].includes(request.status) && <Button variant="ghost" size="sm" onClick={() => statusMutation.mutate({ id: request.request_id, status: "DONE" })}><Check size={14} /> Завершить</Button>}
                      {["OPEN", "IN_PROGRESS"].includes(request.status) && <Button variant="ghost" size="sm" onClick={() => statusMutation.mutate({ id: request.request_id, status: "CANCELLED" })}><X size={14} /> Отменить</Button>}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!(query.data ?? []).length && <EmptyState title="Заявок нет" />}
        </div>
      )}
      <Modal open={newOpen} title="Новая заявка на ремонт" onClose={() => setNewOpen(false)} footer={<><Button variant="secondary" onClick={() => setNewOpen(false)}>Отмена</Button><Button onClick={() => createMutation.mutate()} disabled={createMutation.isPending || !form.room_id || !form.description}>Создать заявку</Button></>}>
        <div className="space-y-3">
          <Select label="Номер" value={form.room_id} onChange={(event) => setForm({ ...form, room_id: event.target.value })}>
            <option value="">Выберите номер</option>
            {(roomsQuery.data ?? []).map((room: any) => <option key={room.room_id} value={room.room_id}>№{room.room_number} · {room.room_type}</option>)}
          </Select>
          <Textarea label="Описание" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} placeholder="Что случилось?" />
          <Select label="Приоритет" value={form.priority} onChange={(event) => setForm({ ...form, priority: event.target.value })}>
            <option value="LOW">Низкий</option><option value="NORMAL">Обычный</option><option value="HIGH">Высокий</option><option value="URGENT">Срочный</option>
          </Select>
          <Select label="Исполнитель" value={form.assigned_to} onChange={(event) => setForm({ ...form, assigned_to: event.target.value })}>
            <option value="">Не назначен</option>
            {(staffQuery.data ?? []).map((member: any) => <option key={member.user_id} value={member.user_id}>{member.full_name}</option>)}
          </Select>
        </div>
      </Modal>
    </div>
  );
}

export function ConsumablesPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [writeOffOpen, setWriteOffOpen] = useState(false);
  const [form, setForm] = useState({ task_id: "", consumable_id: "", quantity: 1 });
  const consumablesQuery = useQuery({ queryKey: ["housekeeping-consumables"], queryFn: () => api.get("/housekeeping/consumables").then((response) => response.data) });
  const tasksQuery = useQuery({ queryKey: ["housekeeping-tasks"], queryFn: () => api.get("/housekeeping/tasks").then((response) => response.data) });
  const mutation = useMutation({
    mutationFn: () => api.post(`/housekeeping/tasks/${form.task_id}/consumables`, { consumable_id: Number(form.consumable_id), quantity: Number(form.quantity) }),
    onSuccess: () => {
      toast("Расходник списан", "success");
      setWriteOffOpen(false);
      setForm({ task_id: "", consumable_id: "", quantity: 1 });
      queryClient.invalidateQueries({ queryKey: ["housekeeping-consumables"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  return (
    <div>
      <PageHeader title="Расходные материалы" subtitle="Остатки, списания и дефицит по хозяйственным материалам." actions={<Button onClick={() => setWriteOffOpen(true)}><Package size={15} /> Списать</Button>} />
      {consumablesQuery.isLoading && <Spinner />}
      {consumablesQuery.isError && <ErrorState message={getErrorMessage(consumablesQuery.error)} />}
      {!consumablesQuery.isLoading && !consumablesQuery.isError && (
        <div className="table-wrap">
          <table className="table-base">
            <thead><tr><th>Материал</th><th>Ед.</th><th>Остаток</th><th>Минимум</th><th>Использовано</th><th>Дефицит</th><th /></tr></thead>
            <tbody>
              {(consumablesQuery.data ?? []).map((item: any) => (
                <tr key={item.consumable_id}>
                  <td className="font-medium">{item.name}</td>
                  <td>{item.unit}</td>
                  <td className="font-semibold">{formatNumber(item.stock_quantity)}</td>
                  <td>{formatNumber(item.min_stock)}</td>
                  <td>{formatNumber(item.used_total)}</td>
                  <td>{item.deficit ? <Badge tone="danger">Дефицит</Badge> : <Badge tone="success">В норме</Badge>}</td>
                  <td className="text-right"><Button variant="ghost" size="sm" onClick={() => { setForm({ ...form, consumable_id: String(item.consumable_id) }); setWriteOffOpen(true); }}>Списать</Button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <Modal open={writeOffOpen} title="Списание расходника" onClose={() => setWriteOffOpen(false)} footer={<><Button variant="secondary" onClick={() => setWriteOffOpen(false)}>Отмена</Button><Button onClick={() => mutation.mutate()} disabled={mutation.isPending || !form.task_id || !form.consumable_id}>Подтвердить списание</Button></>}>
        <div className="space-y-3">
          <Select label="Задание" value={form.task_id} onChange={(event) => setForm({ ...form, task_id: event.target.value })}>
            <option value="">Выберите задание</option>
            {(tasksQuery.data ?? []).filter((task: any) => ["ASSIGNED", "IN_PROGRESS"].includes(task.status)).map((task: any) => <option key={task.task_id} value={task.task_id}>#{task.task_id} · №{task.room_number} · {TASK_TYPE_LABELS[task.task_type] ?? task.task_type}</option>)}
          </Select>
          <Select label="Материал" value={form.consumable_id} onChange={(event) => setForm({ ...form, consumable_id: event.target.value })}>
            <option value="">Выберите материал</option>
            {(consumablesQuery.data ?? []).map((item: any) => <option key={item.consumable_id} value={item.consumable_id}>{item.name} · остаток {formatNumber(item.stock_quantity)}</option>)}
          </Select>
          <Input label="Количество" type="number" min={0.1} step={0.1} value={form.quantity} onChange={(event) => setForm({ ...form, quantity: Number(event.target.value) })} />
        </div>
      </Modal>
    </div>
  );
}

```

## `frontend/src/pages/PublicPages.tsx`

```tsx
import {
  ArrowRight,
  BadgeCheck,
  CalendarDays,
  CheckCircle2,
  ChevronRight,
  Coffee,
  CreditCard,
  Lock,
  Mail,
  MapPin,
  Phone,
  Search,
  ShieldCheck,
  Snowflake,
  Sparkles,
  Star,
  Sun,
  Users,
  Wifi,
} from "lucide-react";
import { useMemo, useState } from "react";
import { Link, Navigate, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api, getErrorMessage } from "../lib/api";
import { useAuth } from "../lib/auth";
import { useI18n } from "../lib/i18n";
import { addDaysISO, formatDate, formatMoney, nightsBetween, todayISO } from "../lib/utils";
import { Button, Card, ErrorState, Input, Select, Spinner, StatusPill, useToast } from "../components/ui";
import { homeForRole } from "../components/Layout";

const FALLBACK_ROOM_TYPES = [
  { room_type_id: 1, name: "Стандарт", capacity: 2, min_price: 4800, description: "Уютный номер с одной кроватью или двумя раздельными." },
  { room_type_id: 2, name: "Комфорт", capacity: 2, min_price: 6400, description: "Номер повышенной комфортности с видом на город." },
  { room_type_id: 3, name: "Люкс", capacity: 4, min_price: 9900, description: "Просторный номер с гостиной зоной." },
];

function RoomArt({ index = 0, className = "" }: { index?: number; className?: string }) {
  const palettes = [
    "from-[#d9c3a5] via-[#b88a67] to-[#5d4437]",
    "from-[#c8d5c8] via-[#8faF9b] to-[#2f5147]",
    "from-[#e5c7ae] via-[#c96f4a] to-[#5b3024]",
  ];
  return (
    <div className={`relative overflow-hidden rounded-2xl bg-gradient-to-br ${palettes[index % palettes.length]} ${className}`}>
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_20%,rgba(255,255,255,0.35),transparent_16rem)]" />
      <div className="absolute bottom-4 left-4 flex items-center gap-2 rounded-full bg-black/25 px-3 py-1 text-[11px] font-semibold text-white backdrop-blur">
        <Sparkles size={13} /> SunStay collection
      </div>
    </div>
  );
}

export function LandingPage() {
  const navigate = useNavigate();
  const { data } = useQuery({
    queryKey: ["public-room-types"],
    queryFn: () => api.get("/public/room-types").then((response) => response.data),
  });
  const roomTypes = data?.length ? data : FALLBACK_ROOM_TYPES;
  const [checkin, setCheckin] = useState(addDaysISO(todayISO(), 7));
  const [checkout, setCheckout] = useState(addDaysISO(todayISO(), 10));
  const [guests, setGuests] = useState(2);

  function submitSearch() {
    navigate(`/search?checkin=${checkin}&checkout=${checkout}&guests=${guests}`);
  }

  return (
    <div>
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_10%,rgba(201,111,74,0.22),transparent_26rem),radial-gradient(circle_at_15%_30%,rgba(18,59,54,0.16),transparent_30rem)]" />
        <div className="relative mx-auto grid max-w-[1240px] gap-10 px-4 pb-16 pt-14 md:grid-cols-[1.05fr_0.95fr] md:px-6 md:pb-24 md:pt-20">
          <div className="flex flex-col justify-center">
            <span className="badge w-fit bg-terracotta/12 text-terracotta">
              <Star size={13} /> Бутик-отель в центре Петербурга
            </span>
            <h1 className="mt-5 max-w-2xl font-display text-5xl font-semibold leading-[1.05] tracking-tight text-ink md:text-6xl">
              Отель, в который хочется вернуться
            </h1>
            <p className="mt-5 max-w-xl text-base leading-7 text-muted">
              48 номеров, тихий внутренний двор и внимательный сервис. Бронируйте напрямую — без скрытых комиссий и лишних звонков.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Button onClick={submitSearch}>
                <Search size={17} /> Найти номер
              </Button>
              <Link to="/login" className="btn-secondary">
                Войти в кабинет
              </Link>
            </div>
            <div className="mt-8 flex flex-wrap gap-6 text-sm text-muted">
              <span className="flex items-center gap-2"><ShieldCheck size={16} className="text-success" /> Безопасная оплата</span>
              <span className="flex items-center gap-2"><BadgeCheck size={16} className="text-success" /> Подтверждение сразу</span>
              <span className="flex items-center gap-2"><MapPin size={16} className="text-terracotta" /> Набережная Мойки, 12</span>
            </div>
          </div>
          <div className="relative">
            <RoomArt index={0} className="h-[360px] shadow-float md:h-[440px]" />
            <Card className="absolute -bottom-8 left-4 right-4 md:left-8 md:right-8">
              <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                <label className="col-span-1 flex flex-col gap-1.5">
                  <span className="label">Заезд</span>
                  <input type="date" value={checkin} onChange={(event) => setCheckin(event.target.value)} className="input" />
                </label>
                <label className="col-span-1 flex flex-col gap-1.5">
                  <span className="label">Выезд</span>
                  <input type="date" value={checkout} onChange={(event) => setCheckout(event.target.value)} className="input" />
                </label>
                <label className="col-span-1 flex flex-col gap-1.5">
                  <span className="label">Гости</span>
                  <select value={guests} onChange={(event) => setGuests(Number(event.target.value))} className="input">
                    {[1, 2, 3, 4].map((value) => <option key={value} value={value}>{value} гостя</option>)}
                  </select>
                </label>
                <div className="col-span-1 flex items-end">
                  <Button className="w-full" onClick={submitSearch}>Найти</Button>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-[1240px] px-4 pt-20 md:px-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="label text-terracotta">Номерной фонд</p>
            <h2 className="mt-2 font-display text-3xl font-semibold text-ink">Камерное пространство для отдыха</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
              Три категории номеров с продуманным светом, натуральными материалами и тишиной.
            </p>
          </div>
          <Link to="/search" className="text-sm font-semibold text-terracotta hover:underline">Смотреть все номера →</Link>
        </div>
        <div className="mt-8 grid gap-5 md:grid-cols-3">
          {roomTypes.map((room: any, index: number) => (
            <Card key={room.room_type_id} className="overflow-hidden p-0">
              <RoomArt index={index} className="h-48 rounded-none" />
              <div className="p-5">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="font-display text-2xl font-semibold text-ink">{room.name}</h3>
                    <p className="mt-1 text-xs text-muted">до {room.capacity} гостей · {room.rooms_count ?? "—"} номеров</p>
                  </div>
                  <div className="text-right">
                    <p className="text-[11px] uppercase tracking-wide text-muted">от</p>
                    <p className="font-display text-xl font-semibold text-ink">{formatMoney(room.min_price)}</p>
                  </div>
                </div>
                <p className="mt-3 min-h-12 text-sm leading-6 text-muted">{room.description}</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  {(room.amenities?.length ? room.amenities : ["Wi-Fi", "Кондиционер", "Сейф"]).slice(0, 4).map((amenity: string) => (
                    <span key={amenity} className="badge bg-surface2 text-muted">{amenity}</span>
                  ))}
                </div>
                <Button
                  variant="secondary"
                  className="mt-5 w-full"
                  onClick={() => navigate(`/search?checkin=${checkin}&checkout=${checkout}&guests=${guests}&room_type_id=${room.room_type_id}`)}
                >
                  Выбрать <ArrowRight size={15} />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-[1240px] px-4 py-20 md:px-6">
        <div className="rounded-3xl bg-forest px-6 py-10 text-white md:px-10 md:py-12">
          <div className="grid gap-8 md:grid-cols-[1.2fr_1fr] md:items-center">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-amber">Раннее бронирование</p>
              <h2 className="mt-3 font-display text-4xl font-semibold">−15% на проживание</h2>
              <p className="mt-3 max-w-xl text-sm leading-6 text-white/70">
                Забронируйте номер минимум за 30 дней и получите скидку по промокоду WELCOME15.
              </p>
            </div>
            <div className="rounded-2xl border border-white/15 bg-white/10 p-5">
              <p className="text-xs uppercase tracking-[0.12em] text-white/60">Промокод</p>
              <p className="mt-2 font-mono text-3xl font-bold tracking-[0.2em] text-amber">WELCOME15</p>
              <p className="mt-2 text-xs text-white/60">Применяется на этапе оформления бронирования.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-[1240px] px-4 pb-20 md:px-6">
        <div className="text-center">
          <p className="label text-terracotta">Почему SunStay</p>
          <h2 className="mt-2 font-display text-3xl font-semibold text-ink">Простое гостеприимство</h2>
        </div>
        <div className="mt-8 grid gap-4 md:grid-cols-4">
          {[
            { icon: <Wifi size={20} />, title: "Быстрый Wi-Fi", text: "Стабильный интернет во всех зонах отеля." },
            { icon: <Coffee size={20} />, title: "Завтрак", text: "Свежая выпечка и кофе каждое утро." },
            { icon: <Snowflake size={20} />, title: "Комфорт", text: "Кондиционеры и тихие номера." },
            { icon: <ShieldCheck size={20} />, title: "Безопасность", text: "Сейфы, видеонаблюдение и охрана." },
          ].map((item) => (
            <Card key={item.title}>
              <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-terracotta/12 text-terracotta">{item.icon}</span>
              <h3 className="mt-4 font-semibold text-ink">{item.title}</h3>
              <p className="mt-1 text-sm leading-6 text-muted">{item.text}</p>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}

export function SearchPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const checkin = params.get("checkin") || addDaysISO(todayISO(), 7);
  const checkout = params.get("checkout") || addDaysISO(todayISO(), 10);
  const guests = Number(params.get("guests") || 2);
  const roomTypeId = params.get("room_type_id") || "";
  const [localCheckin, setLocalCheckin] = useState(checkin);
  const [localCheckout, setLocalCheckout] = useState(checkout);
  const [localGuests, setLocalGuests] = useState(guests);
  const [localRoomType, setLocalRoomType] = useState(roomTypeId);
  const [maxPrice, setMaxPrice] = useState(15000);
  const [amenities, setAmenities] = useState<string[]>([]);

  const query = useQuery({
    queryKey: ["availability", checkin, checkout, guests, roomTypeId],
    queryFn: () =>
      api.get("/public/availability", { params: { checkin, checkout, guests, room_type_id: roomTypeId || undefined } }).then((response) => response.data),
  });

  const results = useMemo(() => {
    const items = query.data ?? [];
    return items.filter((room: any) => {
      if (Number(room.price_per_night) > maxPrice) return false;
      if (amenities.length && !amenities.every((amenity) => (room.amenities ?? []).includes(amenity))) return false;
      return true;
    });
  }, [query.data, maxPrice, amenities]);

  const nights = nightsBetween(checkin, checkout);

  function applyFilters() {
    const next = new URLSearchParams({ checkin: localCheckin, checkout: localCheckout, guests: String(localGuests) });
    if (localRoomType) next.set("room_type_id", localRoomType);
    navigate(`/search?${next.toString()}`);
  }

  function chooseRoom(roomType: any) {
    const room = roomType.rooms?.[0];
    if (!room) return;
    const next = new URLSearchParams({
      room_id: String(room.room_id),
      rate_id: String(room.rate_id),
      checkin,
      checkout,
      price: String(room.price_per_night),
      room_type: roomType.name,
      room_number: room.room_number,
      guests: String(guests),
    });
    navigate(`/checkout?${next.toString()}`);
  }

  return (
    <div className="mx-auto max-w-[1240px] px-4 py-10 md:px-6">
      <div className="mb-6">
        <p className="label text-terracotta">Поиск доступности</p>
        <h1 className="mt-2 font-display text-4xl font-semibold text-ink">Номера на ваши даты</h1>
        <p className="mt-2 text-sm text-muted">{formatDate(checkin)} — {formatDate(checkout)} · {nights} {nights === 1 ? "ночь" : "ночей"} · {guests} гостя</p>
      </div>
      <div className="grid gap-6 lg:grid-cols-[280px_1fr_280px]">
        <Card className="h-fit space-y-4">
          <div className="flex items-center gap-2 text-sm font-semibold text-ink"><Search size={16} /> Фильтры</div>
          <Input label="Заезд" type="date" value={localCheckin} onChange={(event) => setLocalCheckin(event.target.value)} />
          <Input label="Выезд" type="date" value={localCheckout} onChange={(event) => setLocalCheckout(event.target.value)} />
          <Select label="Гости" value={localGuests} onChange={(event) => setLocalGuests(Number(event.target.value))}>
            {[1, 2, 3, 4].map((value) => <option key={value} value={value}>{value} гостя</option>)}
          </Select>
          <Select label="Тип номера" value={localRoomType} onChange={(event) => setLocalRoomType(event.target.value)}>
            <option value="">Все типы</option>
            <option value="1">Стандарт</option>
            <option value="2">Комфорт</option>
            <option value="3">Люкс</option>
          </Select>
          <label className="flex flex-col gap-1.5">
            <span className="label">Цена до {formatMoney(maxPrice)}</span>
            <input type="range" min={3000} max={15000} step={500} value={maxPrice} onChange={(event) => setMaxPrice(Number(event.target.value))} className="accent-terracotta" />
          </label>
          <div>
            <p className="label mb-2">Удобства</p>
            <div className="space-y-2">
              {["Wi-Fi", "Кондиционер", "Мини-бар", "Сейф", "Балкон"].map((amenity) => (
                <label key={amenity} className="flex items-center gap-2 text-sm text-muted">
                  <input
                    type="checkbox"
                    checked={amenities.includes(amenity)}
                    onChange={(event) =>
                      setAmenities((current) =>
                        event.target.checked ? [...current, amenity] : current.filter((item) => item !== amenity),
                      )
                    }
                    className="h-4 w-4 accent-terracotta"
                  />
                  {amenity}
                </label>
              ))}
            </div>
          </div>
          <Button className="w-full" onClick={applyFilters}>Применить</Button>
          <Button variant="ghost" className="w-full" onClick={() => { setAmenities([]); setMaxPrice(15000); }}>Сбросить</Button>
        </Card>

        <div className="space-y-4">
          {query.isLoading && <Spinner />}
          {query.isError && <ErrorState message={getErrorMessage(query.error)} />}
          {!query.isLoading && !results.length && (
            <Card className="py-12 text-center text-sm text-muted">На выбранные даты нет доступных номеров. Попробуйте изменить фильтры.</Card>
          )}
          {results.map((roomType: any, index: number) => (
            <Card key={roomType.room_type_id} className="overflow-hidden p-0">
              <div className="grid md:grid-cols-[220px_1fr]">
                <RoomArt index={index} className="h-44 rounded-none md:h-full" />
                <div className="p-5">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h2 className="font-display text-2xl font-semibold text-ink">{roomType.name}</h2>
                      <p className="mt-1 text-xs text-muted">до {roomType.capacity} гостей · свободно {roomType.available_rooms}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-display text-2xl font-semibold text-ink">{formatMoney(roomType.price_per_night)}</p>
                      <p className="text-xs text-muted">за ночь</p>
                    </div>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-muted">{roomType.description}</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {(roomType.amenities ?? []).map((amenity: string) => (
                      <span key={amenity} className="badge bg-surface2 text-muted">{amenity}</span>
                    ))}
                  </div>
                  <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
                    <p className="text-sm text-muted">Итого за {nights} ночей: <span className="font-semibold text-ink">{formatMoney(Number(roomType.price_per_night) * nights)}</span></p>
                    <Button onClick={() => chooseRoom(roomType)}>Выбрать <ArrowRight size={15} /></Button>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>

        <Card className="h-fit space-y-4 lg:sticky lg:top-24">
          <p className="label">Ваш выбор</p>
          <div className="rounded-xl bg-surface2 p-4 text-sm">
            <p className="flex items-center gap-2 text-muted"><CalendarDays size={15} /> {formatDate(checkin)} — {formatDate(checkout)}</p>
            <p className="mt-2 flex items-center gap-2 text-muted"><Users size={15} /> {guests} гостя</p>
            <p className="mt-2 flex items-center gap-2 text-muted"><MoonIcon /> {nights} ночей</p>
          </div>
          <p className="text-xs leading-5 text-muted">Выберите номер слева, чтобы перейти к оформлению бронирования.</p>
          <Link to="/" className="btn-secondary w-full">Назад</Link>
        </Card>
      </div>
    </div>
  );
}

function MoonIcon() {
  return <span className="inline-block h-4 w-4 rounded-full border border-muted/40" />;
}

export function CheckoutPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { toast } = useToast();
  const roomId = Number(params.get("room_id") || 0);
  const rateId = Number(params.get("rate_id") || 0);
  const checkin = params.get("checkin") || addDaysISO(todayISO(), 7);
  const checkout = params.get("checkout") || addDaysISO(todayISO(), 10);
  const price = Number(params.get("price") || 0);
  const roomType = params.get("room_type") || "Номер";
  const roomNumber = params.get("room_number") || "";
  const nights = nightsBetween(checkin, checkout);
  const [form, setForm] = useState({
    full_name: user?.full_name ?? "",
    document_number: "",
    phone: user?.phone ?? "",
    email: user?.email ?? "",
    pdn_consent: true,
    payment_method: "ONLINE",
    arrival_time: "14:00",
    hold_minutes: 60,
  });
  const [promo, setPromo] = useState("");
  const [discount, setDiscount] = useState(0);
  const [promoError, setPromoError] = useState("");
  const total = price * nights * (1 - discount / 100);

  const promoMutation = useMutation({
    mutationFn: () => api.get(`/public/promo/${encodeURIComponent(promo)}`, { params: { checkin } }).then((response) => response.data),
    onSuccess: (data) => {
      setDiscount(Number(data.discount_percent));
      setPromoError("");
      toast(`Промокод применён: −${data.discount_percent}%`, "success");
    },
    onError: (error) => {
      setDiscount(0);
      setPromoError(getErrorMessage(error));
    },
  });

  const bookingMutation = useMutation({
    mutationFn: () => api.post("/public/bookings", {
      ...form,
      room_id: roomId,
      rate_id: rateId,
      checkin_date: checkin,
      checkout_date: checkout,
      promo_code: promo || undefined,
      adults: 1,
      children: 0,
      source: "SITE",
    }).then((response) => response.data),
    onSuccess: (booking) => {
      navigate("/confirmation", { state: { booking } });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  if (!roomId || !rateId) {
    return <div className="mx-auto max-w-3xl px-4 py-20"><Card><p className="text-muted">Сначала выберите номер.</p><Link to="/search" className="btn-primary mt-4">К поиску</Link></Card></div>;
  }

  return (
    <div className="mx-auto max-w-[1100px] px-4 py-10 md:px-6">
      <div className="mb-8 flex flex-wrap items-center gap-3 text-sm text-muted">
        <span className="badge bg-forest text-white">1</span> Данные гостя
        <ChevronRight size={15} />
        <span className="badge bg-surface2 text-muted">2</span> Оплата
        <ChevronRight size={15} />
        <span className="badge bg-surface2 text-muted">3</span> Подтверждение
      </div>
      <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
        <Card className="space-y-5">
          <div>
            <h1 className="font-display text-3xl font-semibold text-ink">Оформление бронирования</h1>
            <p className="mt-1 text-sm text-muted">Заполните данные гостя и подтвердите бронирование.</p>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <Input label="ФИО" value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} placeholder="Иванов Иван Иванович" />
            <Input label="Документ" value={form.document_number} onChange={(event) => setForm({ ...form, document_number: event.target.value })} placeholder="4510 123456" />
            <Input label="Телефон" value={form.phone ?? ""} onChange={(event) => setForm({ ...form, phone: event.target.value })} placeholder="+7 900 111-22-33" />
            <Input label="Email" value={form.email ?? ""} onChange={(event) => setForm({ ...form, email: event.target.value })} placeholder="guest@example.com" />
            <Input label="Время заезда" type="time" value={form.arrival_time} onChange={(event) => setForm({ ...form, arrival_time: event.target.value })} />
            <Input label="Держать бронь, мин" type="number" min={5} max={1440} value={form.hold_minutes} onChange={(event) => setForm({ ...form, hold_minutes: Number(event.target.value) })} />
          </div>
          <label className="flex items-start gap-2 text-sm text-muted">
            <input type="checkbox" checked={form.pdn_consent} onChange={(event) => setForm({ ...form, pdn_consent: event.target.checked })} className="mt-1 h-4 w-4 accent-terracotta" />
            Согласен на обработку персональных данных
          </label>
          <div>
            <p className="label mb-2">Способ оплаты</p>
            <div className="grid gap-3 sm:grid-cols-2">
              {[
                { value: "ONLINE", label: "Онлайн", icon: <CreditCard size={18} /> },
                { value: "CARD", label: "Карта", icon: <CreditCard size={18} /> },
              ].map((item) => (
                <label key={item.value} className={`flex cursor-pointer items-center gap-3 rounded-xl border p-3 text-sm ${form.payment_method === item.value ? "border-terracotta bg-terracotta/8" : "border-line bg-surface"}`}>
                  <input type="radio" name="payment" value={item.value} checked={form.payment_method === item.value} onChange={(event) => setForm({ ...form, payment_method: event.target.value })} className="accent-terracotta" />
                  {item.icon} {item.label}
                </label>
              ))}
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" onClick={() => navigate(-1)}>Назад</Button>
            <Button onClick={() => bookingMutation.mutate()} disabled={bookingMutation.isPending || !form.full_name || !form.document_number}>
              <Lock size={15} /> {bookingMutation.isPending ? "Оформляем…" : "Оплатить и забронировать"}
            </Button>
          </div>
          {bookingMutation.isError && <ErrorState message={getErrorMessage(bookingMutation.error)} />}
        </Card>
        <Card className="h-fit space-y-4">
          <RoomArt index={1} className="h-40" />
          <div>
            <h2 className="font-display text-2xl font-semibold text-ink">{roomType}</h2>
            <p className="text-sm text-muted">Номер {roomNumber} · {nights} ночей</p>
          </div>
          <div className="space-y-2 text-sm text-muted">
            <div className="flex justify-between"><span>{formatDate(checkin)} — {formatDate(checkout)}</span><span>{nights} ночей</span></div>
            <div className="flex justify-between"><span>{formatMoney(price)} × {nights}</span><span>{formatMoney(price * nights)}</span></div>
            {discount > 0 && <div className="flex justify-between text-success"><span>Скидка {discount}%</span><span>−{formatMoney(price * nights * discount / 100)}</span></div>}
            <div className="divider" />
            <div className="flex justify-between text-base font-semibold text-ink"><span>Итого</span><span>{formatMoney(total)}</span></div>
          </div>
          <div className="flex gap-2">
            <input value={promo} onChange={(event) => setPromo(event.target.value)} placeholder="Промокод" className="input" />
            <Button variant="secondary" onClick={() => promoMutation.mutate()} disabled={!promo || promoMutation.isPending}>Применить</Button>
          </div>
          {promoError && <p className="text-xs text-danger">{promoError}</p>}
          <p className="text-xs leading-5 text-muted">Оплата демонстрационная. Данные карты не запрашиваются.</p>
        </Card>
      </div>
    </div>
  );
}

export function ConfirmationPage() {
  const location = useLocation();
  const { user } = useAuth();
  const booking = (location.state as any)?.booking;
  return (
    <div className="mx-auto max-w-3xl px-4 py-16 md:px-6">
      <Card className="text-center">
        <span className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-success/15 text-success">
          <CheckCircle2 size={34} />
        </span>
        <h1 className="mt-5 font-display text-4xl font-semibold text-ink">Бронирование подтверждено</h1>
        <p className="mt-2 text-sm text-muted">Мы отправили детали на вашу почту. Номер брони: <span className="font-semibold text-ink">#{booking?.booking_id ?? "—"}</span></p>
        {booking && (
          <div className="mx-auto mt-6 grid max-w-lg gap-3 rounded-2xl bg-surface2 p-5 text-left text-sm">
            <div className="flex justify-between"><span className="text-muted">Отель</span><span className="font-semibold">SunStay</span></div>
            <div className="flex justify-between"><span className="text-muted">Даты</span><span>{formatDate(booking.checkin_date)} — {formatDate(booking.checkout_date)}</span></div>
            <div className="flex justify-between"><span className="text-muted">Номер</span><span>{booking.room_type}, №{booking.room_number}</span></div>
            <div className="flex justify-between"><span className="text-muted">Статус</span><StatusPill status={booking.status} /></div>
          </div>
        )}
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          {user?.role_code === "GUEST" && booking && <Link to={`/me/bookings/${booking.booking_id}`} className="btn-primary">В личный кабинет</Link>}
          {user && user.role_code !== "GUEST" && <Link to="/app/bookings" className="btn-primary">К бронированиям</Link>}
          <Link to="/" className="btn-secondary">На главную</Link>
        </div>
      </Card>
    </div>
  );
}

export function LoginPage() {
  const { user, login, register } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  const [tab, setTab] = useState<"login" | "register">("login");
  const [loginForm, setLoginForm] = useState({ email: "", password: "" });
  const [registerForm, setRegisterForm] = useState({
    full_name: "",
    document_number: "",
    phone: "",
    email: "",
    password: "",
    pdn_consent: true,
  });
  const demoQuery = useQuery({
    queryKey: ["demo-accounts"],
    queryFn: () => api.get("/auth/demo-accounts").then((response) => response.data),
  });

  const loginMutation = useMutation({
    mutationFn: () => login(loginForm.email, loginForm.password),
    onSuccess: (nextUser) => navigate(homeForRole(nextUser)),
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const demoLoginMutation = useMutation({
    mutationFn: (account: { email: string; password: string }) => login(account.email, account.password),
    onSuccess: (nextUser) => navigate(homeForRole(nextUser)),
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const registerMutation = useMutation({
    mutationFn: () => register(registerForm),
    onSuccess: (nextUser) => navigate(homeForRole(nextUser)),
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  if (user) return <Navigate to={homeForRole(user)} replace />;

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="relative hidden overflow-hidden bg-forest p-10 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_75%_20%,rgba(227,168,87,0.2),transparent_22rem)]" />
        <div className="relative">
          <Link to="/" className="flex items-center gap-2 text-xl font-semibold"><Sun size={22} className="text-amber" /> SunStay</Link>
          <p className="mt-10 max-w-md font-display text-5xl font-semibold leading-tight">Тишина, свет и забота о деталях.</p>
          <p className="mt-5 max-w-md text-sm leading-7 text-white/65">Войдите, чтобы управлять бронированиями, счетами и услугами в одном пространстве.</p>
        </div>
        <div className="relative flex items-center gap-3 text-sm text-white/60"><ShieldCheck size={18} className="text-amber" /> Безопасный вход и защита персональных данных</div>
      </div>
      <div className="flex items-center justify-center px-4 py-10">
        <div className="w-full max-w-md">
          <Link to="/" className="mb-8 flex items-center gap-2 text-xl font-semibold text-ink lg:hidden"><Sun size={22} className="text-terracotta" /> SunStay</Link>
          <h1 className="font-display text-4xl font-semibold text-ink">Добро пожаловать</h1>
          <p className="mt-2 text-sm text-muted">Вход в личный кабинет гостя или панель сотрудника.</p>
          <div className="mt-6 flex rounded-xl border border-line bg-surface2 p-1">
            <button className={`flex-1 rounded-lg px-3 py-2 text-sm font-semibold ${tab === "login" ? "bg-surface text-ink shadow-sm" : "text-muted"}`} onClick={() => setTab("login")}>Вход</button>
            <button className={`flex-1 rounded-lg px-3 py-2 text-sm font-semibold ${tab === "register" ? "bg-surface text-ink shadow-sm" : "text-muted"}`} onClick={() => setTab("register")}>Регистрация</button>
          </div>
          {tab === "login" ? (
            <form className="mt-5 space-y-4" onSubmit={(event) => { event.preventDefault(); loginMutation.mutate(); }}>
              <Input label="Email" type="email" value={loginForm.email} onChange={(event) => setLoginForm({ ...loginForm, email: event.target.value })} placeholder="you@example.com" />
              <Input label="Пароль" type="password" value={loginForm.password} onChange={(event) => setLoginForm({ ...loginForm, password: event.target.value })} placeholder="••••••••" />
              <Button type="submit" className="w-full" disabled={loginMutation.isPending}>{loginMutation.isPending ? "Входим…" : "Войти"}</Button>
              {loginMutation.isError && <ErrorState message={getErrorMessage(loginMutation.error)} />}
            </form>
          ) : (
            <form className="mt-5 space-y-3" onSubmit={(event) => { event.preventDefault(); registerMutation.mutate(); }}>
              <Input label="ФИО" value={registerForm.full_name} onChange={(event) => setRegisterForm({ ...registerForm, full_name: event.target.value })} placeholder="Иванов Иван Иванович" />
              <Input label="Документ" value={registerForm.document_number} onChange={(event) => setRegisterForm({ ...registerForm, document_number: event.target.value })} placeholder="4510 123456" />
              <Input label="Телефон" value={registerForm.phone} onChange={(event) => setRegisterForm({ ...registerForm, phone: event.target.value })} placeholder="+7 900 111-22-33" />
              <Input label="Email" type="email" value={registerForm.email} onChange={(event) => setRegisterForm({ ...registerForm, email: event.target.value })} placeholder="you@example.com" />
              <Input label="Пароль" type="password" value={registerForm.password} onChange={(event) => setRegisterForm({ ...registerForm, password: event.target.value })} placeholder="Минимум 8 символов" />
              <label className="flex items-start gap-2 text-sm text-muted">
                <input type="checkbox" checked={registerForm.pdn_consent} onChange={(event) => setRegisterForm({ ...registerForm, pdn_consent: event.target.checked })} className="mt-1 h-4 w-4 accent-terracotta" />
                Согласен на обработку персональных данных
              </label>
              <Button type="submit" className="w-full" disabled={registerMutation.isPending}>{registerMutation.isPending ? "Создаём…" : "Зарегистрироваться"}</Button>
              {registerMutation.isError && <ErrorState message={getErrorMessage(registerMutation.error)} />}
            </form>
          )}
          <div className="mt-6 rounded-2xl border border-line bg-surface2 p-4">
            <p className="text-xs font-bold uppercase tracking-[0.12em] text-muted">Демо-доступ</p>
            <div className="mt-3 grid gap-2">
              {(demoQuery.data ?? []).map((account: any) => (
                <button
                  key={account.email}
                  className="flex items-center justify-between rounded-xl border border-line bg-surface px-3 py-2 text-left text-xs hover:border-terracotta/50"
                  onClick={() => {
                    setLoginForm({ email: account.email, password: account.password });
                    demoLoginMutation.mutate({ email: account.email, password: account.password });
                  }}
                >
                  <span className="font-semibold text-ink">{account.role}</span>
                  <span className="text-muted">{account.email}</span>
                </button>
              ))}
              {demoQuery.isLoading && <p className="text-xs text-muted">Загрузка демо-аккаунтов…</p>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

```

## `frontend/src/pages/ReportsPage.tsx`

```tsx
import {
  BarChart3,
  Download,
  Image,
  RefreshCw,
  Save,
} from "lucide-react";
import { useMemo, useRef, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import html2canvas from "html2canvas";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Legend,
  Line,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { analyticsApi, downloadFile, getErrorMessage } from "../lib/api";
import { useAuth } from "../lib/auth";
import { useToast } from "../components/ui";
import { Button, Card, EmptyState, ErrorState, Input, KpiCard, PageHeader, Select, Spinner, Tabs } from "../components/ui";
import { addDaysISO, formatDate, formatMoney, formatNumber, monthLabel, todayISO } from "../lib/utils";

type ReportTab = "occupancy" | "adr" | "cancellations" | "room-status" | "consumables";

const TABS = [
  { value: "occupancy", label: "Загрузка" },
  { value: "adr", label: "ADR и RevPAR" },
  { value: "cancellations", label: "Отмены и no-show" },
  { value: "room-status", label: "Статусы номеров" },
  { value: "consumables", label: "Расходники" },
];

const ENDPOINTS: Record<ReportTab, string> = {
  occupancy: "/reports/occupancy",
  adr: "/reports/adr-revpar",
  cancellations: "/reports/cancellations",
  "room-status": "/reports/room-status",
  consumables: "/reports/consumables",
};

export function ReportsPage() {
  const { settings, updateSettings } = useAuth();
  const { toast } = useToast();
  const reportRef = useRef<HTMLDivElement>(null);
  const [tab, setTab] = useState<ReportTab>("occupancy");
  const [dateFrom, setDateFrom] = useState(addDaysISO(todayISO(), -30));
  const [dateTo, setDateTo] = useState(todayISO());
  const [roomTypeId, setRoomTypeId] = useState("");
  const [applied, setApplied] = useState({ dateFrom: addDaysISO(todayISO(), -30), dateTo: todayISO(), roomTypeId: "" });

  const query = useQuery({
    queryKey: ["analytics-report", tab, applied],
    queryFn: () =>
      analyticsApi.get(ENDPOINTS[tab], {
        params: {
          date_from: applied.dateFrom,
          date_to: applied.dateTo,
          room_type_id: applied.roomTypeId || undefined,
        },
      }).then((response) => response.data),
  });

  const saveMutation = useMutation({
    mutationFn: (name: string) => updateSettings({
      saved_filters: [...(settings.saved_filters ?? []), { name, date_from: applied.dateFrom, date_to: applied.dateTo, room_type_id: applied.roomTypeId, tab }],
    }),
    onSuccess: () => toast("Фильтр сохранён", "success"),
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  const summary = query.data?.summary ?? {};
  const series = query.data?.series ?? [];
  const months = query.data?.months ?? [];
  const reasons = query.data?.reasons ?? [];
  const roomStatus = query.data?.items ?? [];
  const consumables = query.data?.items ?? [];

  const pieColors = ["#123B36", "#C96F4A", "#E3A857", "#9DB5A4", "#3D6F8E", "#B8504E", "#6E746D"];

  const filteredRoomStatus = useMemo(() => roomStatus, [roomStatus]);

  async function exportPng() {
    if (!reportRef.current) return;
    const canvas = await html2canvas(reportRef.current, { backgroundColor: null, scale: 2 });
    const link = document.createElement("a");
    link.download = `sunstay-${tab}.png`;
    link.href = canvas.toDataURL("image/png");
    link.click();
  }

  return (
    <div>
      <PageHeader
        title="Отчёты и аналитика"
        subtitle="Загрузка, доходность, отмены, статусы номеров и расходные материалы."
        actions={
          <>
            <Button variant="secondary" onClick={() => downloadFile(analyticsApi, ENDPOINTS[tab], `${tab}.csv`, { date_from: applied.dateFrom, date_to: applied.dateTo, room_type_id: applied.roomTypeId || undefined, format: "csv" })}><Download size={15} /> Экспорт CSV</Button>
            <Button variant="secondary" onClick={exportPng}><Image size={15} /> Экспорт PNG</Button>
          </>
        }
      />
      <Card className="mb-4 flex flex-wrap items-end gap-2">
        <Input label="С даты" type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
        <Input label="По дату" type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
        <Select label="Тип номера" value={roomTypeId} onChange={(event) => setRoomTypeId(event.target.value)}>
          <option value="">Все типы</option>
          <option value="1">Стандарт</option>
          <option value="2">Комфорт</option>
          <option value="3">Люкс</option>
        </Select>
        <Button onClick={() => setApplied({ dateFrom, dateTo, roomTypeId })}><RefreshCw size={14} /> Применить</Button>
        <Button variant="ghost" onClick={() => { setDateFrom(addDaysISO(todayISO(), -30)); setDateTo(todayISO()); setRoomTypeId(""); setApplied({ dateFrom: addDaysISO(todayISO(), -30), dateTo: todayISO(), roomTypeId: "" }); }}>Сбросить</Button>
        <Button variant="ghost" onClick={() => { const name = window.prompt("Название фильтра", "Мой отчёт"); if (name) saveMutation.mutate(name); }}><Save size={14} /> Сохранить фильтр</Button>
        {(settings.saved_filters ?? []).length > 0 && (
          <Select label="Сохранённые фильтры" onChange={(event) => {
            const filter = (settings.saved_filters ?? [])[Number(event.target.value)];
            if (!filter) return;
            const next = { dateFrom: String(filter.date_from ?? dateFrom), dateTo: String(filter.date_to ?? dateTo), roomTypeId: String(filter.room_type_id ?? "") };
            setDateFrom(next.dateFrom); setDateTo(next.dateTo); setRoomTypeId(next.roomTypeId); setApplied(next);
            if (filter.tab) setTab(filter.tab as ReportTab);
          }}>
            <option value="">Выбрать</option>
            {(settings.saved_filters ?? []).map((filter, index) => <option key={index} value={index}>{String(filter.name ?? `Фильтр ${index + 1}`)}</option>)}
          </Select>
        )}
      </Card>
      <Tabs className="mb-4" value={tab} onChange={(value) => setTab(value as ReportTab)} items={TABS} />
      {query.isLoading && <Spinner />}
      {query.isError && <ErrorState message={getErrorMessage(query.error)} />}
      {!query.isLoading && !query.isError && (
        <div ref={reportRef} className="space-y-5">
          {tab === "occupancy" && (
            <>
              <div className="grid gap-4 md:grid-cols-3">
                <KpiCard label="Средняя загрузка" value={`${summary.average_occupancy ?? 0}%`} hint="За выбранный период" icon={<BarChart3 size={20} />} />
                <KpiCard label="Room nights sold" value={formatNumber(summary.room_nights_sold ?? 0)} hint="Проданных номеро-ночей" icon={<BarChart3 size={20} />} tone="terracotta" />
                <KpiCard label="Room nights available" value={formatNumber(summary.room_nights_available ?? 0)} hint="Доступных номеро-ночей" icon={<BarChart3 size={20} />} tone="sage" />
              </div>
              <Card>
                <h2 className="font-display text-2xl font-semibold">Динамика загрузки</h2>
                <div className="mt-4 h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={series}>
                      <defs><linearGradient id="reportOccupancy" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#C96F4A" stopOpacity={0.35} /><stop offset="95%" stopColor="#C96F4A" stopOpacity={0} /></linearGradient></defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                      <XAxis dataKey="report_date" tickFormatter={(value) => formatDate(value).slice(0, 5)} tick={{ fontSize: 11, fill: "var(--muted)" }} />
                      <YAxis unit="%" tick={{ fontSize: 11, fill: "var(--muted)" }} />
                      <Tooltip labelFormatter={(value) => formatDate(value)} formatter={(value) => [`${value}%`, "Загрузка"]} />
                      <Area type="monotone" dataKey="occupancy_pct" stroke="#C96F4A" strokeWidth={3} fill="url(#reportOccupancy)" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </Card>
            </>
          )}
          {tab === "adr" && (
            <>
              <div className="grid gap-4 md:grid-cols-3">
                <KpiCard label="ADR" value={formatMoney(summary.adr ?? 0)} hint="Средняя цена номера" icon={<BarChart3 size={20} />} />
                <KpiCard label="RevPAR" value={formatMoney(summary.revpar ?? 0)} hint="Доход на доступный номер" icon={<BarChart3 size={20} />} tone="terracotta" />
                <KpiCard label="Room revenue" value={formatMoney(summary.room_revenue ?? 0)} hint="Выручка от проживания" icon={<BarChart3 size={20} />} tone="amber" />
              </div>
              <Card>
                <h2 className="font-display text-2xl font-semibold">ADR и RevPAR</h2>
                <div className="mt-4 h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={series}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                      <XAxis dataKey="report_date" tickFormatter={(value) => formatDate(value).slice(0, 5)} tick={{ fontSize: 11, fill: "var(--muted)" }} />
                      <YAxis tick={{ fontSize: 11, fill: "var(--muted)" }} />
                      <Tooltip labelFormatter={(value) => formatDate(value)} formatter={(value, name) => [formatMoney(Number(value)), name === "adr" ? "ADR" : "RevPAR"]} />
                      <Legend />
                      <Bar dataKey="room_revenue" name="Выручка" fill="#E3A857" opacity={0.45} radius={[6, 6, 0, 0]} />
                      <Line type="monotone" dataKey="adr" name="ADR" stroke="#123B36" strokeWidth={3} dot={false} />
                      <Line type="monotone" dataKey="revpar" name="RevPAR" stroke="#C96F4A" strokeWidth={3} dot={false} />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              </Card>
            </>
          )}
          {tab === "cancellations" && (
            <div className="grid gap-5 xl:grid-cols-2">
              <Card>
                <h2 className="font-display text-2xl font-semibold">Отмены по месяцам</h2>
                <div className="mt-4 h-72">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={months}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                      <XAxis dataKey="month" tickFormatter={(value) => monthLabel(value)} tick={{ fontSize: 11, fill: "var(--muted)" }} />
                      <YAxis tick={{ fontSize: 11, fill: "var(--muted)" }} />
                      <Tooltip labelFormatter={(value) => monthLabel(value)} />
                      <Legend />
                      <Bar dataKey="cancelled" name="Отмены" fill="#C96F4A" radius={[6, 6, 0, 0]} />
                      <Bar dataKey="no_show" name="No-show" fill="#E3A857" radius={[6, 6, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Card>
              <Card>
                <h2 className="font-display text-2xl font-semibold">Причины отмен</h2>
                <div className="mt-2 h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={reasons} dataKey="bookings" nameKey="reason" innerRadius={50} outerRadius={85} paddingAngle={3}>
                        {reasons.map((entry: any, index: number) => <Cell key={entry.reason} fill={pieColors[index % pieColors.length]} />)}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="grid gap-2 text-xs text-muted">
                  {reasons.map((reason: any, index: number) => (
                    <span key={reason.reason} className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full" style={{ background: pieColors[index % pieColors.length] }} /> {reason.reason} · {reason.bookings}</span>
                  ))}
                </div>
              </Card>
            </div>
          )}
          {tab === "room-status" && (
            <Card>
              <h2 className="font-display text-2xl font-semibold">Статусы номеров сегодня</h2>
              <div className="mt-4 h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={filteredRoomStatus}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                    <XAxis dataKey="status" tick={{ fontSize: 11, fill: "var(--muted)" }} />
                    <YAxis tick={{ fontSize: 11, fill: "var(--muted)" }} />
                    <Tooltip />
                    <Bar dataKey="rooms" name="Номеров" fill="#123B36" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          )}
          {tab === "consumables" && (
            <Card>
              <h2 className="font-display text-2xl font-semibold">Расходные материалы</h2>
              <div className="mt-4 table-wrap">
                <table className="table-base">
                  <thead><tr><th>Материал</th><th>Ед.</th><th>Остаток</th><th>Минимум</th><th>Использовано</th><th>За 30 дней</th><th>Статус</th></tr></thead>
                  <tbody>
                    {consumables.map((item: any) => (
                      <tr key={item.consumable_id}>
                        <td className="font-medium">{item.name}</td>
                        <td>{item.unit}</td>
                        <td>{formatNumber(item.stock_quantity)}</td>
                        <td>{formatNumber(item.min_stock)}</td>
                        <td>{formatNumber(item.used_total)}</td>
                        <td>{formatNumber(item.used_30d)}</td>
                        <td>{item.deficit ? <span className="badge bg-danger/10 text-danger">Дефицит</span> : <span className="badge bg-success/10 text-success">В норме</span>}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}
          {!series.length && tab !== "cancellations" && tab !== "room-status" && tab !== "consumables" && <EmptyState title="Нет данных за период" />}
        </div>
      )}
    </div>
  );
}

```

## `frontend/scripts/capture_diagrams.mjs`

```javascript
﻿import { chromium } from "playwright";
import path from "node:path";
import { pathToFileURL } from "node:url";

const htmlPath = path.resolve("../docs/diagrams/diagrams.html");
const outDir = path.resolve("../docs/diagrams");

const browser = await chromium.launch({ channel: "msedge", headless: true });
const page = await browser.newPage({ viewport: { width: 1450, height: 1600 }, deviceScaleFactor: 1.5 });
await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "networkidle" });
await page.waitForSelector(".mermaid svg", { timeout: 30000 });
await page.waitForTimeout(1500);

for (const id of ["architecture", "usecase", "erd", "uimap", "testpyramid"]) {
  const locator = page.locator(`#${id}`);
  await locator.screenshot({ path: path.join(outDir, `${id}.png`) });
  console.log("captured", id);
}

await browser.close();


```

## `frontend/scripts/smoke.mjs`

```javascript
﻿import { chromium } from "playwright";
import path from "node:path";
import fs from "node:fs";

const base = process.env.BASE_URL ?? "http://localhost:5173";
const outDir = path.resolve("../docs/screenshots");
fs.mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch({ channel: "msedge", headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 1024 }, locale: "ru-RU" });
const page = await context.newPage();
const errors = [];
page.on("console", (message) => {
  if (message.type() === "error") errors.push(message.text());
});
page.on("pageerror", (error) => errors.push(String(error)));
page.on("response", (response) => {
  if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`);
});

async function shot(name) {
  await page.screenshot({ path: path.join(outDir, `${name}.png`), fullPage: false });
  console.log("screenshot", name);
}

await page.goto(base, { waitUntil: "networkidle" });
await shot("landing");

await page.goto(`${base}/login`, { waitUntil: "networkidle" });
await shot("login");
await page.getByRole("button", { name: /Менеджер/ }).first().click();
await page.waitForURL("**/app", { timeout: 15000 });
await page.waitForTimeout(1500);
await shot("manager-dashboard");
console.log("manager dashboard text:", (await page.locator("body").innerText()).slice(0, 500));

await page.goto(`${base}/app/bookings`, { waitUntil: "networkidle" });
await page.waitForTimeout(1000);
await shot("bookings-registry");

await page.goto(`${base}/app/room-grid`, { waitUntil: "networkidle" });
await page.waitForTimeout(1000);
await shot("room-grid");

await page.goto(`${base}/app/folios`, { waitUntil: "networkidle" });
await page.waitForTimeout(1000);
await shot("folio-payments");

await page.goto(`${base}/app/reports`, { waitUntil: "networkidle" });
await page.waitForTimeout(1800);
await shot("reports");

await page.goto(`${base}/app/housekeeping`, { waitUntil: "networkidle" });
await page.waitForTimeout(1000);
await shot("housekeeping");

await page.getByTitle("Переключить тему").first().click();
await page.waitForTimeout(500);
await shot("manager-dashboard-dark");

const adminContext = await browser.newContext({ viewport: { width: 1440, height: 1024 }, locale: "ru-RU" });
const adminPage = await adminContext.newPage();
adminPage.on("console", (message) => { if (message.type() === "error") errors.push(`[admin] ${message.text()}`); });
adminPage.on("pageerror", (error) => errors.push(`[admin] ${String(error)}`));
adminPage.on("response", (response) => { if (response.status() >= 400) errors.push(`[admin] ${response.status()} ${response.url()}`); });
await adminPage.goto(`${base}/login`, { waitUntil: "networkidle" });
await adminPage.getByRole("button", { name: /Администратор БД/ }).first().click();
await adminPage.waitForURL("**/app", { timeout: 15000 });
await adminPage.waitForTimeout(1200);
await adminPage.screenshot({ path: path.join(outDir, "admin-dashboard.png") });
await adminPage.goto(`${base}/app/admin/users`, { waitUntil: "networkidle" });
await adminPage.waitForTimeout(1200);
await adminPage.screenshot({ path: path.join(outDir, "admin-users.png") });
await adminPage.goto(`${base}/app/admin/directories`, { waitUntil: "networkidle" });
await adminPage.waitForTimeout(1200);
await adminPage.screenshot({ path: path.join(outDir, "admin-directories.png") });
await adminPage.goto(`${base}/app/admin/audit`, { waitUntil: "networkidle" });
await adminPage.waitForTimeout(1200);
await adminPage.screenshot({ path: path.join(outDir, "admin-audit.png") });
await adminPage.getByRole("button", { name: "Пользователи и вход" }).click();
await adminPage.waitForTimeout(1000);
await adminPage.screenshot({ path: path.join(outDir, "admin-audit-login.png") });
await adminPage.getByRole("button", { name: "Системные события" }).click();
await adminPage.waitForTimeout(1000);
await adminPage.screenshot({ path: path.join(outDir, "admin-audit-system.png") });
await adminPage.goto(`${base}/app/admin/backups`, { waitUntil: "networkidle" });
await adminPage.waitForTimeout(1200);
await adminPage.screenshot({ path: path.join(outDir, "admin-backups.png") });

const guestContext = await browser.newContext({ viewport: { width: 1440, height: 1024 }, locale: "ru-RU" });
const guestPage = await guestContext.newPage();
guestPage.on("console", (message) => { if (message.type() === "error") errors.push(`[guest] ${message.text()}`); });
guestPage.on("pageerror", (error) => errors.push(`[guest] ${String(error)}`));
guestPage.on("response", (response) => { if (response.status() >= 400) errors.push(`[guest] ${response.status()} ${response.url()}`); });
await guestPage.goto(`${base}/login`, { waitUntil: "networkidle" });
await guestPage.getByRole("button", { name: /Гость/ }).first().click();
await guestPage.waitForURL("**/me", { timeout: 15000 });
await guestPage.waitForTimeout(1200);
await guestPage.screenshot({ path: path.join(outDir, "guest-dashboard.png") });
await guestPage.goto(`${base}/me/bookings`, { waitUntil: "networkidle" });
await guestPage.waitForTimeout(1000);
await guestPage.screenshot({ path: path.join(outDir, "guest-bookings.png") });
await guestPage.goto(`${base}/me/invoices`, { waitUntil: "networkidle" });
await guestPage.waitForTimeout(1000);
await guestPage.screenshot({ path: path.join(outDir, "guest-invoices.png") });

console.log("ERRORS:", JSON.stringify(errors, null, 2));
await browser.close();

```
