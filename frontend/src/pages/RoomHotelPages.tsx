import { useState } from "react";
import { ArrowRight, Star } from "lucide-react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, getErrorMessage } from "../lib/api";
import { useAuth } from "../lib/auth";
import { useCurrency } from "../lib/currency";
import { useFeatures } from "../lib/features";
import { addDaysISO, formatDate, resolveImage, roomImageByName, todayISO } from "../lib/utils";
import { Button, Card, ErrorState, Input, PageHeader, Select, Spinner, Textarea, useToast } from "../components/ui";

function ReviewStars({ rating }: { rating: number }) {
  return (
    <div className="flex gap-0.5 text-amber">
      {[1, 2, 3, 4, 5].map((value) => <Star key={value} size={14} className={value <= rating ? "fill-current" : "opacity-25"} />)}
    </div>
  );
}

const FALLBACK = [
  { name: "Стандарт", image_url: "images/spb/standard-classic-1.jpg", min_price: 4000 },
  { name: "Комфорт", image_url: "images/spb/comfort-city-1.jpg", min_price: 5600 },
  { name: "Люкс", image_url: "images/spb/lux-president-1.jpg", min_price: 9200 },
];

export function RoomPage() {
  const { id } = useParams();
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { toast } = useToast();
  const { format } = useCurrency();
  const features = useFeatures();
  const [guests, setGuests] = useState(2);
  const query = useQuery({
    queryKey: ["public-room", id],
    queryFn: () => api.get(`/public/rooms/${id}`).then((response) => response.data),
    enabled: Boolean(id),
  });
  const roomTypesQuery = useQuery({
    queryKey: ["public-room-types"],
    queryFn: () => api.get("/public/room-types").then((response) => response.data),
  });
  const fallbackRoom = {
    room_id: Number(id),
    room_number: params.get("room_number") || "",
    room_type: params.get("room_type") || "Стандарт",
    floor: null,
    capacity: Number(params.get("guests") || 2),
    description: params.get("description") || "",
    variant_name: params.get("variant") || "",
    image_url: params.get("image") || "",
    price_per_night: Number(params.get("price") || 0),
    rate_id: Number(params.get("rate_id") || 1),
    amenities: [],
    reviews: [],
  };
  const hasParams = Boolean(params.get("room_number"));
  const room = query.data ?? (hasParams ? fallbackRoom : null);
  if (!room) return <div className="mx-auto max-w-6xl px-4 py-16"><Spinner /></div>;
  const gallery = Array.from(new Set([
    room.image_url,
    roomImageByName(room.room_type),
    ...(roomTypesQuery.data ?? FALLBACK).map((item: any) => item.image_url),
  ].filter(Boolean))).slice(0, 5);
  const capacity = Number(room.capacity || 2);
  const goCheckout = () => {
    const next = new URLSearchParams({
      room_id: String(room.room_id),
      rate_id: String(room.rate_id || 1),
      checkin: addDaysISO(todayISO(), 7),
      checkout: addDaysISO(todayISO(), 10),
      price: String(room.price_per_night || 0),
      room_type: room.room_type,
      room_number: room.room_number,
      guests: String(guests),
      capacity: String(capacity),
      image: room.image_url || "",
    });
    const target = `/checkout?${next.toString()}`;
    if (!user) { navigate("/login", { state: { from: target } }); return; }
    navigate(target);
  };
  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-10 md:px-6">
      <Link to="/search" className="btn-ghost">← Назад к поиску</Link>
      <PageHeader title={`${room.room_type} · номер ${room.room_number}`} subtitle={`${room.variant_name || "Номер"} · этаж ${room.floor ?? "—"} · до ${capacity} гостей`} />
      <div className="grid gap-2 md:grid-cols-4">
        {gallery.map((src, index) => <img key={src + index} src={resolveImage(src)} alt={`${room.room_type} ${index + 1}`} className="h-52 w-full rounded-2xl object-cover" />)}
      </div>
      <Card className="space-y-4">
        <h2 className="font-display text-3xl font-semibold">{room.variant_name || room.room_type}</h2>
        <p className="text-sm leading-7 text-muted">{room.description || room.room_type_description}</p>
        <div className="flex flex-wrap gap-2">{(room.amenities ?? []).map((amenity: string) => <span key={amenity} className="badge bg-surface2 text-muted">{amenity}</span>)}</div>
        <div className="flex flex-wrap items-center justify-between gap-4 border-t border-line pt-4">
          <div><p className="font-display text-3xl font-semibold">{format(room.price_per_night)}</p><p className="text-xs text-muted">за ночь</p></div>
          <div className="flex items-center gap-3">
            <Select label="Гостей" value={guests} onChange={(event) => setGuests(Number(event.target.value))}>
              {Array.from({ length: capacity }, (_, i) => i + 1).map((value) => <option key={value} value={value}>{value}</option>)}
            </Select>
            <Button className="mt-6" onClick={goCheckout}>Выбрать <ArrowRight size={15} /></Button>
          </div>
        </div>
      </Card>
      <div className="grid gap-5 lg:grid-cols-[1.4fr_1fr]">
        <Card>
          <h2 className="font-display text-2xl font-semibold">Отзывы</h2>
          {!features.reviews ? (
            <p className="mt-3 rounded-xl bg-surface2 p-4 text-sm text-muted">Отзывы временно недоступны.</p>
          ) : (room.reviews ?? []).length ? (
            <div className="mt-4 space-y-3">
              {room.reviews.map((review: any) => (
                <div key={review.review_id} className="rounded-xl border border-line p-4">
                  <div className="flex items-center justify-between gap-3"><ReviewStars rating={Number(review.rating)} /><span className="text-xs text-muted">{formatDate(review.created_at)}</span></div>
                  <h3 className="mt-2 font-semibold">{review.title || "Отзыв"}</h3>
                  <p className="mt-1 text-sm text-muted">{review.body}</p>
                  <p className="mt-2 text-xs text-muted">{review.guest_name}</p>
                </div>
              ))}
            </div>
          ) : <p className="mt-3 text-sm text-muted">Отзывов пока нет.</p>}
        </Card>
        <Card>
          <h2 className="font-display text-2xl font-semibold">Другие предложения</h2>
          <div className="mt-4 space-y-2">
            {(roomTypesQuery.data ?? FALLBACK).filter((item: any) => item.name !== room.room_type && item.room_type_id !== room.room_type_id).map((item: any, index: number) => (
              <Link key={index} to="/search" className="flex items-center gap-3 rounded-xl border border-line p-2 hover:bg-surface2">
                <img src={resolveImage(item.image_url || roomImageByName(item.name))} alt={item.name} className="h-14 w-20 rounded-lg object-cover" />
                <div><p className="text-sm font-semibold">{item.name}</p><p className="text-xs text-muted">от {format(item.min_price)}</p></div>
              </Link>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

export function HotelPage() {
  const features = useFeatures();
  const ratingQuery = useQuery({
    queryKey: ["public-rating"],
    queryFn: () => api.get("/public/rating").then((response) => response.data),
  });
  const reviewsQuery = useQuery({
    queryKey: ["public-reviews"],
    queryFn: () => api.get("/public/reviews", { params: { limit: 12 } }).then((response) => response.data),
  });
  const roomTypesQuery = useQuery({
    queryKey: ["public-room-types"],
    queryFn: () => api.get("/public/room-types").then((response) => response.data),
  });
  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-10 md:px-6">
      <PageHeader title="SunStay" subtitle="Бутик-отель в центре Санкт-Петербурга · набережная Мойки, 12" />
      {ratingQuery.data && Number(ratingQuery.data.total) > 0 && (
        <Card className="flex flex-wrap items-center gap-6">
          <div className="text-center">
            <p className="font-display text-5xl font-semibold text-ink">{Number(ratingQuery.data.average).toFixed(1)}</p>
            <div className="mt-1 flex justify-center gap-0.5 text-amber">
              {[1, 2, 3, 4, 5].map((value) => <Star key={value} size={18} className={value <= Math.round(Number(ratingQuery.data.average)) ? "fill-current" : "opacity-25"} />)}
            </div>
            <p className="mt-1 text-xs text-muted">{ratingQuery.data.total} отзывов</p>
          </div>
          <div className="min-w-[220px] flex-1 space-y-1">
            {[5, 4, 3, 2, 1].map((value) => {
              const count = Number(ratingQuery.data[`stars_${value}`] || 0);
              const total = Number(ratingQuery.data.total || 1);
              return (
                <div key={value} className="flex items-center gap-2 text-xs text-muted">
                  <span className="w-3">{value}</span>
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-surface2">
                    <div className="h-full rounded-full bg-amber" style={{ width: `${Math.round((count / total) * 100)}%` }} />
                  </div>
                  <span className="w-6 text-right">{count}</span>
                </div>
              );
            })}
          </div>
        </Card>
      )}
      <div className="grid gap-2 md:grid-cols-4">
        {(roomTypesQuery.data ?? FALLBACK).map((room: any, index: number) => (
          <img key={index} src={resolveImage(room.image_url || roomImageByName(room.name))} alt={room.name} className="h-52 w-full rounded-2xl object-cover" />
        ))}
      </div>
      <Card>
        <h2 className="font-display text-2xl font-semibold">Об отеле</h2>
        <p className="mt-3 text-sm leading-7 text-muted">48 номеров, тихий внутренний двор и внимательный сервис. Бронируйте напрямую — без скрытых комиссий и лишних звонков.</p>
        <div className="mt-4 flex flex-wrap gap-2"><span className="badge bg-surface2 text-muted">Wi-Fi</span><span className="badge bg-surface2 text-muted">Завтрак</span><span className="badge bg-surface2 text-muted">Парковка</span></div>
        <Link to="/search" className="btn-primary mt-5">Посмотреть номера <ArrowRight size={15} /></Link>
      </Card>
      <div className="grid gap-5 lg:grid-cols-[1.4fr_1fr]">
        <Card>
          <h2 className="font-display text-2xl font-semibold">Отзывы гостей</h2>
          {!features.reviews ? (
            <p className="mt-3 rounded-xl bg-surface2 p-4 text-sm text-muted">Отзывы временно недоступны.</p>
          ) : (reviewsQuery.data ?? []).length ? (
            <div className="mt-4 space-y-3">
              {(reviewsQuery.data ?? []).map((review: any) => (
                <div key={review.review_id} className="rounded-xl border border-line p-4">
                  <div className="flex items-center justify-between gap-3"><ReviewStars rating={Number(review.rating)} /><span className="text-xs text-muted">{formatDate(review.created_at)}</span></div>
                  <h3 className="mt-2 font-semibold">{review.title || "Отзыв"}</h3>
                  <p className="mt-1 text-sm text-muted">{review.body}</p>
                  <p className="mt-2 text-xs text-muted">{review.guest_name}{review.room_type ? ` · ${review.room_type}` : ""}</p>
                </div>
              ))}
            </div>
          ) : <p className="mt-3 text-sm text-muted">Отзывов пока нет.</p>}
        </Card>
        <Card className="space-y-3">
          <h2 className="font-display text-2xl font-semibold">Оставить отзыв</h2>
          <HotelReviewForm />
        </Card>
      </div>
    </div>
  );
}

export function HotelReviewForm() {
  const { user } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const features = useFeatures();
  const [rating, setRating] = useState(5);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const mutation = useMutation({
    mutationFn: () => api.post("/public/hotel-reviews", { rating, title: title || null, body }).then((response) => response.data),
    onSuccess: () => {
      toast("Спасибо! Отзыв опубликован.", "success");
      setTitle(""); setBody(""); setRating(5);
      queryClient.invalidateQueries({ queryKey: ["public-reviews"] });
      queryClient.invalidateQueries({ queryKey: ["public-rating"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  if (!features.reviews) return <p className="text-sm text-muted">Отзывы временно недоступны.</p>;
  if (!user) return <p className="text-sm text-muted">Войдите в аккаунт, чтобы оставить отзыв.</p>;
  return (
    <div className="space-y-3">
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((value) => (
          <button key={value} type="button" onClick={() => setRating(value)} aria-label={`Оценка ${value}`}>
            <Star size={24} className={value <= rating ? "fill-amber text-amber" : "text-muted/40"} />
          </button>
        ))}
      </div>
      <Input label="Заголовок" value={title} onChange={(event) => setTitle(event.target.value)} />
      <Textarea label="Отзыв" value={body} onChange={(event) => setBody(event.target.value)} rows={5} placeholder="Расскажите о вашем пребывании в SunStay…" />
      <Button onClick={() => mutation.mutate()} disabled={mutation.isPending || body.trim().length < 10}>Опубликовать</Button>
    </div>
  );
}
