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
  Badge,
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
  resolveImage,
  roomImageByName,
  statusClass,
  statusLabel,
  statusTextClass,
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
  const lastNight = addDaysISO(checkout, -1);
  const seasonalRates = rates.filter((rate: any) =>
    (!rate.season_start || rate.season_start <= checkin) &&
    (!rate.season_end || rate.season_end >= lastNight)
  );
  useEffect(() => {
    const pool = seasonalRates.length ? seasonalRates : rates;
    if (pool.length && !pool.some((rate: any) => rate.rate_id === Number(rateId))) {
      setRateId(pool[0].rate_id);
    }
  }, [roomId, checkin, checkout, ratesQuery.data]);

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
  const forecastQuery = useQuery({
    queryKey: ["forecast-7"],
    queryFn: () => api.get("/reports/forecast", { params: { days: 7 } }).then((response) => response.data),
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

      <Card className="mt-5">
        <div className="mb-3 flex items-center justify-between">
          <div>
            <h2 className="font-display text-2xl font-semibold">Прогноз загрузки</h2>
            <p className="text-sm text-muted">Ожидаемая загрузка на ближайшие 7 дней по текущим броням.</p>
          </div>
          <Button variant="ghost" size="sm" onClick={() => navigate("/app/reports")}>Отчёты <ChevronRight size={14} /></Button>
        </div>
        <div className="h-56">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={forecastQuery.data?.series ?? []}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="day" tickFormatter={(value) => formatDate(value).slice(0, 5)} tick={{ fontSize: 11, fill: "var(--muted)" }} />
              <YAxis domain={[0, 100]} unit="%" tick={{ fontSize: 11, fill: "var(--muted)" }} />
              <Tooltip formatter={(value: any) => [`${value}%`, "Загрузка"]} labelFormatter={(value) => formatDate(String(value))} />
              <Bar dataKey="occupancy_pct" fill="#123B36" radius={[6, 6, 0, 0]} maxBarSize={42} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </Card>

      <Card className="mt-5">
        <h2 className="font-display text-2xl font-semibold">Быстрые действия</h2>
        <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          <Button variant="secondary" onClick={() => navigate("/app/bookings?new=1")}><Plus size={15} /> Новая бронь</Button>
          <Button variant="secondary" onClick={() => navigate("/app/room-grid")}><CalendarDays size={15} /> Шахматка</Button>
          <Button variant="secondary" onClick={() => navigate("/app/housekeeping")}><Check size={15} /> Задачи</Button>
          <Button variant="secondary" onClick={() => navigate("/app/maintenance")}><AlertTriangle size={15} /> Техзаявки</Button>
        </div>
      </Card>

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
  const { toast } = useToast();
  const queryClient = useQueryClient();
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
  const moveMutation = useMutation({
    mutationFn: ({ id, roomId, checkin, checkout }: { id: number; roomId: number; checkin: string; checkout: string }) =>
      api.post(`/manager/bookings/${id}/move`, { room_id: roomId, checkin_date: checkin, checkout_date: checkout }),
    onSuccess: () => {
      toast("Бронь перенесена", "success");
      queryClient.invalidateQueries({ queryKey: ["room-grid"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
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
                    <p className={`text-[11px] ${statusTextClass(room.status)}`}>{room.room_type} · {statusLabel(room.status)}</p>
                  </td>
                  {days.map((day) => {
                    const booking = bookingFor(room.room_id, day);
                    if (booking) {
                      return (
                        <td key={day} className="border-l border-line p-1 align-middle">
                          <button
                            draggable
                            onDragStart={(event) => { event.dataTransfer.setData("text/plain", String(booking.booking_id)); event.dataTransfer.effectAllowed = "move"; }}
                            className="flex h-9 w-full cursor-grab items-center justify-center rounded-lg transition hover:bg-surface2 active:cursor-grabbing"
                            onClick={() => navigate(`/app/bookings/${booking.booking_id}`)}
                            title={`Бронь #${booking.booking_id} · ${statusLabel(booking.status)}. Перетащите на свободную ячейку.`}
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
                          onDragOver={(event) => { event.preventDefault(); event.dataTransfer.dropEffect = "move"; }}
                          onDrop={(event) => {
                            event.preventDefault();
                            const id = Number(event.dataTransfer.getData("text/plain"));
                            const moved = bookings.find((item: any) => item.booking_id === id);
                            if (!moved) return;
                            const nights = Math.max(1, Math.round((new Date(`${moved.checkout_date}T12:00:00`).getTime() - new Date(`${moved.checkin_date}T12:00:00`).getTime()) / 86400000));
                            moveMutation.mutate({ id, roomId: room.room_id, checkin: day, checkout: addDaysISO(day, nights) });
                          }}
                          title="Создать бронь или перетащите сюда бронь"
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
  const [massOpen, setMassOpen] = useState(false);
  const [massSearch, setMassSearch] = useState("");
  const [massSelected, setMassSelected] = useState<number[]>([]);
  const [massTemplate, setMassTemplate] = useState("");
  const massGuestsQuery = useQuery({
    queryKey: ["mass-guests", massSearch],
    queryFn: () => api.get("/manager/search", { params: { q: massSearch } }).then((response) => response.data),
    enabled: massOpen && massSearch.trim().length >= 2,
  });
  const templatesQuery = useQuery({
    queryKey: ["message-templates"],
    queryFn: () => api.get("/manager/message-templates").then((response) => response.data),
    enabled: massOpen,
  });
  const massSendMutation = useMutation({
    mutationFn: () => api.post("/manager/notifications/send", { guest_ids: massSelected, template_id: massTemplate ? Number(massTemplate) : null }),
    onSuccess: (response) => {
      toast(`Отправлено: ${response.data?.sent ?? massSelected.length}`, "success");
      setMassOpen(false);
      setMassSelected([]);
      setMassTemplate("");
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const filters = { status: status === "all" ? undefined : status, search: search || undefined, date_from: dateFrom || undefined, date_to: dateTo || undefined, page, page_size: pageSize };

  const query = useQuery({
    queryKey: ["manager-bookings", filters],
    queryFn: () => api.get("/manager/bookings", { params: filters }).then((response) => response.data),
  });
  const bulkMutation = useMutation({
    mutationFn: (action: "confirm" | "cancel") =>
      api.post("/manager/bookings/bulk", { ids: selected, action }).then((response) => response.data),
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
            <Button variant="secondary" onClick={() => setMassOpen(true)}>Рассылка</Button>
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
      <Modal
        open={massOpen}
        title="Рассылка гостям"
        subtitle="Найдите гостей по имени и отправьте уведомление в кабинет."
        onClose={() => setMassOpen(false)}
        footer={<><Button variant="secondary" onClick={() => setMassOpen(false)}>Отмена</Button><Button onClick={() => massSendMutation.mutate()} disabled={massSendMutation.isPending || !massSelected.length || !massTemplate}>Отправить</Button></>}
      >
        <div className="space-y-3">
          <Input label="Поиск гостя" value={massSearch} onChange={(event) => setMassSearch(event.target.value)} placeholder="Имя или email" />
          {massSearch.trim().length >= 2 && (
            <div className="max-h-48 space-y-1 overflow-y-auto">
              {(massGuestsQuery.data?.guests ?? []).map((guest: any) => (
                <label key={guest.guest_id} className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-sm hover:bg-surface2">
                  <input type="checkbox" checked={massSelected.includes(guest.guest_id)} onChange={(event) => setMassSelected((current) => event.target.checked ? [...current, guest.guest_id] : current.filter((id) => id !== guest.guest_id))} />
                  <span>{guest.full_name}</span>
                  <span className="ml-auto text-xs text-muted">{guest.email}</span>
                </label>
              ))}
              {!massGuestsQuery.isLoading && !(massGuestsQuery.data?.guests ?? []).length && <p className="text-xs text-muted">Ничего не найдено.</p>}
            </div>
          )}
          <Select label="Шаблон" value={massTemplate} onChange={(event) => setMassTemplate(event.target.value)}>
            <option value="">Выберите шаблон</option>
            {(templatesQuery.data ?? []).map((template: any) => <option key={template.template_id} value={template.template_id}>{template.name}</option>)}
          </Select>
          <p className="text-xs text-muted">Выбрано гостей: {massSelected.length}</p>
        </div>
      </Modal>
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
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [detailsForm, setDetailsForm] = useState({ checkin_date: "", checkout_date: "", adults: 1, children: 0, special_requests: "" });
  const detailsMutation = useMutation({
    mutationFn: () => api.patch(`/manager/bookings/${id}/details`, detailsForm),
    onSuccess: () => {
      toast("Данные брони обновлены", "success");
      setDetailsOpen(false);
      queryClient.invalidateQueries({ queryKey: ["manager-booking", id] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  const query = useQuery({
    queryKey: ["manager-booking", id],
    queryFn: () => api.get(`/manager/bookings/${id}`).then((response) => response.data),
    enabled: Boolean(id),
  });
  const roomsQuery = useQuery({ queryKey: ["manager-rooms"], queryFn: () => api.get("/manager/rooms").then((response) => response.data) });
  const reasonsQuery = useQuery({ queryKey: ["manager-cancellation-reasons"], queryFn: () => api.get("/manager/cancellation-reasons").then((response) => response.data) });
  const [notifyOpen, setNotifyOpen] = useState(false);
  const [templateId, setTemplateId] = useState("");
  const templatesQuery = useQuery({
    queryKey: ["message-templates"],
    queryFn: () => api.get("/manager/message-templates").then((response) => response.data),
    enabled: notifyOpen,
  });
  const notifyMutation = useMutation({
    mutationFn: () => api.post(`/manager/guests/${query.data?.booking?.guest_id}/notify`, { template_id: templateId ? Number(templateId) : null }),
    onSuccess: () => {
      toast("Уведомление отправлено гостю", "success");
      setNotifyOpen(false);
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

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
            <Button variant="secondary" onClick={() => { setDetailsForm({ checkin_date: String(booking.checkin_date).slice(0, 10), checkout_date: String(booking.checkout_date).slice(0, 10), adults: booking.adults, children: booking.children, special_requests: booking.special_requests ?? "" }); setDetailsOpen(true); }}>Изменить бронь</Button>
            <Button variant="secondary" onClick={() => setNotifyOpen(true)}>Уведомить гостя</Button>
            {booking.status === "NEW" && <Button onClick={() => actionMutation.mutate({ action: "confirm" })}><Check size={15} /> Подтвердить</Button>}
            {canCheckIn && <Button onClick={() => setCheckInOpen(true)}><LogIn size={15} /> Заселить</Button>}
            {canCheckOut && <Button onClick={() => setCheckOutOpen(true)}><LogOut size={15} /> Выселить</Button>}
            {canCancel && <Button variant="danger" onClick={() => setCancelOpen(true)}><X size={15} /> Отменить</Button>}
          </>
        }
      />
      <Modal
        open={notifyOpen}
        title="Уведомить гостя"
        subtitle={booking.guest_name}
        onClose={() => setNotifyOpen(false)}
        footer={<><Button variant="secondary" onClick={() => setNotifyOpen(false)}>Отмена</Button><Button onClick={() => notifyMutation.mutate()} disabled={notifyMutation.isPending || !templateId}>Отправить</Button></>}
      >
        <Select label="Шаблон сообщения" value={templateId} onChange={(event) => setTemplateId(event.target.value)}>
          <option value="">Выберите шаблон</option>
          {(templatesQuery.data ?? []).map((template: any) => <option key={template.template_id} value={template.template_id}>{template.name}</option>)}
        </Select>
        <p className="mt-3 text-xs text-muted">Уведомление появится в личном кабинете гостя.</p>
      </Modal>
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
              <div className="rounded-xl bg-surface2 p-4"><img src={resolveImage(booking.room_image, roomImageByName(booking.room_type))} alt={booking.room_type} loading="lazy" className="mb-3 h-28 w-full rounded-lg object-cover" /><p className="label">Проживание</p><p className="mt-2 text-sm text-muted">Заезд: {formatDate(booking.checkin_date)}</p><p className="text-sm text-muted">Выезд: {formatDate(booking.checkout_date)}</p><p className="text-sm text-muted">Время заезда: {String(booking.arrival_time ?? "—").slice(0, 5)}</p><p className="text-sm text-muted">Держать до: {booking.hold_until ? formatDateTime(booking.hold_until) : "—"}</p><p className="text-sm text-muted">Тариф: {booking.rate_name}</p><p className="text-sm text-muted">Гостей: {booking.adults + booking.children}</p>{booking.special_requests && <p className="mt-2 text-sm text-terracotta">Пожелания: {booking.special_requests}</p>}</div>
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

      <Modal
        open={detailsOpen}
        title="Изменить данные брони"
        subtitle="Даты, количество гостей и пожелания"
        onClose={() => setDetailsOpen(false)}
        footer={<><Button variant="secondary" onClick={() => setDetailsOpen(false)}>Отмена</Button><Button onClick={() => detailsMutation.mutate()} disabled={detailsMutation.isPending}>Сохранить</Button></>}
      >
        <div className="grid gap-3 md:grid-cols-2">
          <Input label="Заезд" type="date" value={detailsForm.checkin_date} onChange={(event) => setDetailsForm({ ...detailsForm, checkin_date: event.target.value })} />
          <Input label="Выезд" type="date" value={detailsForm.checkout_date} onChange={(event) => setDetailsForm({ ...detailsForm, checkout_date: event.target.value })} />
          <Input label="Взрослые" type="number" value={detailsForm.adults} onChange={(event) => setDetailsForm({ ...detailsForm, adults: Number(event.target.value) })} />
          <Input label="Дети" type="number" value={detailsForm.children} onChange={(event) => setDetailsForm({ ...detailsForm, children: Number(event.target.value) })} />
        </div>
        <div className="mt-3">
          <Input label="Особые пожелания" value={detailsForm.special_requests} onChange={(event) => setDetailsForm({ ...detailsForm, special_requests: event.target.value })} />
        </div>
      </Modal>
      <Modal open={checkInOpen} title="Заселение гостя" subtitle="Проверьте документ и при необходимости примите депозит." onClose={() => setCheckInOpen(false)} footer={<><Button variant="secondary" onClick={() => setCheckInOpen(false)}>Отмена</Button><Button onClick={() => actionMutation.mutate({ action: "check-in", payload: checkInForm })} disabled={actionMutation.isPending}>Подтвердить заселение</Button></>}>
        <div className="space-y-3">
          <Input label="Документ гостя (необязательно — возьмём из профиля)" value={checkInForm.document_number} onChange={(event) => setCheckInForm({ ...checkInForm, document_number: event.target.value })} placeholder="Оставьте пустым, чтобы использовать данные гостя" />
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
      if (action === "payment") return api.post(`/manager/folios/${folioId}/payments`, payload, { headers: { "Idempotency-Key": crypto.randomUUID() } });
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

export function WaitlistPage() {
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const query = useQuery({
    queryKey: ["waitlist", status, search],
    queryFn: () => api.get("/manager/waitlist", { params: { status: status || undefined, search: search || undefined } }).then((response) => response.data),
  });
  const mutation = useMutation({
    mutationFn: ({ id, nextStatus }: { id: number; nextStatus: string }) =>
      api.patch(`/manager/waitlist/${id}`, { status: nextStatus }),
    onSuccess: () => {
      toast("Лист ожидания обновлён", "success");
      queryClient.invalidateQueries({ queryKey: ["waitlist"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const [convertEntry, setConvertEntry] = useState<any>(null);
  const [convertForm, setConvertForm] = useState({ room_id: "", rate_id: "", document_number: "" });
  const roomsQuery = useQuery({ queryKey: ["manager-rooms"], queryFn: () => api.get("/manager/rooms").then((response) => response.data) });
  const ratesQuery = useQuery({ queryKey: ["manager-rates"], queryFn: () => api.get("/manager/rates").then((response) => response.data) });
  const convertRoom = (roomsQuery.data ?? []).find((room: any) => String(room.room_id) === convertForm.room_id);
  useEffect(() => {
    if (!convertRoom) return;
    const matching = (ratesQuery.data ?? []).filter((rate: any) => rate.room_type_id === convertRoom.room_type_id);
    if (matching.length && !matching.some((rate: any) => String(rate.rate_id) === convertForm.rate_id)) {
      setConvertForm((current) => ({ ...current, rate_id: String(matching[0].rate_id) }));
    }
  }, [convertForm.room_id, ratesQuery.data]);
  const convertMutation = useMutation({
    mutationFn: () => api.post(`/manager/waitlist/${convertEntry.waitlist_id}/convert`, {
      room_id: Number(convertForm.room_id),
      rate_id: Number(convertForm.rate_id),
      document_number: convertForm.document_number,
    }),
    onSuccess: () => {
      toast("Бронь создана из листа ожидания", "success");
      setConvertEntry(null);
      setConvertForm({ room_id: "", rate_id: "", document_number: "" });
      queryClient.invalidateQueries({ queryKey: ["waitlist"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  const rows = query.data ?? [];
  const statusLabels: Record<string, string> = {
    WAITING: "Ожидает",
    NOTIFIED: "Уведомлён",
    CONVERTED: "Преобразован",
    CANCELLED: "Отменён",
  };
  return (
    <div className="space-y-5">
      <PageHeader title="Лист ожидания" subtitle="Заявки гостей на даты, когда не было свободных номеров." />
      <Card className="flex flex-wrap items-end gap-3">
        <Select label="Статус" value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="">Все</option>
          <option value="WAITING">Ожидает</option>
          <option value="NOTIFIED">Уведомлён</option>
          <option value="CONVERTED">Преобразован</option>
          <option value="CANCELLED">Отменён</option>
        </Select>
        <div className="min-w-64 flex-1">
          <Input label="Поиск" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Имя или email" />
        </div>
        <Button variant="secondary" onClick={() => query.refetch()}><RefreshCw size={15} /> Обновить</Button>
      </Card>
      {query.isLoading && <Spinner />}
      {query.isError && <ErrorState message={getErrorMessage(query.error)} />}
      {!query.isLoading && !rows.length && <EmptyState title="Заявок нет" description="Здесь появятся заявки из листа ожидания." />}
      <div className="space-y-3">
        {rows.map((row: any) => (
          <Card key={row.waitlist_id}>
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="font-display text-xl font-semibold">{row.guest_name}</h3>
                  <Badge tone={row.status === "WAITING" ? "warning" : row.status === "CONVERTED" ? "success" : row.status === "CANCELLED" ? "danger" : "info"}>
                    {statusLabels[row.status] ?? row.status}
                  </Badge>
                </div>
                <p className="mt-1 text-sm text-muted">{formatDate(row.checkin_date)} — {formatDate(row.checkout_date)} · {row.adults + row.children} гостей · {row.room_type || "любой тип"}</p>
                <p className="mt-1 text-sm text-muted">{row.phone_masked || "телефон не указан"} {row.email ? `· ${row.email}` : ""}</p>
                {row.note && <p className="mt-2 rounded-xl bg-surface2 px-3 py-2 text-sm text-muted">{row.note}</p>}
              </div>
              <div className="flex flex-wrap gap-2">
                {row.status === "WAITING" && <Button size="sm" variant="secondary" onClick={() => mutation.mutate({ id: row.waitlist_id, nextStatus: "NOTIFIED" })} disabled={mutation.isPending}>Уведомить</Button>}
                {["WAITING", "NOTIFIED"].includes(row.status) && <Button size="sm" onClick={() => { setConvertEntry(row); setConvertForm({ room_id: "", rate_id: "", document_number: "" }); }}><Check size={14} /> Создать бронь</Button>}
                {["WAITING", "NOTIFIED"].includes(row.status) && <Button size="sm" variant="ghost" onClick={() => mutation.mutate({ id: row.waitlist_id, nextStatus: "CANCELLED" })} disabled={mutation.isPending}><X size={14} /> Отменить</Button>}
              </div>
            </div>
          </Card>
        ))}
      </div>
      <Modal
        open={Boolean(convertEntry)}
        title="Создать бронь из листа ожидания"
        subtitle={convertEntry?.guest_name}
        onClose={() => setConvertEntry(null)}
        footer={<><Button variant="secondary" onClick={() => setConvertEntry(null)}>Отмена</Button><Button onClick={() => convertMutation.mutate()} disabled={convertMutation.isPending || !convertForm.room_id || !convertForm.rate_id || convertForm.document_number.length < 3}>Создать</Button></>}
      >
        <div className="space-y-3">
          <Select label="Номер" value={convertForm.room_id} onChange={(event) => setConvertForm({ ...convertForm, room_id: event.target.value })}>
            <option value="">Выберите номер</option>
            {(roomsQuery.data ?? []).map((room: any) => <option key={room.room_id} value={room.room_id}>№{room.room_number} · {room.room_type} · {room.status}</option>)}
          </Select>
          <Select label="Тариф" value={convertForm.rate_id} onChange={(event) => setConvertForm({ ...convertForm, rate_id: event.target.value })}>
            <option value="">Выберите тариф</option>
            {(ratesQuery.data ?? []).filter((rate: any) => !convertRoom || rate.room_type_id === convertRoom.room_type_id).map((rate: any) => <option key={rate.rate_id} value={rate.rate_id}>{rate.name} · {formatMoney(rate.price_per_night)}</option>)}
          </Select>
          <Input label="Документ гостя" value={convertForm.document_number} onChange={(event) => setConvertForm({ ...convertForm, document_number: event.target.value })} placeholder="4510 123456" />
          <p className="text-xs text-muted">Гость: {convertEntry?.guest_name} · {formatDate(convertEntry?.checkin_date)} — {formatDate(convertEntry?.checkout_date)}</p>
        </div>
      </Modal>
    </div>
  );
}

export function FloorPlanPage() {
  const query = useQuery({
    queryKey: ["floor-plan"],
    queryFn: () => api.get("/manager/floor-plan").then((response) => response.data),
  });
  if (query.isLoading) return <Spinner />;
  if (query.isError) return <ErrorState message={getErrorMessage(query.error)} />;
  const floors = query.data ?? [];
  return (
    <div className="space-y-6">
      <PageHeader title="План этажа" subtitle="Схематичное расположение номеров по этажам и их текущий статус." />
      {floors.map((floor: any) => (
        <Card key={floor.floor}>
          <h2 className="font-display text-2xl font-semibold">Этаж {floor.floor}</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {floor.rooms.map((room: any) => (
              <div key={room.room_id} className={`rounded-xl border border-line p-4 ${room.booking_id ? "bg-terracotta/6" : "bg-surface"}`}>
                <div className="flex items-center justify-between">
                  <p className="font-display text-xl font-semibold">№{room.room_number}</p>
                  <span className={`status-pill ${statusClass(room.status)}`}>{statusLabel(room.status)}</span>
                </div>
                <p className="mt-1 text-xs text-muted">{room.room_type} · до {room.capacity} гостей</p>
                {room.booking_id ? (
                  <Link to={`/app/bookings/${room.booking_id}`} className="mt-2 block text-sm font-semibold text-terracotta hover:underline">
                    {room.guest_name} · до {formatDate(room.checkout_date)}
                  </Link>
                ) : <p className="mt-2 text-sm text-muted">Свободен</p>}
              </div>
            ))}
          </div>
        </Card>
      ))}
    </div>
  );
}
