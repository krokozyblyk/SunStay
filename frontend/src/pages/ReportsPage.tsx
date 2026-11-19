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
