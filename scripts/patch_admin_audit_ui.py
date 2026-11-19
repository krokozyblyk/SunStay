from pathlib import Path

PATH = Path(r"C:\pract\Kursovaya1,4kurs\frontend\src\pages\AdminPages.tsx")
text = PATH.read_text(encoding="utf-8")
start = text.find("export function AdminAuditPage()")
end = text.find("export function AdminBackupsPage()")
if start < 0 or end < 0:
    raise SystemExit("AdminAuditPage not found")

new_func = '''export function AdminAuditPage() {
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

'''

text = text[:start] + new_func + text[end:]
PATH.write_text(text, encoding="utf-8")
print("AdminAuditPage replaced")
