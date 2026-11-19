import React from "react";

type ErrorState = { hasError: boolean; message?: string };

export class ErrorBoundary extends React.Component<{ children: React.ReactNode }, ErrorState> {
  state: ErrorState = { hasError: false };

  static getDerivedStateFromError(error: unknown): ErrorState {
    return { hasError: true, message: error instanceof Error ? error.message : String(error) };
  }

  componentDidCatch(error: unknown) {
    console.error("SunStay UI error", error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-[60vh] items-center justify-center p-6">
          <div className="card max-w-lg text-center">
            <p className="label text-terracotta">Что-то пошло не так</p>
            <h1 className="mt-2 font-display text-3xl font-semibold text-ink">Не удалось открыть раздел</h1>
            <p className="mt-3 text-sm text-muted">Обновите страницу. Если ошибка повторится — проверьте соединение с сервером.</p>
            <button className="btn-primary mt-5" onClick={() => window.location.reload()}>Обновить</button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

export function PageSkeleton() {
  return (
    <div className="animate-pulse space-y-4 p-4">
      <div className="h-8 w-56 rounded-lg bg-surface2" />
      <div className="grid gap-4 md:grid-cols-3">
        <div className="h-28 rounded-2xl bg-surface2" />
        <div className="h-28 rounded-2xl bg-surface2" />
        <div className="h-28 rounded-2xl bg-surface2" />
      </div>
      <div className="h-64 rounded-2xl bg-surface2" />
    </div>
  );
}
