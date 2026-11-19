import {
  ArrowRight,
  BadgeCheck,
  CalendarDays,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Coffee,
  CreditCard,
  Lock,
  Mail,
  MapPin,
  MessageSquare,
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
import { useMemo, useRef, useState } from "react";
import { Link, Navigate, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api, getErrorMessage } from "../lib/api";
import { useAuth } from "../lib/auth";
import { useI18n } from "../lib/i18n";
import { useCurrency } from "../lib/currency";
import { useFeatures } from "../lib/features";
import { addDaysISO, formatDate, nightsBetween, todayISO } from "../lib/utils";
import { Button, Card, ErrorState, Input, Select, Spinner, StatusPill, Textarea, useToast } from "../components/ui";
import { homeForRole } from "../components/Layout";

const FALLBACK_ROOM_TYPES = [
  { room_type_id: 1, name: "Стандарт", capacity: 2, min_price: 4800, description: "Уютный номер с одной кроватью или двумя раздельными." },
  { room_type_id: 2, name: "Комфорт", capacity: 2, min_price: 6400, description: "Номер повышенной комфортности с видом на город." },
  { room_type_id: 3, name: "Люкс", capacity: 4, min_price: 9900, description: "Просторный номер с гостиной зоной." },
];

function RoomArt({ index = 0, className = "", imageUrl }: { index?: number; className?: string; imageUrl?: string | null }) {
  if (imageUrl) {
    return (
      <div className={`relative overflow-hidden rounded-2xl bg-surface2 ${className}`}>
        <img src={imageUrl} alt="Номер SunStay" loading="lazy" className="h-full w-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-t from-black/25 via-transparent to-transparent" />
      </div>
    );
  }
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

function ReviewStars({ rating }: { rating: number }) {
  return (
    <div className="flex gap-0.5 text-amber">
      {[1, 2, 3, 4, 5].map((value) => (
        <Star key={value} size={14} className={value <= rating ? "fill-current" : "opacity-25"} />
      ))}
    </div>
  );
}

function AvailabilityCalendar({ onSelect }: { onSelect: (checkin: string, checkout: string) => void }) {
  const { format } = useCurrency();
  const { lang } = useI18n();
  const en = lang === "en";
  const [month, setMonth] = useState(todayISO().slice(0, 7));
  const query = useQuery({
    queryKey: ["public-calendar", month],
    queryFn: () => api.get("/public/calendar", { params: { month } }).then((response) => response.data),
  });
  const days = query.data?.days ?? [];
  const first = new Date(`${month}-01T12:00:00`);
  const offset = (first.getDay() + 6) % 7;
  const cells: Array<any | null> = [...Array(offset).fill(null), ...days];
  const monthTitle = new Intl.DateTimeFormat(en ? "en-US" : "ru-RU", { month: "long", year: "numeric" }).format(first);

  function changeMonth(delta: number) {
    const date = new Date(`${month}-01T12:00:00`);
    date.setMonth(date.getMonth() + delta);
    setMonth(date.toISOString().slice(0, 7));
  }

  return (
    <Card className="overflow-hidden">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="label text-terracotta">{en ? "Availability calendar" : "Календарь доступности"}</p>
          <h3 className="mt-1 font-display text-2xl font-semibold capitalize text-ink">{monthTitle}</h3>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={() => changeMonth(-1)} aria-label="Предыдущий месяц"><ChevronLeft size={16} /></Button>
          <Button variant="secondary" size="sm" onClick={() => changeMonth(1)} aria-label="Следующий месяц"><ChevronRight size={16} /></Button>
        </div>
      </div>
      <div className="mt-5 grid grid-cols-7 gap-1 text-center text-[11px] font-semibold uppercase tracking-wide text-muted">
        {(en ? ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"] : ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]).map((day) => <span key={day} className="py-1">{day}</span>)}
      </div>
      <div className="mt-1 grid grid-cols-7 gap-1">
        {cells.map((day, index) => {
          if (!day) return <div key={`empty-${index}`} className="min-h-16 rounded-xl bg-surface2/40" />;
          const disabled = day.is_past || day.available_rooms === 0;
          return (
            <button
              key={day.day}
              disabled={disabled}
              onClick={() => onSelect(day.day, addDaysISO(day.day, 1))}
              className={`min-h-16 rounded-xl border p-1.5 text-left transition ${
                disabled
                  ? "cursor-not-allowed border-line/50 bg-surface2/50 text-muted/50"
                  : "border-line bg-surface hover:border-terracotta hover:bg-terracotta/8"
              }`}
              title={disabled ? (en ? "No rooms available" : "Нет свободных номеров") : (en ? "Select this date" : "Выбрать эту дату")}
            >
              <span className="text-xs font-bold">{Number(day.day.slice(-2))}</span>
              {!disabled && (
                <>
                  <span className="mt-1 block text-[10px] font-semibold text-ink">{format(day.min_price)}</span>
                  <span className="block text-[9px] text-muted">{day.available_rooms} {en ? "free" : "св."}</span>
                </>
              )}
            </button>
          );
        })}
      </div>
      {query.isLoading && <div className="mt-3"><Spinner /></div>}
    </Card>
  );
}

function WaitlistForm({ checkin, checkout, guests, roomTypeId }: { checkin: string; checkout: string; guests: number; roomTypeId: string }) {
  const { toast } = useToast();
  const [form, setForm] = useState({ full_name: "", email: "", phone: "", note: "" });
  const mutation = useMutation({
    mutationFn: () => api.post("/public/waitlist", {
      full_name: form.full_name,
      email: form.email || null,
      phone: form.phone || null,
      room_type_id: roomTypeId ? Number(roomTypeId) : null,
      checkin_date: checkin,
      checkout_date: checkout,
      adults: guests,
      children: 0,
      note: form.note || null,
    }).then((response) => response.data),
    onSuccess: () => {
      toast("Заявка в лист ожидания создана. Мы свяжемся с вами.", "success");
      setForm({ full_name: "", email: "", phone: "", note: "" });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  return (
    <Card className="space-y-4">
      <div>
        <p className="label text-terracotta">Нет свободных номеров?</p>
        <h3 className="mt-1 font-display text-2xl font-semibold text-ink">Встать в лист ожидания</h3>
        <p className="mt-1 text-sm text-muted">Оставьте контакты — менеджер свяжется, если номер освободится на {formatDate(checkin)} — {formatDate(checkout)}.</p>
      </div>
      <div className="grid gap-3 md:grid-cols-2">
        <Input label="ФИО" value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} placeholder="Иванов Иван" />
        <Input label="Телефон" value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} placeholder="+7 900 111-22-33" />
        <Input label="Email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} placeholder="guest@example.com" />
        <Input label="Комментарий" value={form.note} onChange={(event) => setForm({ ...form, note: event.target.value })} placeholder="Пожелания по номеру" />
      </div>
      <Button onClick={() => mutation.mutate()} disabled={mutation.isPending || form.full_name.trim().length < 3}>
        <MessageSquare size={15} /> {mutation.isPending ? "Отправляем…" : "Оставить заявку"}
      </Button>
    </Card>
  );
}

export function LandingPage() {
  const navigate = useNavigate();
  const { lang } = useI18n();
  const en = lang === "en";
  const { format } = useCurrency();
  const features = useFeatures();
  const { data } = useQuery({
    queryKey: ["public-room-types"],
    queryFn: () => api.get("/public/room-types").then((response) => response.data),
  });
  const reviewsQuery = useQuery({
    queryKey: ["public-reviews"],
    queryFn: () => api.get("/public/reviews", { params: { limit: 3 } }).then((response) => response.data),
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
              <Star size={13} /> {en ? "Boutique hotel in the heart of St. Petersburg" : "Бутик-отель в центре Петербурга"}
            </span>
            <h1 className="mt-5 max-w-2xl font-display text-5xl font-semibold leading-[1.05] tracking-tight text-ink md:text-6xl">
              {en ? "A hotel you want to return to" : "Отель, в который хочется вернуться"}
            </h1>
            <p className="mt-5 max-w-xl text-base leading-7 text-muted">
              {en
                ? "48 rooms, a quiet courtyard and attentive service. Book direct — no hidden fees or extra calls."
                : "48 номеров, тихий внутренний двор и внимательный сервис. Бронируйте напрямую — без скрытых комиссий и лишних звонков."}
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Button onClick={submitSearch}>
                <Search size={17} /> {en ? "Find a room" : "Найти номер"}
              </Button>
              <Link to="/login" className="btn-secondary">
                {en ? "Sign in" : "Войти в кабинет"}
              </Link>
            </div>
            <div className="mt-8 flex flex-wrap gap-6 text-sm text-muted">
              <span className="flex items-center gap-2"><ShieldCheck size={16} className="text-success" /> {en ? "Secure payment" : "Безопасная оплата"}</span>
              <span className="flex items-center gap-2"><BadgeCheck size={16} className="text-success" /> {en ? "Instant confirmation" : "Подтверждение сразу"}</span>
              <span className="flex items-center gap-2"><MapPin size={16} className="text-terracotta" /> {en ? "Moika Embankment, 12" : "Набережная Мойки, 12"}</span>
            </div>
          </div>
          <div className="relative">
            <RoomArt index={0} imageUrl={roomTypes[0]?.image_url} className="h-[360px] shadow-float md:h-[440px]" />
            <Card className="mt-4">
              <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
                <label className="col-span-1 flex flex-col gap-1.5">
                  <span className="label">{en ? "Check-in" : "Заезд"}</span>
                  <input type="date" value={checkin} onChange={(event) => setCheckin(event.target.value)} className="input" />
                </label>
                <label className="col-span-1 flex flex-col gap-1.5">
                  <span className="label">{en ? "Check-out" : "Выезд"}</span>
                  <input type="date" value={checkout} onChange={(event) => setCheckout(event.target.value)} className="input" />
                </label>
                <label className="col-span-1 flex flex-col gap-1.5">
                  <span className="label">{en ? "Guests" : "Гости"}</span>
                  <select value={guests} onChange={(event) => setGuests(Number(event.target.value))} className="input">
                    {[1, 2, 3, 4].map((value) => <option key={value} value={value}>{en ? `${value} guests` : `${value} гостя`}</option>)}
                  </select>
                </label>
                <div className="col-span-1 flex items-end">
                  <Button className="w-full" onClick={submitSearch}>{en ? "Search" : "Найти"}</Button>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </section>

      <section className="mx-auto grid max-w-[1240px] gap-6 px-4 pt-20 md:grid-cols-[1.3fr_0.7fr] md:px-6">
        <AvailabilityCalendar
          onSelect={(nextCheckin, nextCheckout) => {
            setCheckin(nextCheckin);
            setCheckout(nextCheckout);
            navigate(`/search?checkin=${nextCheckin}&checkout=${nextCheckout}&guests=${guests}`);
          }}
        />
        <div className="flex flex-col justify-center rounded-3xl bg-forest p-7 text-white">
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-amber">Планируйте заранее</p>
          <h2 className="mt-3 font-display text-3xl font-semibold">Свободные даты — как на ладони</h2>
          <p className="mt-3 text-sm leading-6 text-white/70">
            Календарь показывает минимальную цену и количество свободных номеров. Нажмите на дату, чтобы сразу перейти к выбору номера.
          </p>
          <div className="mt-6 grid grid-cols-2 gap-3 text-sm">
            <div className="rounded-2xl border border-white/15 bg-white/10 p-4">
              <p className="text-2xl font-semibold text-amber">24/7</p>
              <p className="mt-1 text-xs text-white/65">онлайн-бронирование</p>
            </div>
            <div className="rounded-2xl border border-white/15 bg-white/10 p-4">
              <p className="text-2xl font-semibold text-amber">−15%</p>
              <p className="mt-1 text-xs text-white/65">раннее бронирование</p>
            </div>
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
              <RoomArt index={index} imageUrl={room.image_url} className="h-48 rounded-none" />
              <div className="p-5">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="font-display text-2xl font-semibold text-ink">{room.name}</h3>
                    <p className="mt-1 text-xs text-muted">до {room.capacity} гостей · {room.rooms_count ?? "—"} номеров</p>
                  </div>
                  <div className="text-right">
                    <p className="text-[11px] uppercase tracking-wide text-muted">от</p>
                    <p className="font-display text-xl font-semibold text-ink">{format(room.min_price)}</p>
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

      {features.reviews && (
      <section className="mx-auto max-w-[1240px] px-4 pb-20 md:px-6">
        <div className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="label text-terracotta">{en ? "Guest reviews" : "Отзывы гостей"}</p>
            <h2 className="mt-2 font-display text-3xl font-semibold text-ink">{en ? "What guests say after their stay" : "Что говорят после проживания"}</h2>
          </div>
          <p className="max-w-md text-sm leading-6 text-muted">{en ? "You can leave a review after check-out. All reviews are moderated." : "Отзыв можно оставить в личном кабинете после выезда. Все отзывы проходят модерацию."}</p>
        </div>
        <div className="mt-8 grid gap-5 md:grid-cols-3">
          {(reviewsQuery.data ?? []).map((review: any) => (
            <Card key={review.review_id} className="flex flex-col">
              <div className="flex items-center justify-between gap-3">
                <ReviewStars rating={Number(review.rating)} />
                <span className="badge bg-surface2 text-muted">{review.room_type}</span>
              </div>
              <h3 className="mt-4 font-display text-xl font-semibold text-ink">{review.title || "Отзыв гостя"}</h3>
              <p className="mt-2 flex-1 text-sm leading-6 text-muted">{review.body}</p>
              <p className="mt-4 text-xs font-semibold text-ink">{review.guest_name}</p>
            </Card>
          ))}
        </div>
      </section>
      )}
    </div>
  );
}

export function SearchPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { format } = useCurrency();
  const features = useFeatures();
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
      image: roomType.image_url || "",
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
            <span className="label">Цена до {format(maxPrice)}</span>
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
            <>
              <Card className="py-10 text-center text-sm text-muted">На выбранные даты нет доступных номеров. Попробуйте изменить фильтры или встаньте в лист ожидания.</Card>
              {features.waitlist && <WaitlistForm checkin={checkin} checkout={checkout} guests={guests} roomTypeId={roomTypeId} />}
            </>
          )}
          {results.map((roomType: any, index: number) => (
            <Card key={roomType.room_type_id} className="overflow-hidden p-0">
              <div className="grid md:grid-cols-[220px_1fr]">
                <RoomArt index={index} imageUrl={roomType.image_url} className="h-44 rounded-none md:h-full" />
                <div className="p-5">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div>
                      <h2 className="font-display text-2xl font-semibold text-ink">{roomType.name}</h2>
                      <p className="mt-1 text-xs text-muted">до {roomType.capacity} гостей · свободно {roomType.available_rooms}</p>
                    </div>
                    <div className="text-right">
                      <p className="font-display text-2xl font-semibold text-ink">{format(roomType.price_per_night)}</p>
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
                    <p className="text-sm text-muted">Итого за {nights} ночей: <span className="font-semibold text-ink">{format(Number(roomType.price_per_night) * nights)}</span></p>
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
  const { format } = useCurrency();
  const features = useFeatures();
  const { toast } = useToast();
  const roomId = Number(params.get("room_id") || 0);
  const rateId = Number(params.get("rate_id") || 0);
  const checkin = params.get("checkin") || addDaysISO(todayISO(), 7);
  const checkout = params.get("checkout") || addDaysISO(todayISO(), 10);
  const price = Number(params.get("price") || 0);
  const roomType = params.get("room_type") || "Номер";
  const roomNumber = params.get("room_number") || "";
  const roomImage = params.get("image") || "";
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
    special_requests: "",
  });
  const [promo, setPromo] = useState("");
  const [discount, setDiscount] = useState(0);
  const [promoError, setPromoError] = useState("");
  const [pointsToUse, setPointsToUse] = useState(0);
  const loyaltyQuery = useQuery({
    queryKey: ["guest-loyalty"],
    queryFn: () => api.get("/guest/loyalty").then((response) => response.data),
    enabled: user?.role_code === "GUEST",
  });
  const rawTotal = price * nights * (1 - discount / 100);
  const balance = Number(loyaltyQuery.data?.points_balance ?? 0);
  const appliedPoints = Math.min(pointsToUse, balance, Math.floor(rawTotal * 0.3));
  const total = rawTotal - appliedPoints;

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

  const idempotencyKey = useRef(crypto.randomUUID());
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
      points_to_use: appliedPoints,
    }, { headers: { "Idempotency-Key": idempotencyKey.current } }).then((response) => response.data),
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
          {features.special_requests && <Textarea label="Особые пожелания" value={form.special_requests} onChange={(event) => setForm({ ...form, special_requests: event.target.value })} placeholder="Ранний заезд, детская кроватка, аллергии, этаж…" rows={3} />}
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
          <RoomArt index={1} imageUrl={roomImage} className="h-40" />
          <div>
            <h2 className="font-display text-2xl font-semibold text-ink">{roomType}</h2>
            <p className="text-sm text-muted">Номер {roomNumber} · {nights} ночей</p>
          </div>
          <div className="space-y-2 text-sm text-muted">
            <div className="flex justify-between"><span>{formatDate(checkin)} — {formatDate(checkout)}</span><span>{nights} ночей</span></div>
            <div className="flex justify-between"><span>{format(price)} × {nights}</span><span>{format(price * nights)}</span></div>
            {discount > 0 && <div className="flex justify-between text-success"><span>Скидка {discount}%</span><span>−{format(price * nights * discount / 100)}</span></div>}
            {appliedPoints > 0 && <div className="flex justify-between text-success"><span>Бонусные баллы</span><span>−{format(appliedPoints)}</span></div>}
            <div className="divider" />
            <div className="flex justify-between text-base font-semibold text-ink"><span>Итого</span><span>{format(total)}</span></div>
          </div>
          <div className="flex gap-2">
            <input value={promo} onChange={(event) => setPromo(event.target.value)} placeholder="Промокод" className="input" />
            <Button variant="secondary" onClick={() => promoMutation.mutate()} disabled={!promo || promoMutation.isPending}>Применить</Button>
          </div>
          {promoError && <p className="text-xs text-danger">{promoError}</p>}
          {user?.role_code === "GUEST" && (
            <div className="rounded-xl bg-surface2 p-3 text-sm">
              <p className="flex items-center justify-between text-muted">
                <span>Списать бонусные баллы</span>
                <span className="font-semibold text-ink">доступно {balance}</span>
              </p>
              <input type="number" min={0} max={balance} value={pointsToUse} onChange={(event) => setPointsToUse(Math.max(0, Number(event.target.value)))} className="input mt-2" placeholder="0" />
              <p className="mt-1 text-xs text-muted">Списывается не более 30% стоимости. 1 балл = 1 ₽.</p>
            </div>
          )}
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
  const { user, login, verify2fa, register } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  const [tab, setTab] = useState<"login" | "register">("login");
  const [loginForm, setLoginForm] = useState({ email: "", password: "" });
  const [twofaToken, setTwofaToken] = useState("");
  const [twofaCode, setTwofaCode] = useState("");
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
    onSuccess: (result) => {
      if (result.requires_2fa) {
        setTwofaToken(result.twofa_token ?? "");
        return;
      }
      if (result.user) navigate(homeForRole(result.user));
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const demoLoginMutation = useMutation({
    mutationFn: (account: { email: string; password: string }) => login(account.email, account.password),
    onSuccess: (result) => {
      if (result.requires_2fa) {
        setTwofaToken(result.twofa_token ?? "");
        return;
      }
      if (result.user) navigate(homeForRole(result.user));
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const verifyMutation = useMutation({
    mutationFn: () => verify2fa(twofaToken, twofaCode),
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
            twofaToken ? (
              <form className="mt-5 space-y-4" onSubmit={(event) => { event.preventDefault(); verifyMutation.mutate(); }}>
                <p className="text-sm text-muted">Введите 6-значный код из приложения-аутентификатора.</p>
                <Input label="Код 2FA" value={twofaCode} onChange={(event) => setTwofaCode(event.target.value)} placeholder="123456" />
                <Button type="submit" className="w-full" disabled={verifyMutation.isPending}>{verifyMutation.isPending ? "Проверяем…" : "Подтвердить"}</Button>
                <Button type="button" variant="ghost" className="w-full" onClick={() => { setTwofaToken(""); setTwofaCode(""); }}>Назад</Button>
                {verifyMutation.isError && <ErrorState message={getErrorMessage(verifyMutation.error)} />}
              </form>
            ) : (
              <form className="mt-5 space-y-4" onSubmit={(event) => { event.preventDefault(); loginMutation.mutate(); }}>
                <Input label="Email" type="email" value={loginForm.email} onChange={(event) => setLoginForm({ ...loginForm, email: event.target.value })} placeholder="you@example.com" />
                <Input label="Пароль" type="password" value={loginForm.password} onChange={(event) => setLoginForm({ ...loginForm, password: event.target.value })} placeholder="••••••••" />
                <Button type="submit" className="w-full" disabled={loginMutation.isPending}>{loginMutation.isPending ? "Входим…" : "Войти"}</Button>
                {loginMutation.isError && <ErrorState message={getErrorMessage(loginMutation.error)} />}
              </form>
            )
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
