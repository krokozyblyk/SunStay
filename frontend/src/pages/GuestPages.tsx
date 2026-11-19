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
  Star,
  Trash2,
  UserRound,
} from "lucide-react";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, downloadFile, getErrorMessage } from "../lib/api";
import { useAuth } from "../lib/auth";
import { useI18n } from "../lib/i18n";
import { useFeatures } from "../lib/features";
import { useToast } from "../components/ui";
import { Button, Card, Drawer, EmptyState, ErrorState, Input, KpiCard, Modal, PageHeader, Select, Spinner, StatusPill, Tabs, Textarea } from "../components/ui";
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
  const loyaltyQuery = useQuery({
    queryKey: ["guest-loyalty"],
    queryFn: () => api.get("/guest/loyalty").then((response) => response.data),
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
              <h2 className="font-display text-xl font-semibold">Бонусные баллы</h2>
              <Sparkles size={18} className="text-terracotta" />
            </div>
            <p className="font-display text-3xl font-semibold">{loyaltyQuery.data?.points_balance ?? 0}</p>
            <p className="mt-1 text-xs text-muted">Начисляются 5% от оплаченного проживания. Можно списать до 30% стоимости брони.</p>
            <Link to="/me/loyalty" className="btn-secondary mt-4 w-full">История баллов</Link>
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
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const features = useFeatures();
  const [cancelOpen, setCancelOpen] = useState(false);
  const [reasonId, setReasonId] = useState<number | "">("");
  const [reviewOpen, setReviewOpen] = useState(false);
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewTitle, setReviewTitle] = useState("");
  const [reviewBody, setReviewBody] = useState("");
  const [changeOpen, setChangeOpen] = useState(false);
  const [changeCheckin, setChangeCheckin] = useState("");
  const [changeCheckout, setChangeCheckout] = useState("");
  const [requestsOpen, setRequestsOpen] = useState(false);
  const [requestsText, setRequestsText] = useState("");
  const quoteQuery = useQuery({
    queryKey: ["cancellation-quote", id],
    queryFn: () => api.get(`/guest/bookings/${id}/cancellation-quote`).then((response) => response.data),
    enabled: Boolean(id) && cancelOpen,
  });
  const priceQuery = useQuery({
    queryKey: ["price-breakdown", id],
    queryFn: () => api.get(`/guest/bookings/${id}/price-breakdown`).then((response) => response.data),
    enabled: Boolean(id),
  });
  const requestsMutation = useMutation({
    mutationFn: () => api.patch(`/guest/bookings/${id}/requests`, { special_requests: requestsText }).then((response) => response.data),
    onSuccess: () => {
      toast("Пожелания сохранены", "success");
      setRequestsOpen(false);
      queryClient.invalidateQueries({ queryKey: ["guest-booking", id] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
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
  const reviewMutation = useMutation({
    mutationFn: () => api.post("/guest/reviews", {
      booking_id: Number(id),
      rating: reviewRating,
      title: reviewTitle || null,
      body: reviewBody,
    }).then((response) => response.data),
    onSuccess: () => {
      toast("Спасибо за отзыв! Он появится после модерации.", "success");
      setReviewOpen(false);
      setReviewTitle("");
      setReviewBody("");
      queryClient.invalidateQueries({ queryKey: ["guest-booking", id] });
      queryClient.invalidateQueries({ queryKey: ["guest-reviews"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const changeMutation = useMutation({
    mutationFn: () => api.post(`/guest/bookings/${id}/change`, {
      checkin_date: changeCheckin,
      checkout_date: changeCheckout,
    }).then((response) => response.data),
    onSuccess: () => {
      toast("Даты бронирования изменены", "success");
      setChangeOpen(false);
      queryClient.invalidateQueries({ queryKey: ["guest-booking", id] });
      queryClient.invalidateQueries({ queryKey: ["guest-bookings"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  if (query.isLoading) return <Spinner />;
  if (query.isError) return <ErrorState message={getErrorMessage(query.error)} />;
  const { booking, services, folio, review, timeline } = query.data;

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
            {booking.room_image && <img src={booking.room_image} alt={booking.room_type} loading="lazy" className="mt-3 h-36 w-full rounded-xl object-cover" />}
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
          {features.special_requests && (
            <Card>
              <div className="flex items-center justify-between gap-2">
                <h2 className="font-display text-2xl font-semibold">Особые пожелания</h2>
                <Button variant="ghost" size="sm" onClick={() => { setRequestsText(booking.special_requests ?? ""); setRequestsOpen(true); }}>Изменить</Button>
              </div>
              <p className="mt-3 text-sm text-muted">{booking.special_requests || "Пожелания не указаны."}</p>
            </Card>
          )}
          {priceQuery.data && (
            <Card>
              <h2 className="font-display text-2xl font-semibold">Детализация цены</h2>
              <div className="mt-4 space-y-2 text-sm text-muted">
                <div className="flex justify-between"><span>Проживание · {priceQuery.data.nights} ноч.</span><span>{formatMoney(priceQuery.data.room_total)}</span></div>
                {Number(priceQuery.data.promo_discount) > 0 && <div className="flex justify-between text-success"><span>Промокод</span><span>−{formatMoney(priceQuery.data.promo_discount)}</span></div>}
                {Number(priceQuery.data.loyalty_discount) > 0 && <div className="flex justify-between text-success"><span>Бонусные баллы</span><span>−{formatMoney(priceQuery.data.loyalty_discount)}</span></div>}
                {Number(priceQuery.data.services_total) > 0 && <div className="flex justify-between"><span>Услуги</span><span>{formatMoney(priceQuery.data.services_total)}</span></div>}
                <div className="divider" />
                <div className="flex justify-between text-base font-semibold text-ink"><span>Итого</span><span>{formatMoney(priceQuery.data.total)}</span></div>
              </div>
            </Card>
          )}
          <Card className="space-y-2">
            <Link to={`/me/services?booking=${booking.booking_id}`} className="btn-primary w-full">Заказать услугу</Link>
            <Button variant="secondary" className="w-full" onClick={() => downloadFile(api, `/guest/bookings/${booking.booking_id}/voucher.pdf`, `voucher-${booking.booking_id}.pdf`)}><Download size={15} /> Скачать ваучер</Button>
            <Button variant="secondary" className="w-full" onClick={() => navigate(`/checkout?room_id=${booking.room_id}&rate_id=${booking.rate_id}&checkin=${booking.checkin_date}&checkout=${booking.checkout_date}&price=${booking.price_per_night}&room_type=${encodeURIComponent(booking.room_type)}&room_number=${booking.room_number}&guests=${booking.adults + booking.children}`)}>Повторить бронирование</Button>
            {folio && <Button variant="secondary" className="w-full" onClick={() => downloadFile(api, `/guest/folios/${folio.folio_id}/pdf`, `folio-${folio.folio_id}.pdf`)}><Download size={15} /> Скачать счёт</Button>}
            {["NEW", "CONFIRMED"].includes(booking.status) && <Button variant="secondary" className="w-full" onClick={() => { setChangeCheckin(booking.checkin_date); setChangeCheckout(booking.checkout_date); setChangeOpen(true); }}>Изменить даты</Button>}
            {features.reviews && booking.status === "CHECKED_OUT" && !review && (
              <Button variant="secondary" className="w-full" onClick={() => setReviewOpen(true)}>
                <Star size={15} /> Оставить отзыв
              </Button>
            )}
            {review && (
              <p className="text-center text-xs text-muted">
                Отзыв: {review.status === "APPROVED" ? "опубликован" : review.status === "REJECTED" ? "отклонён" : "на модерации"}
              </p>
            )}
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
        {quoteQuery.data && (
          <div className="mb-4 rounded-xl bg-surface2 p-4 text-sm">
            <p className="font-semibold text-ink">Возврат: {formatMoney(quoteQuery.data.refund)} ({quoteQuery.data.percent}%)</p>
            <p className="mt-1 text-xs text-muted">Оплачено: {formatMoney(quoteQuery.data.paid)} · до заезда {quoteQuery.data.hours_left} ч.</p>
            <p className="mt-2 text-xs text-muted">До 2 дней — 100%, 24–48 ч — 50%, менее 24 ч — без возврата.</p>
          </div>
        )}
        <Select label="Причина" value={reasonId} onChange={(event) => setReasonId(event.target.value ? Number(event.target.value) : "")}>
          <option value="">Без причины</option>
          {(reasonsQuery.data ?? []).map((reason: any) => <option key={reason.reason_id} value={reason.reason_id}>{reason.name}</option>)}
        </Select>
      </Modal>
      <Modal
        open={requestsOpen}
        title="Особые пожелания"
        subtitle="Менеджер увидит их при подготовке к заезду."
        onClose={() => setRequestsOpen(false)}
        footer={<><Button variant="secondary" onClick={() => setRequestsOpen(false)}>Отмена</Button><Button onClick={() => requestsMutation.mutate()} disabled={requestsMutation.isPending}>Сохранить</Button></>}
      >
        <Textarea label="Пожелания" value={requestsText} onChange={(event) => setRequestsText(event.target.value)} placeholder="Ранний заезд, детская кроватка, аллергии, этаж…" rows={4} />
      </Modal>
      <Modal
        open={reviewOpen}
        title="Отзыв о проживании"
        subtitle={`${booking.room_type}, номер ${booking.room_number}`}
        onClose={() => setReviewOpen(false)}
        footer={<><Button variant="secondary" onClick={() => setReviewOpen(false)}>Отмена</Button><Button onClick={() => reviewMutation.mutate()} disabled={reviewMutation.isPending || reviewBody.trim().length < 10}>{reviewMutation.isPending ? "Отправляем…" : "Отправить отзыв"}</Button></>}
      >
        <div className="space-y-4">
          <div>
            <p className="label mb-2">Оценка</p>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5].map((value) => (
                <button key={value} type="button" onClick={() => setReviewRating(value)} className="rounded-lg p-1" aria-label={`${value} из 5`}>
                  <Star size={26} className={value <= reviewRating ? "fill-amber text-amber" : "text-muted/40"} />
                </button>
              ))}
            </div>
          </div>
          <Input label="Заголовок" value={reviewTitle} onChange={(event) => setReviewTitle(event.target.value)} placeholder="Коротко о главном" />
          <Textarea label="Отзыв" value={reviewBody} onChange={(event) => setReviewBody(event.target.value)} placeholder="Расскажите, что понравилось, а что можно улучшить" rows={5} />
          <p className="text-xs text-muted">Отзыв появится на сайте после проверки менеджером.</p>
        </div>
      </Modal>
      <Modal
        open={changeOpen}
        title="Изменить даты"
        subtitle="Перенос дат возможен для новой или подтверждённой брони."
        onClose={() => setChangeOpen(false)}
        footer={<><Button variant="secondary" onClick={() => setChangeOpen(false)}>Отмена</Button><Button onClick={() => changeMutation.mutate()} disabled={changeMutation.isPending || !changeCheckin || !changeCheckout}>{changeMutation.isPending ? "Сохраняем…" : "Сохранить даты"}</Button></>}
      >
        <div className="grid gap-4 md:grid-cols-2">
          <Input label="Заезд" type="date" value={changeCheckin} onChange={(event) => setChangeCheckin(event.target.value)} />
          <Input label="Выезд" type="date" value={changeCheckout} onChange={(event) => setChangeCheckout(event.target.value)} />
        </div>
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
                {service.image_url && <img src={service.image_url} alt={service.name} loading="lazy" className="mb-3 h-28 w-full rounded-xl object-cover" />}
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
  const [passwordForm, setPasswordForm] = useState({ old_password: "", new_password: "" });
  const saveMutation = useMutation({
    mutationFn: () => updateSettings(form),
    onSuccess: () => {
      toast("Настройки сохранены", "success");
      setLang(form.language);
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const passwordMutation = useMutation({
    mutationFn: () => api.post("/auth/change-password", passwordForm),
    onSuccess: () => {
      toast("Пароль изменён. Остальные сессии завершены.", "success");
      setPasswordForm({ old_password: "", new_password: "" });
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
        <Card className="space-y-4 lg:col-span-2">
          <h2 className="font-display text-2xl font-semibold">Безопасность</h2>
          <p className="text-sm text-muted">После смены пароля остальные активные сессии будут завершены.</p>
          <div className="grid gap-4 md:grid-cols-2">
            <Input label="Текущий пароль" type="password" value={passwordForm.old_password} onChange={(event) => setPasswordForm({ ...passwordForm, old_password: event.target.value })} placeholder="••••••••" />
            <Input label="Новый пароль" type="password" value={passwordForm.new_password} onChange={(event) => setPasswordForm({ ...passwordForm, new_password: event.target.value })} placeholder="Минимум 8 символов" />
          </div>
          <Button onClick={() => passwordMutation.mutate()} disabled={passwordMutation.isPending || !passwordForm.old_password || passwordForm.new_password.length < 8}>
            {passwordMutation.isPending ? "Сохраняем…" : "Сменить пароль"}
          </Button>
        </Card>
      </div>
    </div>
  );
}
export function GuestLoyaltyPage() {
  const query = useQuery({
    queryKey: ["guest-loyalty"],
    queryFn: () => api.get("/guest/loyalty").then((response) => response.data),
  });
  if (query.isLoading) return <Spinner />;
  if (query.isError) return <ErrorState message={getErrorMessage(query.error)} />;
  const data = query.data;
  return (
    <GuestPage>
      <PageHeader title="Бонусные баллы" subtitle="Программа лояльности SunStay." />
      <div className="grid gap-5 lg:grid-cols-[1fr_1.5fr]">
        <Card>
          <p className="label">Доступно баллов</p>
          <p className="mt-3 font-display text-5xl font-semibold text-terracotta">{data.points_balance}</p>
          <div className="mt-5 space-y-2 text-sm text-muted">
            <p>Начисляется 5% от оплаченного проживания после выезда.</p>
            <p>1 балл = 1 ₽. Можно списать до 30% стоимости новой брони при оплате онлайн.</p>
          </div>
        </Card>
        <Card>
          <h2 className="font-display text-2xl font-semibold">История операций</h2>
          {(data.transactions ?? []).length ? (
            <div className="mt-4 space-y-2">
              {data.transactions.map((tx: any) => (
                <div key={tx.transaction_id} className="flex items-center justify-between gap-3 rounded-xl border border-line px-4 py-3 text-sm">
                  <div>
                    <p className="font-semibold text-ink">{tx.description}</p>
                    <p className="text-xs text-muted">{formatDateTime(tx.created_at)}</p>
                  </div>
                  <span className={`font-semibold ${tx.transaction_type === "EARN" ? "text-success" : "text-danger"}`}>
                    {tx.transaction_type === "EARN" ? "+" : "−"}{tx.points}
                  </span>
                </div>
              ))}
            </div>
          ) : <EmptyState title="Операций пока нет" description="Баллы появятся после первого выезда." />}
        </Card>
      </div>
    </GuestPage>
  );
}
