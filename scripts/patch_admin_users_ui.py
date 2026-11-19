from pathlib import Path

PATH = Path(r"C:\pract\Kursovaya1,4kurs\frontend\src\pages\AdminPages.tsx")
text = PATH.read_text(encoding="utf-8")
start = text.find("function UsersTable(")
end = text.find("function PermissionsMatrix(")
if start < 0 or end < 0:
    raise SystemExit("UsersTable not found")

new_func = '''function UsersTable({ mode }: { mode: "admin" | "employees" }) {
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
            <thead><tr><th>Сотрудник</th><th>Роль</th><th>Контакты</th><th>Статус</th><th>Последняя активность</th><th /></tr></thead>
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

'''

text = text[:start] + new_func + text[end:]
PATH.write_text(text, encoding="utf-8")
print("UsersTable replaced")
