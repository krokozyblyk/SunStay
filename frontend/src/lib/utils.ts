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
  if (["CONFIRMED", "CHECKED_IN", "DONE", "ЧИСТЫЙ_ГОТОВ", "ГОТОВ"].includes(status)) return "success";
  if (["NEW", "ASSIGNED", "OPEN", "В_УБОРКЕ", "ГРЯЗНЫЙ", "ОЖИДАЕТ", "ЗАБРОНИРОВАН"].includes(status)) return "warning";
  if (["CANCELLED", "NO_SHOW", "СВОБОДЕН", "ТРЕБУЕТ УБОРКИ"].includes(status)) return "danger";
  if (["IN_PROGRESS", "ЗАСЕЛЁН", "CHECKED_OUT"].includes(status)) return "info";
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

export function statusColor(status?: string | null) {
  const tone = statusTone(status);
  const map: Record<StatusTone, string> = {
    success: "#2f9d6d",
    warning: "#d99420",
    danger: "#e05252",
    info: "#3d9bc4",
    neutral: "#8b938c",
  };
  return map[tone];
}

export function statusTextClass(status?: string | null) {
  const tone = statusTone(status);
  const map: Record<StatusTone, string> = {
    success: "text-emerald-700 dark:text-emerald-300",
    warning: "text-amber-700 dark:text-amber-300",
    danger: "text-rose-700 dark:text-rose-300",
    info: "text-sky-700 dark:text-sky-300",
    neutral: "text-muted",
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

export function asset(path: string) {
  const base = import.meta.env.BASE_URL || "/";
  if (path.startsWith(base)) return path;
  return `${base}${path.replace(/^\//, "")}`;
}

export function resolveImage(value?: string | null, fallback = "") {
  if (!value) return fallback;
  if (value.startsWith("http") || value.startsWith("data:")) return value;
  return asset(value);
}

export function roomImageByName(name?: string | null) {
  const value = (name ?? "").toLowerCase();
  if (value.includes("стандарт")) return "images/rooms/standard-4.jpg";
  if (value.includes("комфорт")) return "images/rooms/comfort-4.jpg";
  if (value.includes("люкс")) return "images/rooms/lux-4.jpg";
  return "images/rooms/standard-4.jpg";
}

export function serviceImageByName(name?: string | null) {
  const value = (name ?? "").toLowerCase();
  if (value.includes("завтрак")) return "images/services/breakfast.jpg";
  if (value.includes("парков")) return "images/services/parking.jpg";
  if (value.includes("трансфер") || value.includes("аэропорт")) return "images/services/transfer.jpg";
  if (value.includes("спа") || value.includes("массаж")) return "images/services/spa.jpg";
  return "images/service-other.jpg";
}
