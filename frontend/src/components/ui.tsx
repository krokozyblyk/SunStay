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
  useRef,
  useState,
  type ButtonHTMLAttributes,
  type CSSProperties,
  type ChangeEvent,
  type InputHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
} from "react";
import { cn, initials, statusClass, statusColor, statusLabel } from "../lib/utils";
import { useI18n } from "../lib/i18n";

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

const PAGE_TRANSLATIONS: Record<string, string> = {
  "Операционный обзор": "Operations overview",
  "Загрузка, заезды, выезды и состояние номерного фонда на сегодня.": "Occupancy, arrivals, departures and room status for today.",
  "Шахматка номеров": "Room grid",
  "Визуальная сетка номеров и броней. Нажмите на свободную ячейку, чтобы создать бронь.": "Visual room and booking grid. Click an empty cell to create a booking.",
  "Реестр бронирований": "Bookings registry",
  "Поиск, фильтры и массовые операции с бронями.": "Search, filters and bulk booking actions.",
  "Folio и платежи": "Folio & payments",
  "Начисления, платежи, возвраты и баланс.": "Charges, payments, refunds and balance.",
  "Отчёты": "Reports",
  "Отчеты": "Reports",
  "Доска хаускипинга": "Housekeeping board",
  "Заявки на ремонт": "Maintenance requests",
  "Расходные материалы": "Consumables",
  "Пользователи и роли": "Users & roles",
  "Сотрудники": "Employees",
  "Назначение ролей Менеджера и Хаускипинга.": "Assign Manager and Housekeeping roles.",
  "Справочники отеля": "Hotel directories",
  "Типы номеров, номера, удобства, тарифы, услуги и другое.": "Room types, rooms, amenities, rates, services and more.",
  "Журнал аудита": "Audit log",
  "Кто, когда и что изменил. Ошибки подсвечиваются красным.": "Who changed what and when. Errors are highlighted in red.",
  "Отзывы гостей": "Guest reviews",
  "Модерация отзывов после проживания.": "Moderate reviews after check-out.",
  "Резервное копирование и мониторинг": "Backups & monitoring",
  "Статус копий, расписание и телеметрия базы данных.": "Backup status, schedule and database telemetry.",
  "Сессии пользователей": "User sessions",
  "Активные и отозванные refresh-сессии.": "Active and revoked refresh sessions.",
  "Настройки системы": "System settings",
  "Лист ожидания": "Waitlist",
  "Заявки гостей на даты, когда не было свободных номеров.": "Guest requests for dates with no available rooms.",
  "План этажа": "Floor plan",
  "Схематичное расположение номеров по этажам и их текущий статус.": "Schematic room layout by floor with current status.",
  "Мои бронирования": "My bookings",
  "Мои счета": "My invoices",
  "Дополнительные услуги": "Services",
  "Бонусные баллы": "Loyalty points",
  "Профиль и настройки": "Profile & settings",
};

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  const { lang } = useI18n();
  const tr = (value?: string) => (lang === "en" && value ? PAGE_TRANSLATIONS[value] ?? value : value);
  return (
    <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div>
        <h1 className="page-title">{tr(title)}</h1>
        {subtitle && <p className="page-subtitle max-w-3xl">{tr(subtitle)}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

export function Badge({
  children,
  tone = "neutral",
  className,
  style,
}: {
  children: ReactNode;
  tone?: "neutral" | "success" | "warning" | "danger" | "info" | "forest";
  className?: string;
  style?: CSSProperties;
}) {
  const tones = {
    neutral: "bg-surface2 text-muted",
    success: "bg-emerald-500/12 text-emerald-700 dark:text-emerald-300",
    warning: "bg-amber-500/14 text-amber-700 dark:text-amber-300",
    danger: "bg-rose-500/12 text-rose-700 dark:text-rose-300",
    info: "bg-sky-500/12 text-sky-700 dark:text-sky-300",
    forest: "bg-forest/10 text-forest dark:bg-white/10 dark:text-ink",
  };
  return <span className={cn("badge", tones[tone], className)} style={style}>{children}</span>;
}

export function StatusPill({ status }: { status?: string | null }) {
  return <span className={cn("status-pill", statusClass(status))} style={{ color: statusColor(status) }}>{statusLabel(status)}</span>;
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
  numeric,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { label?: string; numeric?: boolean }) {
  const isNumber = props.type === "number" || numeric;
  const focused = useRef(false);
  const display = (value: unknown) => (value === null || value === undefined ? "" : String(value));
  const [text, setText] = useState(() => display(props.value));

  // Only sync from the outside when the field is not being typed in. This
  // prevents the caret/focus from jumping away after every digit.
  useEffect(() => {
    if (isNumber && !focused.current) setText(display(props.value));
  }, [props.value, isNumber]);

  const handleNumber = (event: ChangeEvent<HTMLInputElement>) => {
    let next = event.target.value.replace(/[^0-9.]/g, "");
    if (next.length > 1 && next.startsWith("0") && next[1] !== ".") {
      next = next.replace(/^0+/, "") || "0";
    }
    setText(next);
    const synthetic = {
      ...event,
      target: { ...event.target, value: next },
      currentTarget: { ...event.currentTarget, value: next },
    } as ChangeEvent<HTMLInputElement>;
    props.onChange?.(synthetic);
  };

  return (
    <label className="flex flex-col gap-1.5">
      {label && <span className="label">{label}</span>}
      <input
        {...props}
        type={numeric ? "text" : props.type}
        inputMode={numeric ? "numeric" : props.inputMode}
        className={cn("input", className)}
        value={isNumber ? text : props.value}
        onFocus={(event) => { focused.current = true; props.onFocus?.(event); }}
        onBlur={(event) => {
          focused.current = false;
          if (isNumber) setText(display(props.value));
          props.onBlur?.(event);
        }}
        onChange={isNumber ? handleNumber : props.onChange}
      />
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
  const panelRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const handler = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
      if (event.key === "Tab" && panelRef.current) {
        const focusable = panelRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
        );
        if (!focusable.length) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    };
    window.addEventListener("keydown", handler);
    const timer = window.setTimeout(() => {
      const first = panelRef.current?.querySelector<HTMLElement>("input, select, textarea, button");
      first?.focus();
    }, 30);
    return () => {
      window.removeEventListener("keydown", handler);
      window.clearTimeout(timer);
    };
  }, [open, onClose]);

  if (!open) return null;
  const widths = { sm: "max-w-md", md: "max-w-2xl", lg: "max-w-4xl" };
  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm">
      <div ref={panelRef} role="dialog" aria-modal="true" aria-label={title} className={cn("card w-full animate-fade-in overflow-hidden", widths[size])}>
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
