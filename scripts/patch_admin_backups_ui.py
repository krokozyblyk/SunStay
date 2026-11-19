from pathlib import Path

PATH = Path(r"C:\pract\Kursovaya1,4kurs\frontend\src\pages\AdminPages.tsx")
text = PATH.read_text(encoding="utf-8")
start = text.find("export function AdminBackupsPage()")
end = text.find("export function AdminSettingsPage()")
if start < 0 or end < 0:
    raise SystemExit("AdminBackupsPage not found")

new_func = '''export function AdminBackupsPage() {
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

'''

text = text[:start] + new_func + text[end:]
PATH.write_text(text, encoding="utf-8")
print("AdminBackupsPage replaced")
