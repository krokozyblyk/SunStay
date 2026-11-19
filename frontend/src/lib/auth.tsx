import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { ACCESS_KEY, REFRESH_KEY, USER_KEY, api } from "./api";
import { useI18n } from "./i18n";
import { useTheme, type Theme } from "./theme";

export type User = {
  user_id: number;
  role_id: number;
  role_name: string;
  role_code: string;
  full_name: string;
  email: string;
  phone?: string | null;
  guest_id?: number | null;
  permissions: string[];
};

export type UserSettings = {
  theme: Theme;
  language: "ru" | "en";
  date_format: string;
  number_format: string;
  page_size: number;
  saved_filters: Array<Record<string, unknown>>;
};

const DEFAULT_SETTINGS: UserSettings = {
  theme: "light",
  language: "ru",
  date_format: "dd.MM.yyyy",
  number_format: "space_comma",
  page_size: 25,
  saved_filters: [],
};

export type LoginResult = {
  user?: User;
  requires_2fa?: boolean;
  twofa_token?: string;
};

type AuthContextValue = {
  user: User | null;
  settings: UserSettings;
  loading: boolean;
  login: (email: string, password: string) => Promise<LoginResult>;
  verify2fa: (twofaToken: string, code: string) => Promise<User>;
  register: (payload: Record<string, unknown>) => Promise<User>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  updateSettings: (patch: Partial<UserSettings>) => Promise<void>;
  hasPermission: (permission: string) => boolean;
  isStaff: boolean;
  isGuest: boolean;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const { setTheme } = useTheme();
  const { setLang } = useI18n();
  const [user, setUser] = useState<User | null>(() => {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return null;
    try {
      return JSON.parse(raw) as User;
    } catch {
      return null;
    }
  });
  const [settings, setSettings] = useState<UserSettings>(DEFAULT_SETTINGS);
  const [loading, setLoading] = useState(true);

  const applySettings = useCallback(
    (next: UserSettings) => {
      setSettings(next);
      setTheme(next.theme ?? "light");
      setLang(next.language === "en" ? "en" : "ru");
    },
    [setLang, setTheme],
  );

  const clearSession = useCallback(() => {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_KEY);
    setUser(null);
    setSettings(DEFAULT_SETTINGS);
  }, []);

  const loadMe = useCallback(async () => {
    const response = await api.get("/auth/me");
    const data = response.data;
    const nextSettings = { ...DEFAULT_SETTINGS, ...(data.settings ?? {}) } as UserSettings;
    setUser(data.user);
    localStorage.setItem(USER_KEY, JSON.stringify(data.user));
    applySettings(nextSettings);
  }, [applySettings]);

  const refreshUser = useCallback(async () => {
    if (!localStorage.getItem(ACCESS_KEY)) return;
    await loadMe();
  }, [loadMe]);

  useEffect(() => {
    let cancelled = false;
    async function bootstrap() {
      const access = localStorage.getItem(ACCESS_KEY);
      const refresh = localStorage.getItem(REFRESH_KEY);
      if (!access) {
        setLoading(false);
        return;
      }
      try {
        await loadMe();
      } catch {
        if (refresh) {
          try {
            const response = await api.post("/auth/refresh", { refresh_token: refresh });
            localStorage.setItem(ACCESS_KEY, response.data.access_token);
            localStorage.setItem(REFRESH_KEY, response.data.refresh_token);
            await loadMe();
          } catch {
            if (!cancelled) clearSession();
          }
        } else if (!cancelled) {
          clearSession();
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    bootstrap();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = useCallback(
    async (email: string, password: string): Promise<LoginResult> => {
      const response = await api.post("/auth/login", { email, password });
      if (response.data.requires_2fa) {
        return { requires_2fa: true, twofa_token: response.data.twofa_token };
      }
      localStorage.setItem(ACCESS_KEY, response.data.access_token);
      localStorage.setItem(REFRESH_KEY, response.data.refresh_token);
      localStorage.setItem(USER_KEY, JSON.stringify(response.data.user));
      setUser(response.data.user);
      await loadMe();
      return { user: response.data.user as User };
    },
    [loadMe],
  );

  const verify2fa = useCallback(
    async (twofaToken: string, code: string) => {
      const response = await api.post("/auth/2fa/verify", { twofa_token: twofaToken, code });
      localStorage.setItem(ACCESS_KEY, response.data.access_token);
      localStorage.setItem(REFRESH_KEY, response.data.refresh_token);
      localStorage.setItem(USER_KEY, JSON.stringify(response.data.user));
      setUser(response.data.user);
      await loadMe();
      return response.data.user as User;
    },
    [loadMe],
  );

  const register = useCallback(
    async (payload: Record<string, unknown>) => {
      const response = await api.post("/auth/register", payload);
      localStorage.setItem(ACCESS_KEY, response.data.access_token);
      localStorage.setItem(REFRESH_KEY, response.data.refresh_token);
      localStorage.setItem(USER_KEY, JSON.stringify(response.data.user));
      setUser(response.data.user);
      await loadMe();
      return response.data.user as User;
    },
    [loadMe],
  );

  const logout = useCallback(async () => {
    const refresh = localStorage.getItem(REFRESH_KEY);
    try {
      if (refresh) await api.post("/auth/logout", { refresh_token: refresh });
    } catch {
      // ignore
    } finally {
      clearSession();
    }
  }, [clearSession]);

  const updateSettings = useCallback(
    async (patch: Partial<UserSettings>) => {
      const next = { ...settings, ...patch };
      const response = await api.put("/settings", next);
      applySettings({ ...DEFAULT_SETTINGS, ...response.data });
    },
    [applySettings, settings],
  );

  const hasPermission = useCallback(
    (permission: string) => Boolean(user?.permissions?.includes(permission)),
    [user],
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      settings,
      loading,
      login,
      verify2fa,
      register,
      logout,
      refreshUser,
      updateSettings,
      hasPermission,
      isStaff: Boolean(user && user.role_code !== "GUEST"),
      isGuest: user?.role_code === "GUEST",
    }),
    [user, settings, loading, login, verify2fa, register, logout, refreshUser, updateSettings, hasPermission],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
