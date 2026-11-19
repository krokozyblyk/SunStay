import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "../lib/auth";
import { useI18n } from "../lib/i18n";
import { api, getErrorMessage } from "../lib/api";
import { Button, Card, Input, PageHeader, Select, useToast } from "../components/ui";
import { TwoFactorSetup } from "../components/TwoFactor";

export function StaffSettingsPage() {
  const { user, settings, updateSettings, refreshUser } = useAuth();
  const { setLang } = useI18n();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [form, setForm] = useState(settings);
  const [profileForm, setProfileForm] = useState({
    full_name: user?.full_name ?? "",
    email: user?.email ?? "",
    phone: user?.phone ?? "",
  });
  const [passwordForm, setPasswordForm] = useState({ old_password: "", new_password: "" });

  const profileMutation = useMutation({
    mutationFn: () => api.patch("/auth/profile", profileForm),
    onSuccess: () => {
      toast("Личные данные сохранены", "success");
      refreshUser();
      queryClient.invalidateQueries();
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

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
      toast("Пароль изменён", "success");
      setPasswordForm({ old_password: "", new_password: "" });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  return (
    <div>
      <PageHeader title="Настройки" subtitle="Личные настройки, пароль и двухфакторная аутентификация." />
      <div className="grid gap-5 lg:grid-cols-2">
        <Card className="space-y-3">
          <h2 className="font-display text-2xl font-semibold">Личные данные</h2>
          <Input label="ФИО" value={profileForm.full_name} onChange={(event) => setProfileForm({ ...profileForm, full_name: event.target.value })} />
          <Input label="Email" value={profileForm.email} onChange={(event) => setProfileForm({ ...profileForm, email: event.target.value })} />
          <Input label="Телефон" value={profileForm.phone} onChange={(event) => setProfileForm({ ...profileForm, phone: event.target.value })} />
          <Button onClick={() => profileMutation.mutate()} disabled={profileMutation.isPending || profileForm.full_name.trim().length < 3 || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(profileForm.email)}>Сохранить данные</Button>
        </Card>
        <Card className="space-y-4">
          <h2 className="font-display text-2xl font-semibold">Отображение</h2>
          <Select label="Тема" value={form.theme} onChange={(event) => setForm({ ...form, theme: event.target.value as any })}>
            <option value="light">Светлая</option>
            <option value="dark">Тёмная</option>
            <option value="system">Системная</option>
          </Select>
          <Select label="Язык" value={form.language} onChange={(event) => setForm({ ...form, language: event.target.value as "ru" | "en" })}>
            <option value="ru">Русский</option>
            <option value="en">English</option>
          </Select>
          <Button onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending}>Сохранить</Button>
        </Card>
        <Card className="space-y-3">
          <h2 className="font-display text-2xl font-semibold">Смена пароля</h2>
          <Input label="Текущий пароль" type="password" value={passwordForm.old_password} onChange={(event) => setPasswordForm({ ...passwordForm, old_password: event.target.value })} />
          <Input label="Новый пароль" type="password" value={passwordForm.new_password} onChange={(event) => setPasswordForm({ ...passwordForm, new_password: event.target.value })} />
          <Button onClick={() => passwordMutation.mutate()} disabled={passwordMutation.isPending || !passwordForm.old_password || passwordForm.new_password.length < 8}>Сменить пароль</Button>
        </Card>
        <div className="lg:col-span-2"><TwoFactorSetup /></div>
      </div>
    </div>
  );
}
