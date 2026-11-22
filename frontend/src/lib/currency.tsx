import { createContext, useContext, useMemo, useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "./api";
import { formatMoney } from "./utils";

export type Currency = "RUB" | "USD" | "EUR";

type CurrencyContextValue = {
  currency: Currency;
  setCurrency: (currency: Currency) => void;
  rates: Record<Currency, number>;
  format: (value?: number | string | null) => string;
};

const DEFAULT_RATES: Record<Currency, number> = { RUB: 1, USD: 90, EUR: 100 };
const CurrencyContext = createContext<CurrencyContextValue | null>(null);

export function CurrencyProvider({ children }: { children: ReactNode }) {
  const [currency, setCurrencyState] = useState<Currency>(() => {
    const saved = localStorage.getItem("sunstay_currency") as Currency | null;
    return saved && ["RUB", "USD", "EUR"].includes(saved) ? saved : "RUB";
  });

  const { data } = useQuery({
    queryKey: ["public-currencies"],
    queryFn: () => api.get("/public/currencies").then((response) => response.data),
    staleTime: 300000,
    retry: 1,
  });

  const rates = useMemo<Record<Currency, number>>(
    () => ({
      RUB: 1,
      USD: Number(data?.rates?.USD || DEFAULT_RATES.USD),
      EUR: Number(data?.rates?.EUR || DEFAULT_RATES.EUR),
    }),
    [data],
  );

  const value = useMemo<CurrencyContextValue>(() => {
    const setCurrency = (next: Currency) => {
      localStorage.setItem("sunstay_currency", next);
      setCurrencyState(next);
    };
    const format = (amount?: number | string | null) => {
      if (currency === "RUB") return formatMoney(amount);
      const converted = Number(amount ?? 0) / rates[currency];
      return new Intl.NumberFormat("ru-RU", {
        style: "currency",
        currency,
        maximumFractionDigits: 0,
      }).format(Number.isFinite(converted) ? converted : 0);
    };
    return { currency, setCurrency, rates, format };
  }, [currency, rates]);

  return <CurrencyContext.Provider value={value}>{children}</CurrencyContext.Provider>;
}

export function useCurrency() {
  const context = useContext(CurrencyContext);
  if (!context) throw new Error("useCurrency must be used inside CurrencyProvider");
  return context;
}

export function CurrencySelect() {
  const { currency, setCurrency } = useCurrency();
  return (
    <select
      value={currency}
      onChange={(event) => setCurrency(event.target.value as Currency)}
      className="no-arrow h-9 rounded-xl border border-line bg-surface px-2 pr-2 text-xs font-semibold text-muted outline-none focus:border-terracotta"
      title="Валюта отображения"
    >
      <option value="RUB">RUB</option>
      <option value="USD">USD</option>
      <option value="EUR">EUR</option>
    </select>
  );
}
