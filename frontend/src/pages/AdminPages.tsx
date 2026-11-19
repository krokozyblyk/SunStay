import {
  Activity,
  Ban,
  BookOpen,
  Check,
  DatabaseBackup,
  Download,
  Edit,
  Eye,
  KeyRound,
  Plus,
  RefreshCw,
  Save,
  ShieldCheck,
  Star,
  Trash2,
  Unlock,
  Upload,
  UserCheck,
  Users,
  X,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, downloadFile, getErrorMessage } from "../lib/api";
import { useAuth } from "../lib/auth";
import { useToast } from "../components/ui";
import { TwoFactorSetup } from "../components/TwoFactor";
import {
  Avatar,
  Badge,
  Button,
  Card,
  Drawer,
  EmptyState,
  ErrorState,
  Input,
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
import { formatDate, formatDateTime, formatMoney, formatNumber, ROLE_LABELS, statusLabel } from "../lib/utils";

type DirectoryField = {
  key: string;
  label: string;
  type?: "text" | "number" | "date" | "textarea" | "select" | "image";
  options?: Array<{ value: string | number; label: string }>;
  required?: boolean;
};

const DIRECTORY_PK: Record<string, string> = {
  "room-types": "room_type_id",
  rooms: "room_id",
  amenities: "amenity_id",
  "rate-plans": "rate_id",
  services: "service_id",
  "promo-codes": "promo_id",
  "cancellation-reasons": "reason_id",
};

const DIRECTORY_CONFIG: Record<string, { label: string; fields: DirectoryField[] }> = {
  "room-types": {
    label: "Типы номеров",
    fields: [
      { key: "name", label: "Название", required: true },
      { key: "capacity", label: "Вместимость", type: "number", required: true },
      { key: "description", label: "Описание", type: "textarea" },
      { key: "image_url", label: "Фото (ссылка или файл)", type: "image" },
    ],
  },
  rooms: {
    label: "Номера",
    fields: [
      { key: "room_number", label: "Номер", required: true },
      { key: "floor", label: "Этаж", type: "number", required: true },
      { key: "room_type_id", label: "Тип", type: "select", required: true },
      { key: "status_id", label: "Статус", type: "select", required: true },
      { key: "block_reason_id", label: "Причина блокировки", type: "select" },
    ],
  },
  amenities: {
    label: "Удобства",
    fields: [{ key: "name", label: "Название", required: true }],
  },
  "rate-plans": {
    label: "Тарифы",
    fields: [
      { key: "room_type_id", label: "Тип номера", type: "select", required: true },
      { key: "name", label: "Название", required: true },
      { key: "season_start", label: "Начало сезона", type: "date", required: true },
      { key: "season_end", label: "Конец сезона", type: "date", required: true },
      { key: "price_per_night", label: "Цена за ночь", type: "number", required: true },
      { key: "cancellation_terms", label: "Условия отмены", type: "textarea" },
    ],
  },
  services: {
    label: "Услуги",
    fields: [
      { key: "unit_id", label: "Единица", type: "select", required: true },
      { key: "name", label: "Название", required: true },
      { key: "price", label: "Цена", type: "number", required: true },
      { key: "image_url", label: "Фото (ссылка или файл)", type: "image" },
    ],
  },
  "promo-codes": {
    label: "Промокоды",
    fields: [
      { key: "code", label: "Код", required: true },
      { key: "discount_percent", label: "Скидка, %", type: "number", required: true },
      { key: "valid_from", label: "Действует с", type: "date", required: true },
      { key: "valid_to", label: "Действует до", type: "date", required: true },
    ],
  },
  "cancellation-reasons": {
    label: "Причины отмены",
    fields: [{ key: "name", label: "Название", required: true }],
  },
};

function UsersTable({ mode }: { mode: "admin" | "employees" }) {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);
  const [createOpen, setCreateOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [resetOpen, setResetOpen] = useState(false);
  const [blockOpen, setBlockOpen] = useState(false);
  const [selected, setSelected] = useState<any>(null);
  const [blockUser, setBlockUser] = useState<any>(null);
  const [blockReasonId, setBlockReasonId] = useState("");
  const [blockCustom, setBlockCustom] = useState("");
  const [form, setForm] = useState({ role_id: "2", full_name: "", email: "", phone: "", password: "" });
  const [resetPassword, setResetPassword] = useState("");
  const [roleValue, setRoleValue] = useState("2");

  const query = useQuery({
    queryKey: ["admin-users", search, roleFilter, statusFilter, page],
    queryFn: () => api.get("/admin/users", {
      params: {
        search: search || undefined,
        role_id: roleFilter || undefined,
        status_filter: statusFilter || undefined,
        page,
        page_size: 25,
      },
    }).then((response) => response.data),
  });
  const rolesQuery = useQuery({
    queryKey: ["admin-roles"],
    queryFn: () => api.get("/admin/roles").then((response) => response.data),
  });
  const statsQuery = useQuery({
    queryKey: ["admin-user-stats"],
    queryFn: () => api.get("/admin/users/stats").then((response) => response.data),
    enabled: mode === "admin",
  });
  const reasonsQuery = useQuery({
    queryKey: ["user-block-reasons"],
    queryFn: () => api.get("/admin/users/block-reasons").then((response) => response.data),
    enabled: mode === "admin",
  });

  const createMutation = useMutation({
    mutationFn: () => api.post("/admin/users", { ...form, role_id: Number(form.role_id) }),
    onSuccess: () => {
      toast("Пользователь создан", "success");
      setCreateOpen(false);
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      queryClient.invalidateQueries({ queryKey: ["admin-user-stats"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const editMutation = useMutation({
    mutationFn: () => api.patch(`/admin/users/${selected.user_id}`, {
      role_id: Number(roleValue),
      full_name: form.full_name,
      email: form.email,
      phone: form.phone,
    }),
    onSuccess: () => {
      toast("Пользователь обновлён", "success");
      setEditOpen(false);
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const blockMutation = useMutation({
    mutationFn: ({ id, reason_id, custom_reason }: { id: number; reason_id: number | null; custom_reason: string | null }) =>
      api.post(`/admin/users/${id}/block`, { reason_id, custom_reason }),
    onSuccess: () => {
      toast("Пользователь заблокирован", "success");
      setBlockOpen(false);
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      queryClient.invalidateQueries({ queryKey: ["admin-user-stats"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const unblockMutation = useMutation({
    mutationFn: (id: number) => api.post(`/admin/users/${id}/unblock`),
    onSuccess: () => {
      toast("Пользователь разблокирован", "success");
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      queryClient.invalidateQueries({ queryKey: ["admin-user-stats"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const resetMutation = useMutation({
    mutationFn: () => api.post(`/admin/users/${selected.user_id}/reset-password`, { new_password: resetPassword }),
    onSuccess: () => {
      toast("Пароль обновлён", "success");
      setResetOpen(false);
      setResetPassword("");
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const roleMutation = useMutation({
    mutationFn: () => api.patch(`/admin/users/${selected.user_id}/role`, { role_id: Number(roleValue) }),
    onSuccess: () => {
      toast("Роль обновлена", "success");
      setEditOpen(false);
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  const items = query.data?.items ?? [];
  const total = query.data?.total ?? 0;
  const roles = rolesQuery.data ?? [];
  const stats = statsQuery.data?.summary ?? {};
  const reasons = reasonsQuery.data ?? [];
  const editableRoles = mode === "employees" ? roles.filter((role: any) => [2, 3].includes(role.role_id)) : roles;

  function openCreate() {
    setForm({ role_id: "2", full_name: "", email: "", phone: "", password: "" });
    setCreateOpen(true);
  }

  function openEdit(userRow: any) {
    setSelected(userRow);
    setForm({
      role_id: String(userRow.role_id),
      full_name: userRow.full_name ?? "",
      email: userRow.email ?? "",
      phone: userRow.phone ?? "",
      password: "",
    });
    setRoleValue(String(userRow.role_id));
    setEditOpen(true);
  }

  function openBlock(userRow: any) {
    setBlockUser(userRow);
    setBlockReasonId("");
    setBlockCustom("");
    setBlockOpen(true);
  }

  function submitBlock() {
    if (!blockReasonId && !blockCustom.trim()) {
      toast("Укажите причину блокировки", "error");
      return;
    }
    blockMutation.mutate({
      id: blockUser.user_id,
      reason_id: blockReasonId ? Number(blockReasonId) : null,
      custom_reason: blockCustom.trim() || null,
    });
  }

  return (
    <div>
      {mode === "admin" && (
        <div className="mb-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div><p className="label">Всего</p><p className="kpi-value mt-2">{stats.total ?? 0}</p></div>
              <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-forest/10 text-forest dark:bg-white/10 dark:text-ink"><Users size={19} /></span>
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div><p className="label">Онлайн</p><p className="kpi-value mt-2">{stats.online ?? 0}</p></div>
              <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-emerald-500/12 text-emerald-600"><Activity size={19} /></span>
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div><p className="label">Активные</p><p className="kpi-value mt-2">{stats.active ?? 0}</p></div>
              <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-sky-500/12 text-sky-600"><UserCheck size={19} /></span>
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div><p className="label">Заблокированные</p><p className="kpi-value mt-2">{stats.blocked ?? 0}</p></div>
              <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-rose-500/12 text-rose-600"><Ban size={19} /></span>
            </div>
          </Card>
        </div>
      )}

      <Card className="mb-4 flex flex-wrap items-end gap-2">
        <Input
          label="Поиск"
          value={search}
          onChange={(event) => { setSearch(event.target.value); setPage(1); }}
          placeholder="ФИО, email, телефон"
          className="min-w-[220px]"
        />
        {mode === "admin" && (
          <Select label="Роль" value={roleFilter} onChange={(event) => { setRoleFilter(event.target.value); setPage(1); }}>
            <option value="">Все роли</option>
            {roles.map((role: any) => <option key={role.role_id} value={role.role_id}>{role.name}</option>)}
          </Select>
        )}
        {mode === "admin" && (
          <Select label="Статус" value={statusFilter} onChange={(event) => { setStatusFilter(event.target.value); setPage(1); }}>
            <option value="">Все</option>
            <option value="online">Онлайн</option>
            <option value="active">Активные</option>
            <option value="blocked">Заблокированные</option>
          </Select>
        )}
        <Button variant="secondary" onClick={() => query.refetch()}><RefreshCw size={14} /> Обновить</Button>
        {mode === "admin" && <Button onClick={openCreate}><Plus size={15} /> Добавить пользователя</Button>}
      </Card>

      {query.isLoading && <Spinner />}
      {query.isError && <ErrorState message={getErrorMessage(query.error)} />}
      {!query.isLoading && !query.isError && (
        <div className="table-wrap">
          <table className="table-base">
            <thead><tr><th>Сотрудник</th><th>Роль</th><th>Контакты</th><th>Статус</th><th>2FA</th><th>Последняя активность</th><th /></tr></thead>
            <tbody>
              {items.map((userRow: any) => (
                <tr key={userRow.user_id}>
                  <td>
                    <div className="flex items-center gap-3">
                      <Avatar name={userRow.full_name} className="h-9 w-9 text-[10px]" />
                      <div><p className="font-semibold">{userRow.full_name}</p><p className="text-xs text-muted">{userRow.email}</p></div>
                    </div>
                  </td>
                  <td><Badge tone={userRow.role_id === 5 ? "danger" : userRow.role_id === 4 ? "warning" : "info"}>{userRow.role_name}</Badge></td>
                  <td>
                    <SensitiveValue value={userRow.phone} />
                    <p className="mt-1 text-xs text-muted">{userRow.email}</p>
                  </td>
                  <td>
                    {!userRow.is_active ? (
                      <div><Badge tone="danger">Заблокирован</Badge><p className="mt-1 max-w-[220px] text-xs text-muted">{userRow.block_reason ?? "Причина не указана"}</p></div>
                    ) : userRow.is_online ? (
                      <Badge tone="success">Онлайн</Badge>
                    ) : (
                      <Badge tone="neutral">Не в сети</Badge>
                    )}
                  </td>
                  <td><span className={userRow.totp_enabled ? "text-success" : "text-muted"}>{userRow.totp_enabled ? "✓" : "✗"}</span></td>
                  <td>{userRow.last_seen_at ? formatDateTime(userRow.last_seen_at) : "—"}</td>
                  <td className="text-right">
                    <div className="flex justify-end gap-1">
                      {mode === "admin" && <Button variant="ghost" size="sm" onClick={() => openEdit(userRow)}><Edit size={14} /></Button>}
                      {mode === "employees" && <Button variant="ghost" size="sm" onClick={() => openEdit(userRow)}>Роль</Button>}
                      {mode === "admin" && <Button variant="ghost" size="sm" onClick={() => { setSelected(userRow); setResetOpen(true); }}><KeyRound size={14} /></Button>}
                      {mode === "admin" && (
                        userRow.is_active
                          ? <Button variant="ghost" size="sm" onClick={() => openBlock(userRow)}><Ban size={14} /></Button>
                          : <Button variant="ghost" size="sm" onClick={() => unblockMutation.mutate(userRow.user_id)}><Unlock size={14} /></Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pagination page={page} pageSize={25} total={total} onPageChange={setPage} />
        </div>
      )}

      <Modal open={createOpen} title="Новый пользователь" onClose={() => setCreateOpen(false)} footer={<><Button variant="secondary" onClick={() => setCreateOpen(false)}>Отмена</Button><Button onClick={() => createMutation.mutate()} disabled={createMutation.isPending}>Создать</Button></>}>
        <div className="space-y-3">
          <Select label="Роль" value={form.role_id} onChange={(event) => setForm({ ...form, role_id: event.target.value })}>
            {roles.map((role: any) => <option key={role.role_id} value={role.role_id}>{role.name}</option>)}
          </Select>
          <Input label="ФИО" value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} />
          <Input label="Email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />
          <Input label="Телефон" value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} />
          <Input label="Пароль" type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} />
        </div>
      </Modal>

      <Modal open={editOpen} title={mode === "employees" ? "Назначение роли" : "Редактировать пользователя"} onClose={() => setEditOpen(false)} footer={<><Button variant="secondary" onClick={() => setEditOpen(false)}>Отмена</Button>{mode === "employees" ? <Button onClick={() => roleMutation.mutate()} disabled={roleMutation.isPending}>Сохранить роль</Button> : <Button onClick={() => editMutation.mutate()} disabled={editMutation.isPending}>Сохранить</Button>}</>}>
        <div className="space-y-3">
          {mode === "admin" && <Input label="ФИО" value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} />}
          {mode === "admin" && <Input label="Email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} />}
          {mode === "admin" && <Input label="Телефон" value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} />}
          <Select label="Роль" value={roleValue} onChange={(event) => setRoleValue(event.target.value)}>
            {editableRoles.map((role: any) => <option key={role.role_id} value={role.role_id}>{role.name}</option>)}
          </Select>
        </div>
      </Modal>

      <Modal open={resetOpen} title="Сброс пароля" onClose={() => setResetOpen(false)} footer={<><Button variant="secondary" onClick={() => setResetOpen(false)}>Отмена</Button><Button onClick={() => resetMutation.mutate()} disabled={resetMutation.isPending || resetPassword.length < 8}>Сбросить</Button></>}>
        <Input label="Новый пароль" type="password" value={resetPassword} onChange={(event) => setResetPassword(event.target.value)} />
      </Modal>

      <Modal open={blockOpen} title="Блокировка пользователя" subtitle={blockUser?.full_name} onClose={() => setBlockOpen(false)} footer={<><Button variant="secondary" onClick={() => setBlockOpen(false)}>Отмена</Button><Button variant="danger" onClick={submitBlock} disabled={blockMutation.isPending}>Заблокировать</Button></>}>
        <div className="space-y-3">
          <Select label="Причина" value={blockReasonId} onChange={(event) => setBlockReasonId(event.target.value)}>
            <option value="">Выберите причину</option>
            {reasons.map((reason: any) => <option key={reason.reason_id} value={reason.reason_id}>{reason.name}</option>)}
          </Select>
          <Input label="Своя причина" value={blockCustom} onChange={(event) => setBlockCustom(event.target.value)} placeholder="Можно указать свой текст" />
          <p className="text-xs text-muted">Если выбрана причина из списка, своя причина необязательна.</p>
        </div>
      </Modal>
    </div>
  );
}

function PermissionsMatrix() {
  const { user } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [roleId, setRoleId] = useState("2");
  const [selected, setSelected] = useState<string[]>([]);
  const rolesQuery = useQuery({ queryKey: ["admin-roles"], queryFn: () => api.get("/admin/roles").then((response) => response.data) });
  const permissionsQuery = useQuery({ queryKey: ["admin-permissions"], queryFn: () => api.get("/admin/permissions").then((response) => response.data) });
  const roles = useMemo(() => rolesQuery.data ?? [], [rolesQuery.data]);
  const permissions = useMemo(() => permissionsQuery.data ?? [], [permissionsQuery.data]);
  const grouped = useMemo(() => {
    const map: Record<string, any[]> = {};
    for (const permission of permissions) (map[permission.module] ??= []).push(permission);
    return map;
  }, [permissions]);

  useEffect(() => {
    const role = roles.find((item: any) => String(item.role_id) === roleId);
    const next = role?.permissions ?? [];
    setSelected((current) => (current.join("|") === next.join("|") ? current : next));
  }, [roleId, roles]);

  const saveMutation = useMutation({
    mutationFn: () => api.put(`/admin/roles/${roleId}/permissions`, { permission_codes: selected }),
    onSuccess: () => { toast("Права сохранены", "success"); queryClient.invalidateQueries({ queryKey: ["admin-roles"] }); },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  if (user?.role_code !== "DB_ADMIN") return null;

  return (
    <Card className="mt-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="font-display text-2xl font-semibold">Матрица полномочий</h2>
          <p className="text-sm text-muted">Изменения применяются на сервере сразу после сохранения.</p>
        </div>
        <div className="flex items-end gap-2">
          <Select label="Роль" value={roleId} onChange={(event) => setRoleId(event.target.value)}>
            {roles.map((role: any) => <option key={role.role_id} value={role.role_id}>{role.name}</option>)}
          </Select>
          <Button onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending}><Save size={15} /> Сохранить права</Button>
        </div>
      </div>
      <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {Object.entries(grouped).map(([module, items]) => (
          <div key={module} className="rounded-xl border border-line p-3">
            <p className="mb-2 text-[11px] font-bold uppercase tracking-[0.08em] text-muted">{module}</p>
            <div className="space-y-1.5">
              {items.map((permission: any) => (
                <label key={permission.code} className="flex items-center gap-2 text-xs text-muted">
                  <input
                    type="checkbox"
                    className="h-4 w-4 accent-terracotta"
                    checked={selected.includes(permission.code)}
                    onChange={(event) => setSelected((current) => event.target.checked ? [...current, permission.code] : current.filter((code) => code !== permission.code))}
                  />
                  <span>{permission.description}</span>
                </label>
              ))}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

export function AdminUsersPage() {
  return (
    <div>
      <PageHeader title="Пользователи и роли" subtitle="Учётные записи сотрудников, роли и матрица полномочий." />
      <UsersTable mode="admin" />
      <PermissionsMatrix />
    </div>
  );
}

export function EmployeesPage() {
  return (
    <div>
      <PageHeader title="Сотрудники" subtitle="Назначение ролей Менеджера и Хаускипинга." />
      <UsersTable mode="employees" />
      <div className="mt-5">
        <TwoFactorCard />
      </div>
    </div>
  );
}

export function TwoFactorCard() {
  return <TwoFactorSetup />;
}

function DirectoryPageContent() {
  const { user } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [entity, setEntity] = useState("room-types");
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [form, setForm] = useState<Record<string, any>>({});
  const [importOpen, setImportOpen] = useState(false);
  const [importPreview, setImportPreview] = useState<any>(null);
  const [importFile, setImportFile] = useState<File | null>(null);
  const config = DIRECTORY_CONFIG[entity];
  const allowedTabs = user?.role_code === "HOTEL_MANAGER"
    ? ["rooms", "rate-plans", "services", "promo-codes"]
    : Object.keys(DIRECTORY_CONFIG);
  const activeTabs = allowedTabs.map((key) => ({ value: key, label: DIRECTORY_CONFIG[key].label }));

  useEffect(() => {
    if (!allowedTabs.includes(entity)) setEntity(allowedTabs[0]);
  }, [allowedTabs, entity]);

  const query = useQuery({
    queryKey: ["admin-directory", entity],
    queryFn: () => api.get(`/admin/directories/${entity}`).then((response) => response.data),
  });
  const roomTypesQuery = useQuery({ queryKey: ["admin-directory", "room-types"], queryFn: () => api.get("/admin/directories/room-types").then((response) => response.data), enabled: ["rooms", "rate-plans"].includes(entity) });
  const roomStatusesQuery = useQuery({ queryKey: ["admin-directory", "room-statuses"], queryFn: () => api.get("/admin/directories/room-statuses").then((response) => response.data), enabled: entity === "rooms" });
  const blockReasonsQuery = useQuery({ queryKey: ["admin-directory", "block-reasons"], queryFn: () => api.get("/admin/directories/block-reasons").then((response) => response.data), enabled: entity === "rooms" });
  const serviceUnitsQuery = useQuery({ queryKey: ["admin-directory", "service-units"], queryFn: () => api.get("/admin/directories/service-units").then((response) => response.data), enabled: entity === "services" });

  const createMutation = useMutation({
    mutationFn: () => api.post(`/admin/directories/${entity}`, form),
    onSuccess: () => { toast("Запись добавлена", "success"); setModalOpen(false); queryClient.invalidateQueries({ queryKey: ["admin-directory", entity] }); },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const updateMutation = useMutation({
    mutationFn: () => api.patch(`/admin/directories/${entity}/${editing[DIRECTORY_PK[entity]]}`, form),
    onSuccess: () => { toast("Запись обновлена", "success"); setModalOpen(false); queryClient.invalidateQueries({ queryKey: ["admin-directory", entity] }); },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const deleteMutation = useMutation({
    mutationFn: (item: any) => api.delete(`/admin/directories/${entity}/${item[DIRECTORY_PK[entity]]}`),
    onSuccess: () => { toast("Запись удалена", "success"); queryClient.invalidateQueries({ queryKey: ["admin-directory", entity] }); },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const importPreviewMutation = useMutation({
    mutationFn: (file: File) => {
      const data = new FormData();
      data.append("file", file);
      return api.post("/imports/rates/preview", data, { headers: { "Content-Type": "multipart/form-data" } }).then((response) => response.data);
    },
    onSuccess: (data) => { setImportPreview(data); toast(`Проверено строк: ${data.total}, ошибок: ${data.errors}`, data.errors ? "info" : "success"); },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const importCommitMutation = useMutation({
    mutationFn: () => api.post("/imports/rates/commit", { filename: importFile?.name, rows: importPreview.rows }),
    onSuccess: () => { toast("Тарифы загружены", "success"); setImportOpen(false); setImportPreview(null); setImportFile(null); queryClient.invalidateQueries({ queryKey: ["admin-directory", "rate-plans"] }); },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  function idKey() {
    return DIRECTORY_PK[entity];
  }

  function openCreate() {
    setEditing(null);
    setForm({});
    setModalOpen(true);
  }

  function openEdit(item: any) {
    setEditing(item);
    const next: Record<string, any> = {};
    for (const field of config.fields) next[field.key] = item[field.key] ?? "";
    setForm(next);
    setModalOpen(true);
  }

  function optionsFor(field: DirectoryField) {
    if (field.key === "room_type_id") return (roomTypesQuery.data ?? []).map((item: any) => ({ value: item.room_type_id, label: item.name }));
    if (field.key === "status_id") return (roomStatusesQuery.data ?? []).map((item: any) => ({ value: item.status_id, label: item.name }));
    if (field.key === "block_reason_id") return [{ value: "", label: "Не блокирован" }, ...(blockReasonsQuery.data ?? []).map((item: any) => ({ value: item.reason_id, label: item.name }))];
    if (field.key === "unit_id") return (serviceUnitsQuery.data ?? []).map((item: any) => ({ value: item.unit_id, label: item.name }));
    return field.options ?? [];
  }

  const items = query.data ?? [];
  const columns = config.fields.filter((field) => field.key !== "description" && field.key !== "cancellation_terms");

  return (
    <div>
      <PageHeader
        title="Справочники отеля"
        subtitle="Типы номеров, номера, тарифы, услуги и промокоды."
        actions={
          <>
            {entity === "rate-plans" && <Button variant="secondary" onClick={() => setImportOpen(true)}><Upload size={15} /> Импорт CSV</Button>}
            <Button onClick={openCreate}><Plus size={15} /> Добавить</Button>
          </>
        }
      />
      <Tabs className="mb-4" value={entity} onChange={setEntity} items={activeTabs} />
      {query.isLoading && <Spinner />}
      {query.isError && <ErrorState message={getErrorMessage(query.error)} />}
      {!query.isLoading && !query.isError && (
        <div className="table-wrap">
          <table className="table-base">
            <thead><tr>{columns.map((field) => <th key={field.key}>{field.label}</th>)}<th /></tr></thead>
            <tbody>
              {items.map((item: any) => (
                <tr key={item[idKey()]}>
                  {columns.map((field) => {
                    let value = item[field.key];
                    if (field.key === "room_type_id") value = (roomTypesQuery.data ?? []).find((roomType: any) => roomType.room_type_id === value)?.name ?? value;
                    if (field.key === "status_id") value = (roomStatusesQuery.data ?? []).find((status: any) => status.status_id === value)?.name ?? value;
                    if (field.key === "unit_id") value = (serviceUnitsQuery.data ?? []).find((unit: any) => unit.unit_id === value)?.name ?? value;
                    if (field.key === "block_reason_id") value = value ? value : "—";
                    if (field.type === "number" && ["price_per_night", "price"].includes(field.key)) value = formatMoney(value);
                    return <td key={field.key}>{String(value ?? "—")}</td>;
                  })}
                  <td className="text-right">
                    <div className="flex justify-end gap-1">
                      <Button variant="ghost" size="sm" onClick={() => openEdit(item)}><Edit size={14} /></Button>
                      <Button variant="ghost" size="sm" onClick={() => { if (window.confirm("Удалить запись?")) deleteMutation.mutate(item); }}><Trash2 size={14} /></Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!items.length && <EmptyState />}
        </div>
      )}

      <Modal open={modalOpen} title={editing ? "Редактировать запись" : "Добавить запись"} onClose={() => setModalOpen(false)} footer={<><Button variant="secondary" onClick={() => setModalOpen(false)}>Отмена</Button><Button onClick={() => editing ? updateMutation.mutate() : createMutation.mutate()} disabled={createMutation.isPending || updateMutation.isPending}><Save size={15} /> Сохранить</Button></>}>
        <div className="space-y-3">
          {config.fields.map((field) => {
            if (field.type === "select") {
              return (
                <Select key={field.key} label={field.label} value={form[field.key] ?? ""} onChange={(event) => setForm({ ...form, [field.key]: event.target.value })}>
                  <option value="">Выберите</option>
                  {optionsFor(field).map((option: { value: string | number; label: string }) => <option key={option.value} value={option.value}>{option.label}</option>)}
                </Select>
              );
            }
            if (field.type === "textarea") {
              return <Textarea key={field.key} label={field.label} value={form[field.key] ?? ""} onChange={(event) => setForm({ ...form, [field.key]: event.target.value })} />;
            }
            if (field.type === "image") {
              return (
                <div key={field.key} className="space-y-2">
                  <Input label={field.label} value={form[field.key] ?? ""} onChange={(event) => setForm({ ...form, [field.key]: event.target.value })} />
                  <input
                    type="file"
                    accept="image/*"
                    className="input py-2"
                    onChange={(event) => {
                      const file = event.target.files?.[0];
                      if (!file) return;
                      const reader = new FileReader();
                      reader.onload = () => setForm((current) => ({ ...current, [field.key]: String(reader.result) }));
                      reader.readAsDataURL(file);
                    }}
                  />
                  {String(form[field.key] ?? "").startsWith("data:image") && <img src={String(form[field.key])} alt="Превью" className="h-24 w-full rounded-xl object-cover" />}
                </div>
              );
            }
            return <Input key={field.key} label={field.label} type={field.type ?? "text"} value={form[field.key] ?? ""} onChange={(event) => setForm({ ...form, [field.key]: field.type === "number" ? Number(event.target.value) : event.target.value })} />;
          })}
        </div>
      </Modal>

      <Modal open={importOpen} title="Импорт тарифов из CSV" subtitle="CSV: room_type, name, season_start, season_end, price_per_night, cancellation_terms" onClose={() => setImportOpen(false)} size="lg" footer={<><Button variant="secondary" onClick={() => setImportOpen(false)}>Отмена</Button><Button onClick={() => importCommitMutation.mutate()} disabled={!importPreview?.rows?.some((row: any) => row.status === "ok") || importCommitMutation.isPending}>Загрузить</Button></>}>
        <div className="space-y-4">
          <input type="file" accept=".csv,text/csv" onChange={(event) => { const file = event.target.files?.[0]; if (file) { setImportFile(file); importPreviewMutation.mutate(file); } }} className="input py-2" />
          {importPreview && (
            <div className="space-y-2">
              <div className="flex gap-3 text-sm"><span>Всего: {importPreview.total}</span><span className="text-success">OK: {importPreview.valid}</span><span className="text-danger">Ошибок: {importPreview.errors}</span></div>
              <div className="max-h-72 overflow-auto rounded-xl border border-line">
                <table className="table-base">
                  <thead><tr><th>Строка</th><th>Тип</th><th>Название</th><th>Цена</th><th>Статус</th><th>Ошибка</th></tr></thead>
                  <tbody>
                    {importPreview.rows.map((row: any) => (
                      <tr key={row.row}>
                        <td>{row.row}</td><td>{row.room_type}</td><td>{row.name}</td><td>{formatMoney(row.price_per_night)}</td>
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

export function AdminDirectoriesPage() {
  return <DirectoryPageContent />;
}

export function AdminAuditPage() {
  const [tab, setTab] = useState("data");
  const [roleFilter, setRoleFilter] = useState("");
  const [userSearch, setUserSearch] = useState("");
  const [tableName, setTableName] = useState("");
  const [action, setAction] = useState("");
  const [errorsOnly, setErrorsOnly] = useState(false);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<any>(null);

  const eventType = tab === "login" ? "LOGIN_SECURITY" : tab === "system" ? "AUTO_RELEASE" : "DATA_CHANGE";
  const params = {
    role_id: roleFilter || undefined,
    user_search: userSearch || undefined,
    table_name: tableName || undefined,
    action: action || undefined,
    event_type: eventType,
    is_error: errorsOnly ? true : undefined,
    date_from: dateFrom || undefined,
    date_to: dateTo || undefined,
  };

  const rolesQuery = useQuery({
    queryKey: ["admin-roles"],
    queryFn: () => api.get("/admin/roles").then((response) => response.data),
  });
  const query = useQuery({
    queryKey: ["admin-audit", tab, roleFilter, userSearch, tableName, action, errorsOnly, dateFrom, dateTo, page],
    queryFn: () => api.get("/admin/audit", { params: { ...params, page, page_size: 25 } }).then((response) => response.data),
  });
  const roles = rolesQuery.data ?? [];
  const items = query.data?.items ?? [];
  const total = query.data?.total ?? 0;

  function resetFilters() {
    setRoleFilter("");
    setUserSearch("");
    setTableName("");
    setAction("");
    setErrorsOnly(false);
    setDateFrom("");
    setDateTo("");
    setPage(1);
  }

  return (
    <div>
      <PageHeader
        title="Журнал аудита"
        subtitle="Кто, когда и что изменил. Ошибки подсвечиваются красным."
        actions={
          <Button
            variant="secondary"
            onClick={() => downloadFile(api, "/admin/audit/export", "audit.csv", params)}
          >
            <Download size={15} /> Экспорт CSV
          </Button>
        }
      />

      <Tabs
        className="mb-4"
        value={tab}
        onChange={(value) => { setTab(value); setPage(1); }}
        items={[
          { value: "data", label: "Изменения данных" },
          { value: "login", label: "Пользователи и вход" },
          { value: "system", label: "Системные события" },
        ]}
      />

      <Card className="mb-4 flex flex-wrap items-end gap-2">
        <Select label="Роль" value={roleFilter} onChange={(event) => { setRoleFilter(event.target.value); setPage(1); }}>
          <option value="">Все роли</option>
          {roles.map((role: any) => <option key={role.role_id} value={role.role_id}>{role.name}</option>)}
        </Select>
        <Input
          label="Пользователь"
          value={userSearch}
          onChange={(event) => { setUserSearch(event.target.value); setPage(1); }}
          placeholder="Имя или email"
        />
        <Input
          label="Таблица"
          value={tableName}
          onChange={(event) => { setTableName(event.target.value); setPage(1); }}
          placeholder="bookings"
        />
        <Select label="Действие" value={action} onChange={(event) => { setAction(event.target.value); setPage(1); }}>
          <option value="">Все</option>
          <option value="INSERT">INSERT</option>
          <option value="UPDATE">UPDATE</option>
          <option value="DELETE">DELETE</option>
          <option value="LOGIN_SUCCESS">LOGIN_SUCCESS</option>
          <option value="LOGIN_FAILED">LOGIN_FAILED</option>
          <option value="LOGIN_BLOCKED">LOGIN_BLOCKED</option>
          <option value="AUTO_RELEASE">AUTO_RELEASE</option>
          <option value="ERROR">ERROR</option>
        </Select>
        <label className="flex h-10 items-center gap-2 text-sm text-muted">
          <input type="checkbox" checked={errorsOnly} onChange={(event) => { setErrorsOnly(event.target.checked); setPage(1); }} className="h-4 w-4 accent-terracotta" />
          Только ошибки
        </label>
        <Input label="С даты" type="date" value={dateFrom} onChange={(event) => { setDateFrom(event.target.value); setPage(1); }} />
        <Input label="По дату" type="date" value={dateTo} onChange={(event) => { setDateTo(event.target.value); setPage(1); }} />
        <Button variant="secondary" onClick={() => setPage(1)}>Применить</Button>
        <Button variant="ghost" onClick={resetFilters}>Сбросить</Button>
      </Card>

      {query.isLoading && <Spinner />}
      {query.isError && <ErrorState message={getErrorMessage(query.error)} />}
      {!query.isLoading && !query.isError && (
        <div className="table-wrap">
          <table className="table-base">
            <thead>
              <tr>
                <th>Дата</th><th>Пользователь</th><th>Роль</th><th>Действие</th>
                <th>Объект</th><th>Ошибка</th><th>IP</th><th />
              </tr>
            </thead>
            <tbody>
              {items.map((item: any) => (
                <tr key={item.log_id} className={item.is_error ? "bg-rose-500/10" : undefined}>
                  <td>{formatDateTime(item.changed_at)}</td>
                  <td>{item.user_name ?? "—"}</td>
                  <td>{item.role_name ?? "—"}</td>
                  <td>
                    <Badge tone={item.is_error ? "danger" : item.action === "DELETE" ? "danger" : item.action === "INSERT" ? "success" : "warning"}>
                      {item.event_type === "LOGIN_SECURITY" ? item.action : item.action}
                    </Badge>
                  </td>
                  <td>{item.table_name} {item.record_id ? `#${item.record_id}` : ""}</td>
                  <td className="max-w-[260px]">
                    {item.is_error
                      ? <span className="text-xs font-semibold text-rose-600 dark:text-rose-300">{item.error_message ?? "Ошибка"}</span>
                      : <span className="text-xs text-muted">—</span>}
                  </td>
                  <td className="text-xs text-muted">{item.ip_address ?? "—"}</td>
                  <td className="text-right">
                    <Button variant="ghost" size="sm" onClick={() => setSelected(item)}>
                      <Eye size={14} /> Детали
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pagination page={page} pageSize={25} total={total} onPageChange={setPage} />
        </div>
      )}

      <Drawer
        open={Boolean(selected)}
        title={selected?.event_type === "LOGIN_SECURITY" ? "Событие входа" : "Детализация изменений"}
        subtitle={selected ? `${selected.table_name}${selected.record_id ? ` #${selected.record_id}` : ""} · ${selected.action}` : ""}
        onClose={() => setSelected(null)}
      >
        {selected && (
          <div className="space-y-4">
            {selected.is_error && (
              <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-sm text-rose-700 dark:text-rose-300">
                <p className="font-semibold">Ошибка</p>
                <p className="mt-1">{selected.error_message ?? "Без описания"}</p>
              </div>
            )}
            {selected.event_type === "LOGIN_SECURITY" ? (
              <div className="space-y-2 rounded-xl border border-line p-3 text-sm">
                <p><span className="text-muted">Событие:</span> {selected.action}</p>
                <p><span className="text-muted">Пользователь:</span> {selected.user_name ?? "—"}</p>
                <p><span className="text-muted">IP:</span> {selected.ip_address ?? "—"}</p>
                <p><span className="text-muted">User-Agent:</span> {selected.user_agent ?? "—"}</p>
                <p><span className="text-muted">Request ID:</span> {selected.request_id ?? "—"}</p>
                <p><span className="text-muted">Данные:</span> {selected.new_value ?? "—"}</p>
              </div>
            ) : (
              <>
                <div><p className="label mb-2">Было</p><pre className="max-h-64 overflow-auto rounded-xl bg-surface2 p-3 text-xs">{selected.old_value ? JSON.stringify(JSON.parse(selected.old_value), null, 2) : "—"}</pre></div>
                <div><p className="label mb-2">Стало</p><pre className="max-h-64 overflow-auto rounded-xl bg-surface2 p-3 text-xs">{selected.new_value ? JSON.stringify(JSON.parse(selected.new_value), null, 2) : "—"}</pre></div>
                <div className="rounded-xl border border-line p-3 text-xs text-muted">
                  <p>IP: {selected.ip_address ?? "—"}</p>
                  <p>User-Agent: {selected.user_agent ?? "—"}</p>
                  <p>Request ID: {selected.request_id ?? "—"}</p>
                </div>
              </>
            )}
          </div>
        )}
      </Drawer>
    </div>
  );
}

export function AdminBackupsPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [restoreOpen, setRestoreOpen] = useState(false);
  const backupsQuery = useQuery({
    queryKey: ["admin-backups"],
    queryFn: () => api.get("/admin/backups").then((response) => response.data),
  });
  const monitoringQuery = useQuery({
    queryKey: ["admin-monitoring"],
    queryFn: () => api.get("/admin/monitoring").then((response) => response.data),
  });
  const createMutation = useMutation({
    mutationFn: () => api.post("/admin/backups"),
    onSuccess: () => {
      toast("Резервная копия обновлена", "success");
      queryClient.invalidateQueries({ queryKey: ["admin-backups"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const verifyMutation = useMutation({
    mutationFn: () => api.post("/admin/backups/verify").then((response) => response.data),
    onSuccess: (data) => toast(data.ok ? `Копия цела · ${data.size} байт` : `Ошибка копии: ${data.error}`, data.ok ? "success" : "error"),
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const testRestoreMutation = useMutation({
    mutationFn: () => api.post("/admin/backups/test-restore").then((response) => response.data),
    onSuccess: (data) => toast(data.ok ? `Тест восстановления: ${data.tables} таблиц, ${data.bookings} броней` : `Ошибка восстановления: ${data.error}`, data.ok ? "success" : "error"),
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const restoreMutation = useMutation({
    mutationFn: () => api.post("/admin/backups/restore"),
    onSuccess: () => {
      toast("База восстановлена", "success");
      setRestoreOpen(false);
      queryClient.invalidateQueries();
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  const data = backupsQuery.data ?? {};
  const file = data.file;
  const settings = data.settings ?? {};
  const summary = monitoringQuery.data?.summary ?? {};
  const tables = monitoringQuery.data?.tables ?? [];
  const enabled = settings["backup.enabled"] !== false;
  const schedule = settings["backup.schedule_time"] ?? "03:00";
  const lastStatus = settings["backup.last_status"] ?? "never";
  const lastError = settings["backup.last_error"];

  return (
    <div>
      <PageHeader
        title="Резервное копирование и мониторинг"
        subtitle="Одна актуальная копия, обновляется по расписанию или вручную."
        actions={
          <>
            <Button variant="secondary" onClick={() => { monitoringQuery.refetch(); backupsQuery.refetch(); }}>
              <RefreshCw size={15} /> Обновить
            </Button>
            <Button variant="secondary" onClick={() => downloadFile(api, "/admin/backups/download", "sunstay_latest.dump")}>
              <Download size={15} /> Скачать копию
            </Button>
            <Button variant="secondary" onClick={() => verifyMutation.mutate()} disabled={verifyMutation.isPending}>
              Проверить копию
            </Button>
            <Button variant="secondary" onClick={() => testRestoreMutation.mutate()} disabled={testRestoreMutation.isPending}>
              Тест восстановления
            </Button>
            <Button onClick={() => createMutation.mutate()} disabled={createMutation.isPending}>
              <DatabaseBackup size={15} /> Создать сейчас
            </Button>
          </>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card><p className="label">Размер БД</p><p className="kpi-value mt-2">{formatNumber((summary.db_size ?? 0) / 1024 / 1024)} МБ</p></Card>
        <Card><p className="label">Активные соединения</p><p className="kpi-value mt-2">{summary.active_connections ?? 0}</p></Card>
        <Card>
          <p className="label">Последняя копия</p>
          <p className="mt-2 text-sm font-semibold">{file ? formatDateTime(file.updated_at) : "—"}</p>
          <p className="mt-1 text-xs text-muted">{file ? `${formatNumber(file.size / 1024)} КБ` : "Копия ещё не создана"}</p>
        </Card>
        <Card>
          <p className="label">Расписание</p>
          <p className="mt-2 text-sm font-semibold">{enabled ? `Ежедневно в ${schedule}` : "Выключено"}</p>
          <p className={`mt-1 text-xs ${lastStatus === "error" ? "text-rose-600" : "text-muted"}`}>
            Статус: {lastStatus === "success" ? "успешно" : lastStatus === "error" ? "ошибка" : "ещё не запускалось"}
          </p>
        </Card>
      </div>

      <div className="mt-5 grid gap-5 xl:grid-cols-[1.2fr_1fr]">
        <Card>
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="font-display text-2xl font-semibold">Актуальная копия</h2>
              <p className="text-sm text-muted">Файл перезаписывается при каждом запуске.</p>
            </div>
            <Badge tone={file ? "success" : "warning"}>{file ? "готова" : "нет копии"}</Badge>
          </div>
          <div className="mt-5 rounded-xl bg-surface2 p-4 text-sm">
            <p className="font-mono text-xs">{file?.filename ?? "sunstay_latest.dump"}</p>
            <p className="mt-2 text-muted">Обновлено: {file ? formatDateTime(file.updated_at) : "—"}</p>
            <p className="text-muted">Размер: {file ? `${formatNumber(file.size / 1024)} КБ` : "—"}</p>
            {lastError && <p className="mt-2 text-rose-600">{lastError}</p>}
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <Button variant="secondary" onClick={() => downloadFile(api, "/admin/backups/download", "sunstay_latest.dump")}>
              <Download size={15} /> Скачать
            </Button>
            <Button variant="danger" onClick={() => setRestoreOpen(true)} disabled={!file}>
              <RefreshCw size={15} /> Восстановить
            </Button>
          </div>
          <p className="mt-4 text-xs leading-5 text-muted">
            Восстановление заменит текущие данные. Используйте только на учебном стенде.
          </p>
        </Card>

        <Card>
          <h2 className="font-display text-2xl font-semibold">Телеметрия инфраструктуры</h2>
          <div className="mt-4 space-y-2">
            {tables.map((table: any) => (
              <div key={table.relname} className="flex items-center justify-between rounded-xl border border-line px-3 py-2 text-sm">
                <span>{table.relname}</span>
                <span className="text-muted">{formatNumber(table.n_live_tup)} строк · {formatNumber(table.size / 1024)} КБ</span>
              </div>
            ))}
          </div>
          {monitoringQuery.isError && <ErrorState message={getErrorMessage(monitoringQuery.error)} />}
        </Card>
      </div>

      <Modal
        open={restoreOpen}
        title="Восстановление базы"
        subtitle={file?.filename ?? ""}
        onClose={() => setRestoreOpen(false)}
        footer={<><Button variant="secondary" onClick={() => setRestoreOpen(false)}>Отмена</Button><Button variant="danger" onClick={() => restoreMutation.mutate()} disabled={restoreMutation.isPending}>Подтвердить восстановление</Button></>}
      >
        <p className="text-sm text-muted">Текущие данные будут заменены содержимым актуальной копии.</p>
      </Modal>
    </div>
  );
}

export function AdminSettingsPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const query = useQuery({ queryKey: ["admin-settings"], queryFn: () => api.get("/admin/settings").then((response) => response.data) });
  const [form, setForm] = useState<Record<string, any>>({});
  useEffect(() => {
    if (!query.data) return;
    const next: Record<string, any> = {};
    for (const row of query.data) next[row.key] = row.value;
    setForm(next);
  }, [query.data]);
  const mutation = useMutation({
    mutationFn: () => api.put("/admin/settings", form),
    onSuccess: () => { toast("Настройки сохранены", "success"); queryClient.invalidateQueries({ queryKey: ["admin-settings"] }); },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const [passwordForm, setPasswordForm] = useState({ old_password: "", new_password: "" });
  const passwordMutation = useMutation({
    mutationFn: () => api.post("/auth/change-password", passwordForm),
    onSuccess: () => { toast("Пароль изменён", "success"); setPasswordForm({ old_password: "", new_password: "" }); },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  if (query.isLoading) return <Spinner />;
  if (query.isError) return <ErrorState message={getErrorMessage(query.error)} />;

  return (
    <div>
      <PageHeader title="Параметры системы" subtitle="Отель, оформление, безопасность и резервное копирование." actions={<Button onClick={() => mutation.mutate()} disabled={mutation.isPending}><Save size={15} /> Сохранить</Button>} />
      <div className="grid gap-5 xl:grid-cols-2">
        <Card className="space-y-4">
          <h2 className="font-display text-2xl font-semibold">1. Отель</h2>
          <Input label="Название" value={form["hotel.name"] ?? ""} onChange={(event) => setForm({ ...form, "hotel.name": event.target.value })} />
          <Input label="Адрес" value={form["hotel.address"] ?? ""} onChange={(event) => setForm({ ...form, "hotel.address": event.target.value })} />
          <Input label="Телефон" value={form["hotel.phone"] ?? ""} onChange={(event) => setForm({ ...form, "hotel.phone": event.target.value })} />
          <Input label="Email" value={form["hotel.email"] ?? ""} onChange={(event) => setForm({ ...form, "hotel.email": event.target.value })} />
        </Card>
        <Card className="space-y-4">
          <h2 className="font-display text-2xl font-semibold">2. Оформление</h2>
          <Select label="Тема по умолчанию" value={form["app.default_theme"] ?? "light"} onChange={(event) => setForm({ ...form, "app.default_theme": event.target.value })}>
            <option value="light">Светлая</option><option value="dark">Тёмная</option><option value="system">Системная</option>
          </Select>
          <Select label="Язык по умолчанию" value={form["app.default_language"] ?? "ru"} onChange={(event) => setForm({ ...form, "app.default_language": event.target.value })}>
            <option value="ru">Русский</option><option value="en">English</option>
          </Select>
        </Card>
        <Card className="space-y-4">
          <h2 className="font-display text-2xl font-semibold">3. Безопасность</h2>
          <Input label="Таймаут сессии, мин" type="number" value={form["security.session_timeout_minutes"] ?? 120} onChange={(event) => setForm({ ...form, "security.session_timeout_minutes": Number(event.target.value) })} />
          <Input label="Максимум попыток входа" type="number" value={form["security.max_login_attempts"] ?? 5} onChange={(event) => setForm({ ...form, "security.max_login_attempts": Number(event.target.value) })} />
          <Input label="Минимальная длина пароля" type="number" value={form["password.min_length"] ?? 8} onChange={(event) => setForm({ ...form, "password.min_length": Number(event.target.value) })} />
          <Select label="Требовать заглавную букву" value={String(form["password.require_uppercase"] ?? true)} onChange={(event) => setForm({ ...form, "password.require_uppercase": event.target.value === "true" })}>
            <option value="true">Да</option><option value="false">Нет</option>
          </Select>
          <Select label="Требовать цифру" value={String(form["password.require_digit"] ?? true)} onChange={(event) => setForm({ ...form, "password.require_digit": event.target.value === "true" })}>
            <option value="true">Да</option><option value="false">Нет</option>
          </Select>
          <Select label="Требовать спецсимвол" value={String(form["password.require_special"] ?? false)} onChange={(event) => setForm({ ...form, "password.require_special": event.target.value === "true" })}>
            <option value="true">Да</option><option value="false">Нет</option>
          </Select>
        </Card>
        <Card className="space-y-3">
          <h2 className="font-display text-2xl font-semibold">Смена пароля</h2>
          <Input label="Текущий пароль" type="password" value={passwordForm.old_password} onChange={(event) => setPasswordForm({ ...passwordForm, old_password: event.target.value })} />
          <Input label="Новый пароль" type="password" value={passwordForm.new_password} onChange={(event) => setPasswordForm({ ...passwordForm, new_password: event.target.value })} />
          <Button onClick={() => passwordMutation.mutate()} disabled={passwordMutation.isPending || !passwordForm.old_password || passwordForm.new_password.length < 8}>Сменить пароль</Button>
        </Card>
        <TwoFactorSetup />
        <Card className="space-y-3">
          <h2 className="font-display text-2xl font-semibold">Функции сайта</h2>
          {[
            ["feature.reviews", "Отзывы"],
            ["feature.waitlist", "Лист ожидания"],
            ["feature.loyalty", "Бонусные баллы"],
            ["feature.special_requests", "Особые пожелания"],
          ].map(([key, label]) => (
            <Select key={key} label={label} value={String(form[key] ?? true)} onChange={(event) => setForm({ ...form, [key]: event.target.value === "true" })}>
              <option value="true">Включено</option>
              <option value="false">Выключено</option>
            </Select>
          ))}
        </Card>
        <Card className="space-y-4">
          <h2 className="font-display text-2xl font-semibold">4. Резервное копирование</h2>
          <Select label="Включено" value={String(form["backup.enabled"] ?? true)} onChange={(event) => setForm({ ...form, "backup.enabled": event.target.value === "true" })}>
            <option value="true">Да</option>
            <option value="false">Нет</option>
          </Select>
          <Input label="Время обновления" type="time" value={form["backup.schedule_time"] ?? "03:00"} onChange={(event) => setForm({ ...form, "backup.schedule_time": event.target.value })} />
          <div className="rounded-xl bg-surface2 p-3 text-xs text-muted">
            <p>Одна копия <span className="font-mono">sunstay_latest.dump</span> перезаписывается при каждом запуске.</p>
            <p className="mt-1">Последний запуск: {form["backup.last_run_at"] ? formatDateTime(form["backup.last_run_at"]) : "—"}</p>
            <p>Статус: {form["backup.last_status"] ?? "never"}</p>
          </div>
          <p className="text-xs text-muted">Создать копию вручную и скачать её можно на странице «Бэкапы».</p>
        </Card>
      </div>
    </div>
  );
}

export function AdminReviewsPage() {
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const query = useQuery({
    queryKey: ["admin-reviews", status, search],
    queryFn: () => api.get("/admin/reviews", { params: { status: status || undefined, search: search || undefined } }).then((response) => response.data),
  });
  const mutation = useMutation({
    mutationFn: ({ id, nextStatus }: { id: number; nextStatus: "APPROVED" | "REJECTED" }) =>
      api.patch(`/admin/reviews/${id}`, { status: nextStatus }),
    onSuccess: () => {
      toast("Статус отзыва обновлён", "success");
      queryClient.invalidateQueries({ queryKey: ["admin-reviews"] });
      queryClient.invalidateQueries({ queryKey: ["public-reviews"] });
      queryClient.invalidateQueries({ queryKey: ["public-rating"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  const reviews = query.data ?? [];
  return (
    <div className="space-y-5">
      <PageHeader title="Отзывы гостей" subtitle="Модерация отзывов после проживания." />
      <Card className="flex flex-wrap items-end gap-3">
        <Select label="Статус" value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="">Все</option>
          <option value="PENDING">На модерации</option>
          <option value="APPROVED">Опубликованные</option>
          <option value="REJECTED">Отклонённые</option>
        </Select>
        <div className="min-w-64 flex-1">
          <Input label="Поиск" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Гость, заголовок или текст" />
        </div>
        <Button variant="secondary" onClick={() => query.refetch()}><RefreshCw size={15} /> Обновить</Button>
      </Card>
      {query.isLoading && <Spinner />}
      {query.isError && <ErrorState message={getErrorMessage(query.error)} />}
      {!query.isLoading && !reviews.length && <EmptyState title="Отзывов нет" description="Здесь появятся отзывы гостей после выезда." />}
      <div className="space-y-3">
        {reviews.map((review: any) => (
          <Card key={review.review_id}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <div className="flex text-amber">
                    {[1, 2, 3, 4, 5].map((value) => <Star key={value} size={15} className={value <= review.rating ? "fill-current" : "opacity-25"} />)}
                  </div>
                  <Badge tone={review.status === "APPROVED" ? "success" : review.status === "REJECTED" ? "danger" : "warning"}>
                    {review.status === "APPROVED" ? "Опубликован" : review.status === "REJECTED" ? "Отклонён" : "На модерации"}
                  </Badge>
                </div>
                <h3 className="mt-2 font-display text-xl font-semibold">{review.title || "Без заголовка"}</h3>
                <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">{review.body}</p>
                <p className="mt-3 text-xs text-muted">{review.guest_name} · {review.room_type}, №{review.room_number} · {formatDate(review.checkin_date)} — {formatDate(review.checkout_date)}</p>
              </div>
              <div className="flex gap-2">
                {review.status !== "APPROVED" && <Button size="sm" onClick={() => mutation.mutate({ id: review.review_id, nextStatus: "APPROVED" })} disabled={mutation.isPending}><Check size={14} /> Опубликовать</Button>}
                {review.status !== "REJECTED" && <Button size="sm" variant="secondary" onClick={() => mutation.mutate({ id: review.review_id, nextStatus: "REJECTED" })} disabled={mutation.isPending}><X size={14} /> Отклонить</Button>}
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

export function AdminSessionsPage() {
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const query = useQuery({
    queryKey: ["admin-sessions"],
    queryFn: () => api.get("/admin/sessions").then((response) => response.data),
  });
  const revoke = useMutation({
    mutationFn: (id: number) => api.post(`/admin/sessions/${id}/revoke`),
    onSuccess: () => { toast("Сессия отозвана", "success"); queryClient.invalidateQueries({ queryKey: ["admin-sessions"] }); },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  if (query.isLoading) return <Spinner />;
  if (query.isError) return <ErrorState message={getErrorMessage(query.error)} />;
  const rows = query.data ?? [];
  return (
    <div className="space-y-4">
      <PageHeader title="Сессии пользователей" subtitle="Активные и отозванные refresh-сессии." />
      <div className="table-wrap">
        <table className="table-base">
          <thead><tr><th>Пользователь</th><th>Роль</th><th>IP</th><th>Создана</th><th>Истекает</th><th>Статус</th><th /></tr></thead>
          <tbody>
            {rows.map((row: any) => (
              <tr key={row.session_id}>
                <td><p className="font-semibold">{row.full_name}</p><p className="text-xs text-muted">{row.email}</p></td>
                <td>{row.role_name}</td>
                <td>{row.ip_address || "—"}</td>
                <td>{formatDateTime(row.created_at)}</td>
                <td>{formatDateTime(row.expires_at)}</td>
                <td>{row.revoked_at ? <Badge tone="danger">Отозвана</Badge> : <Badge tone="success">Активна</Badge>}</td>
                <td>{!row.revoked_at && <Button size="sm" variant="secondary" onClick={() => revoke.mutate(row.session_id)} disabled={revoke.isPending}>Отозвать</Button>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
