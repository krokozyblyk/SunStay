import {
  BarChart3,
  Bell,
  BookOpen,
  CalendarDays,
  CircleHelp,
  DatabaseBackup,
  Grid3X3,
  Home,
  Languages,
  LayoutDashboard,
  ListPlus,
  LogOut,
  Menu,
  MessageSquare,
  Moon,
  Package,
  ReceiptText,
  Search,
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
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAuth, type User } from "../lib/auth";
import { useI18n } from "../lib/i18n";
import { useTheme } from "../lib/theme";
import { CurrencySelect } from "../lib/currency";
import { api, getErrorMessage } from "../lib/api";
import { useRealtime } from "../lib/realtime";
import { cn, formatDate, formatDateTime, ROLE_LABELS, statusLabel } from "../lib/utils";
import { Avatar, Button, EmptyState, Input, Modal, Spinner } from "./ui";

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
  const { lang } = useI18n();
  const navigate = useNavigate();
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-40 border-b border-line/70 bg-canvas/90 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-[1240px] items-center justify-between gap-4 px-4 md:px-6">
          <Brand />
          <nav className="hidden items-center gap-6 text-sm font-medium text-muted md:flex">
            <Link to="/" className="hover:text-ink">{lang === "en" ? "Rooms" : "Номера"}</Link>
            <Link to="/search" className="hover:text-ink">{lang === "en" ? "Booking" : "Бронирование"}</Link>
          </nav>
          <div className="flex items-center gap-2">
            <CurrencySelect />
            <LanguageToggle compact />
            <ThemeToggle compact />
            {user ? (
              <div className="flex items-center gap-2">
                <Link
                  to={homeForRole(user)}
                  className="hidden items-center gap-2 rounded-xl border border-line bg-surface px-3 py-2 text-sm font-semibold text-ink sm:flex"
                >
                  <Avatar name={user.full_name} className="h-7 w-7 text-[10px]" />
                  {user.role_code === "GUEST" ? (lang === "en" ? "My account" : "Личный кабинет") : (lang === "en" ? "Dashboard" : "Панель")}
                </Link>
                <Button variant="ghost" size="sm" onClick={() => logout().then(() => navigate("/"))}>
                  <LogOut size={15} /> Выйти
                </Button>
              </div>
            ) : (
              <>
                <Link to="/login" className="hidden text-sm font-semibold text-ink hover:text-terracotta sm:block">
                  {lang === "en" ? "Sign in" : "Войти"}
                </Link>
                <Link to="/search" className="btn-primary btn-sm">{lang === "en" ? "Book now" : "Забронировать"}</Link>
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

function NotificationBell() {
  const { user } = useAuth();
  const base = user?.role_code === "GUEST" ? "/guest/notifications" : "/notifications";
  const [open, setOpen] = useState(false);
  const queryClient = useQueryClient();
  const countQuery = useQuery({
    queryKey: ["notifications-count", base],
    queryFn: () => api.get(`${base}/unread-count`).then((response) => response.data),
    refetchInterval: 30000,
  });
  const listQuery = useQuery({
    queryKey: ["guest-notifications"],
    queryFn: () => api.get(base).then((response) => response.data),
    enabled: open,
  });
  const readMutation = useMutation({
    mutationFn: (id: number) => api.post(`${base}/${id}/read`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["guest-notifications"] }),
    onError: (error) => getErrorMessage(error),
  });
  const readAllMutation = useMutation({
    mutationFn: () => api.post(`${base}/read-all`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["guest-notifications"] }),
  });

  const unread = Number(countQuery.data?.count ?? 0);
  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="relative flex h-9 w-9 items-center justify-center rounded-xl border border-line bg-surface text-muted hover:text-ink"
        title="Уведомления"
      >
        <Bell size={17} />
        {unread > 0 && (
          <span className="absolute -right-1.5 -top-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-terracotta px-1 text-[10px] font-bold text-white">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </button>
      <Modal
        open={open}
        title="Уведомления"
        subtitle="Новости по вашим бронированиям"
        onClose={() => setOpen(false)}
        footer={<Button variant="secondary" onClick={() => readAllMutation.mutate()}>Прочитать все</Button>}
      >
        {listQuery.isLoading && <Spinner />}
        {!listQuery.isLoading && !(listQuery.data ?? []).length && (
          <p className="py-6 text-center text-sm text-muted">Уведомлений пока нет.</p>
        )}
        <div className="max-h-[60vh] space-y-2 overflow-y-auto">
          {(listQuery.data ?? []).map((item: any) => (
            <button
              key={item.notification_id}
              onClick={() => readMutation.mutate(item.notification_id)}
              className={`block w-full rounded-xl border p-3 text-left transition ${item.read_at ? "border-line bg-surface" : "border-terracotta/40 bg-terracotta/8"}`}
            >
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm font-semibold text-ink">{item.title}</p>
                {!item.read_at && <span className="h-2 w-2 shrink-0 rounded-full bg-terracotta" />}
              </div>
              {item.body && <p className="mt-1 text-xs text-muted">{item.body}</p>}
              <p className="mt-1 text-[10px] text-muted">{formatDateTime(item.created_at)}</p>
            </button>
          ))}
        </div>
      </Modal>
    </>
  );
}

function GlobalSearch() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const navigate = useNavigate();
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen(true);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);
  const searchQuery = useQuery({
    queryKey: ["global-search", query],
    queryFn: () => api.get("/manager/search", { params: { q: query } }).then((response) => response.data),
    enabled: open && query.trim().length >= 2,
  });
  const results = searchQuery.data;
  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="hidden items-center gap-2 rounded-xl border border-line bg-surface px-3 py-2 text-xs text-muted hover:text-ink md:flex"
      >
        <Search size={15} /> Поиск <kbd className="rounded bg-surface2 px-1.5 py-0.5 font-mono text-[10px]">Ctrl K</kbd>
      </button>
      <Modal open={open} title="Глобальный поиск" subtitle="Брони, гости и номера" onClose={() => setOpen(false)}>
        <Input autoFocus value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Имя гостя, номер, № брони…" />
        <div className="mt-3 max-h-[60vh] space-y-3 overflow-y-auto">
          {searchQuery.isLoading && <Spinner />}
          {!searchQuery.isLoading && results && !results.bookings?.length && !results.guests?.length && !results.rooms?.length && (
            <EmptyState title="Ничего не найдено" />
          )}
          {results?.bookings?.length > 0 && (
            <div>
              <p className="label mb-1">Бронирования</p>
              {results.bookings.map((booking: any) => (
                <button key={booking.booking_id} className="flex w-full items-center justify-between gap-2 rounded-lg px-2 py-1.5 text-sm hover:bg-surface2" onClick={() => { setOpen(false); navigate(`/app/bookings/${booking.booking_id}`); }}>
                  <span>#{booking.booking_id} · {booking.guest_name}</span>
                  <span className="text-xs text-muted">{booking.room_number} · {statusLabel(booking.status)}</span>
                </button>
              ))}
            </div>
          )}
          {results?.guests?.length > 0 && (
            <div>
              <p className="label mb-1">Гости</p>
              {results.guests.map((guest: any) => (
                <button key={guest.guest_id} className="flex w-full items-center justify-between gap-2 rounded-lg px-2 py-1.5 text-sm hover:bg-surface2" onClick={() => { setOpen(false); navigate(`/app/bookings?search=${encodeURIComponent(guest.full_name)}`); }}>
                  <span>{guest.full_name}</span>
                  <span className="text-xs text-muted">{guest.phone_masked} · {guest.bookings_count} броней</span>
                </button>
              ))}
            </div>
          )}
          {results?.rooms?.length > 0 && (
            <div>
              <p className="label mb-1">Номера</p>
              {results.rooms.map((room: any) => (
                <button key={room.room_id} className="flex w-full items-center justify-between gap-2 rounded-lg px-2 py-1.5 text-sm hover:bg-surface2" onClick={() => { setOpen(false); navigate("/app/room-grid"); }}>
                  <span>№{room.room_number} · {room.room_type}</span>
                  <span className="text-xs text-muted">{room.status}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </Modal>
    </>
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
  const reviews = { to: "/app/admin/reviews", label: "Отзывы", icon: <MessageSquare size={18} /> };
  const sessions = { to: "/app/admin/sessions", label: "Сессии", icon: <ShieldCheck size={18} /> };
  const waitlist = { to: "/app/waitlist", label: "Лист ожидания", icon: <ListPlus size={18} /> };
  const floorPlan = { to: "/app/floor-plan", label: "План этажа", icon: <Home size={18} /> };
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
          { to: "/me/loyalty", label: "Бонусы", icon: <Sparkles size={18} /> },
          { to: "/me/profile", label: t("guestProfile"), icon: <UserRound size={18} /> },
        ],
      },
    ];
  }
  if (role === "HOUSEKEEPING") {
    return [{ group: "Операции", items: [hk, maintenance, consumables] }];
  }
  if (role === "MANAGER") {
    return [{ group: "Управление", items: [dashboard, grid, floorPlan, bookings, folios, waitlist, hk, reports] }];
  }
  if (role === "HOTEL_MANAGER") {
    return [
      { group: "Управление", items: [dashboard, reports, grid, floorPlan, bookings, folios, waitlist, hk] },
      { group: "Администрирование", items: [directories, employees, reviews, audit] },
    ];
  }
  return [
    { group: "Управление", items: [dashboard, grid, floorPlan, bookings, folios, waitlist, hk, reports] },
    { group: "Администрирование", items: [users, sessions, directories, reviews, audit, backups, maintenance, consumables, settings] },
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

function OnboardingTour() {
  const [step, setStep] = useState(0);
  const [hidden, setHidden] = useState(() => localStorage.getItem("sunstay_tour_hidden") === "1");
  const steps = [
    "Используйте меню слева, чтобы перейти в нужный раздел.",
    "Иконка уведомлений показывает новые события по броням.",
    "Настройки темы и языка — в правом верхнем углу.",
  ];
  if (hidden) return null;
  return (
    <div className="fixed bottom-5 right-5 z-[80] w-[300px] rounded-2xl border border-line bg-surface p-4 shadow-float">
      <p className="label text-terracotta">Подсказка {step + 1} из {steps.length}</p>
      <p className="mt-2 text-sm text-ink">{steps[step]}</p>
      <div className="mt-4 flex flex-wrap gap-2">
        {step < steps.length - 1 ? (
          <Button size="sm" onClick={() => setStep(step + 1)}>Далее</Button>
        ) : (
          <Button size="sm" onClick={() => { localStorage.setItem("sunstay_tour_hidden", "1"); setHidden(true); }}>Понятно</Button>
        )}
        <Button size="sm" variant="ghost" onClick={() => { localStorage.setItem("sunstay_tour_hidden", "1"); setHidden(true); }}>Скрыть подсказки</Button>
      </div>
    </div>
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

  const isStaff = user?.role_code !== "GUEST";
  useRealtime(isStaff);
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
            {isStaff && <GlobalSearch />}
            <NotificationBell />
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
        <OnboardingTour />
      </div>
      <HotkeysModal open={hotkeysOpen} onClose={() => setHotkeysOpen(false)} />
    </div>
  );
}
