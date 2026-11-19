import {
  AlertTriangle,
  Check,
  ClipboardList,
  Package,
  Play,
  Plus,
  Sparkles,
  Wrench,
  X,
} from "lucide-react";
import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, getErrorMessage } from "../lib/api";
import { useToast } from "../components/ui";
import {
  Badge,
  Button,
  Card,
  Drawer,
  EmptyState,
  ErrorState,
  Input,
  Modal,
  PageHeader,
  Select,
  Spinner,
  StatusPill,
  Tabs,
  Textarea,
} from "../components/ui";
import {
  formatDateTime,
  formatNumber,
  MAINTENANCE_STATUS_LABELS,
  PRIORITY_LABELS,
  statusLabel,
  TASK_STATUS_LABELS,
  TASK_TYPE_LABELS,
} from "../lib/utils";

const TASK_COLUMNS = [
  { status: "ASSIGNED", label: "Назначено", tone: "bg-amber-500/10" },
  { status: "IN_PROGRESS", label: "В работе", tone: "bg-sky-500/10" },
  { status: "DONE", label: "Выполнено", tone: "bg-emerald-500/10" },
  { status: "CANCELLED", label: "Отменено", tone: "bg-surface2" },
];

export function HousekeepingBoardPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [floor, setFloor] = useState("all");
  const [assignee, setAssignee] = useState("all");
  const [newOpen, setNewOpen] = useState(false);
  const [newForm, setNewForm] = useState({ room_id: "", staff_id: "", task_type: "DAILY", priority: "NORMAL" });
  const [selectedTask, setSelectedTask] = useState<any>(null);
  const [writeOffOpen, setWriteOffOpen] = useState(false);
  const [writeOffForm, setWriteOffForm] = useState({ consumable_id: "", quantity: 1 });

  const tasksQuery = useQuery({
    queryKey: ["housekeeping-tasks", floor, assignee],
    queryFn: () => api.get("/housekeeping/tasks", { params: { floor: floor === "all" ? undefined : floor, assignee_id: assignee === "all" ? undefined : assignee } }).then((response) => response.data),
  });
  const staffQuery = useQuery({ queryKey: ["housekeeping-staff"], queryFn: () => api.get("/housekeeping/staff").then((response) => response.data) });
  const roomsQuery = useQuery({ queryKey: ["housekeeping-rooms"], queryFn: () => api.get("/housekeeping/rooms").then((response) => response.data) });
  const consumablesQuery = useQuery({ queryKey: ["housekeeping-consumables"], queryFn: () => api.get("/housekeeping/consumables").then((response) => response.data) });

  const actionMutation = useMutation({
    mutationFn: async ({ taskId, action }: { taskId: number; action: string }) => {
      if (action === "start") {
        await api.post(`/housekeeping/tasks/${taskId}/start`);
        return;
      }
      if (action === "complete") {
        await api.post(`/housekeeping/tasks/${taskId}/complete`);
        return;
      }
      if (action === "cancel") {
        await api.post(`/housekeeping/tasks/${taskId}/cancel`);
      }
    },
    onSuccess: () => {
      toast("Задание обновлено", "success");
      setSelectedTask(null);
      queryClient.invalidateQueries({ queryKey: ["housekeeping-tasks"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  const createMutation = useMutation({
    mutationFn: () => api.post("/housekeeping/tasks", {
      room_id: Number(newForm.room_id),
      staff_id: newForm.staff_id ? Number(newForm.staff_id) : null,
      task_type: newForm.task_type,
      priority: newForm.priority,
    }),
    onSuccess: () => {
      toast("Задание создано", "success");
      setNewOpen(false);
      setNewForm({ room_id: "", staff_id: "", task_type: "DAILY", priority: "NORMAL" });
      queryClient.invalidateQueries({ queryKey: ["housekeeping-tasks"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  const writeOffMutation = useMutation({
    mutationFn: () => api.post(`/housekeeping/tasks/${selectedTask?.task_id}/consumables`, {
      consumable_id: Number(writeOffForm.consumable_id),
      quantity: Number(writeOffForm.quantity),
    }),
    onSuccess: () => {
      toast("Расходник списан", "success");
      setWriteOffOpen(false);
      setWriteOffForm({ consumable_id: "", quantity: 1 });
      queryClient.invalidateQueries({ queryKey: ["housekeeping-tasks"] });
      queryClient.invalidateQueries({ queryKey: ["housekeeping-consumables"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  const tasks = tasksQuery.data ?? [];
  const grouped = useMemo(() => {
    const map: Record<string, any[]> = {};
    for (const column of TASK_COLUMNS) map[column.status] = [];
    for (const task of tasks) (map[task.status] ??= []).push(task);
    return map;
  }, [tasks]);

  return (
    <div>
      <PageHeader
        title="Доска хаускипинга"
        subtitle="Задания на уборку, статусы номеров и списание расходников."
        actions={<Button onClick={() => setNewOpen(true)}><Plus size={15} /> Новое задание</Button>}
      />
      <Card className="mb-4 flex flex-wrap items-end gap-2">
        <Select label="Этаж" value={floor} onChange={(event) => setFloor(event.target.value)}>
          <option value="all">Все этажи</option>
          <option value="1">1 этаж</option>
          <option value="2">2 этаж</option>
          <option value="3">3 этаж</option>
        </Select>
        <Select label="Исполнитель" value={assignee} onChange={(event) => setAssignee(event.target.value)}>
          <option value="all">Все</option>
          {(staffQuery.data ?? []).map((member: any) => <option key={member.user_id} value={member.user_id}>{member.full_name}</option>)}
        </Select>
        <Button variant="ghost" onClick={() => { setFloor("all"); setAssignee("all"); }}>Сбросить</Button>
      </Card>
      {tasksQuery.isLoading && <Spinner />}
      {tasksQuery.isError && <ErrorState message={getErrorMessage(tasksQuery.error)} />}
      {!tasksQuery.isLoading && !tasksQuery.isError && (
        <div className="grid gap-4 xl:grid-cols-4">
          {TASK_COLUMNS.map((column) => (
            <div key={column.status} className="rounded-2xl border border-line bg-surface2 p-3">
              <div className="mb-3 flex items-center justify-between">
                <p className="text-sm font-bold">{column.label}</p>
                <span className="badge bg-surface text-muted">{grouped[column.status]?.length ?? 0}</span>
              </div>
              <div className="space-y-2">
                {(grouped[column.status] ?? []).map((task: any) => (
                  <button key={task.task_id} className="w-full rounded-xl border border-line bg-surface p-3 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-soft" onClick={() => setSelectedTask(task)}>
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="font-semibold text-ink">№{task.room_number} · {TASK_TYPE_LABELS[task.task_type] ?? task.task_type}</p>
                        <p className="mt-1 text-xs text-muted">{task.assignee_name ?? "Не назначен"} · {formatDateTime(task.assigned_at)}</p>
                      </div>
                      <Badge tone={task.priority === "URGENT" || task.priority === "HIGH" ? "danger" : "neutral"}>{PRIORITY_LABELS[task.priority] ?? task.priority}</Badge>
                    </div>
                    <div className="mt-3 flex items-center justify-between">
                      <StatusPill status={task.status} />
                      <span className="text-xs text-muted">{statusLabel(task.room_status)}</span>
                    </div>
                  </button>
                ))}
                {!grouped[column.status]?.length && <p className="px-2 py-6 text-center text-xs text-muted">Пусто</p>}
              </div>
            </div>
          ))}
        </div>
      )}

      <Drawer
        open={Boolean(selectedTask)}
        title={selectedTask ? `Задание #${selectedTask.task_id}` : "Задание"}
        subtitle={selectedTask ? `Номер ${selectedTask.room_number} · ${selectedTask.room_type}` : ""}
        onClose={() => setSelectedTask(null)}
        footer={selectedTask && (
          <div className="flex flex-wrap justify-end gap-2">
            {selectedTask.status === "ASSIGNED" && <Button size="sm" onClick={() => actionMutation.mutate({ taskId: selectedTask.task_id, action: "start" })}><Play size={14} /> Начать</Button>}
            {["ASSIGNED", "IN_PROGRESS"].includes(selectedTask.status) && <Button size="sm" onClick={() => actionMutation.mutate({ taskId: selectedTask.task_id, action: "complete" })}><Check size={14} /> Завершить</Button>}
            {["ASSIGNED", "IN_PROGRESS"].includes(selectedTask.status) && <Button size="sm" variant="ghost" onClick={() => actionMutation.mutate({ taskId: selectedTask.task_id, action: "cancel" })}><X size={14} /> Отменить</Button>}
            <Button size="sm" variant="secondary" onClick={() => setWriteOffOpen(true)}><Package size={14} /> Списать расходники</Button>
          </div>
        )}
      >
        {selectedTask && (
          <div className="space-y-4">
            <div className="rounded-2xl bg-surface2 p-4 text-sm">
              <div className="flex justify-between"><span className="text-muted">Статус</span><StatusPill status={selectedTask.status} /></div>
              <div className="mt-2 flex justify-between"><span className="text-muted">Тип</span><span>{TASK_TYPE_LABELS[selectedTask.task_type] ?? selectedTask.task_type}</span></div>
              <div className="mt-2 flex justify-between"><span className="text-muted">Приоритет</span><span>{PRIORITY_LABELS[selectedTask.priority] ?? selectedTask.priority}</span></div>
              <div className="mt-2 flex justify-between"><span className="text-muted">Назначено</span><span>{formatDateTime(selectedTask.assigned_at)}</span></div>
              {selectedTask.completed_at && <div className="mt-2 flex justify-between"><span className="text-muted">Завершено</span><span>{formatDateTime(selectedTask.completed_at)}</span></div>}
            </div>
            <div>
              <p className="label mb-2">Чек-лист</p>
              <div className="space-y-2 text-sm text-muted">
                <label className="flex items-center gap-2"><input type="checkbox" className="h-4 w-4 accent-terracotta" /> Проверить чистоту номера</label>
                <label className="flex items-center gap-2"><input type="checkbox" className="h-4 w-4 accent-terracotta" /> Заменить бельё и полотенца</label>
                <label className="flex items-center gap-2"><input type="checkbox" className="h-4 w-4 accent-terracotta" /> Пополнить расходники</label>
                <label className="flex items-center gap-2"><input type="checkbox" className="h-4 w-4 accent-terracotta" /> Проверить технику</label>
              </div>
            </div>
          </div>
        )}
      </Drawer>

      <Modal open={newOpen} title="Новое задание" onClose={() => setNewOpen(false)} footer={<><Button variant="secondary" onClick={() => setNewOpen(false)}>Отмена</Button><Button onClick={() => createMutation.mutate()} disabled={createMutation.isPending || !newForm.room_id}>Создать</Button></>}>
        <div className="space-y-3">
          <Select label="Номер" value={newForm.room_id} onChange={(event) => setNewForm({ ...newForm, room_id: event.target.value })}>
            <option value="">Выберите номер</option>
            {(roomsQuery.data ?? []).map((room: any) => <option key={room.room_id} value={room.room_id}>№{room.room_number} · {room.room_type} · {room.status}</option>)}
          </Select>
          <Select label="Исполнитель" value={newForm.staff_id} onChange={(event) => setNewForm({ ...newForm, staff_id: event.target.value })}>
            <option value="">Не назначен</option>
            {(staffQuery.data ?? []).map((member: any) => <option key={member.user_id} value={member.user_id}>{member.full_name}</option>)}
          </Select>
          <Select label="Тип задания" value={newForm.task_type} onChange={(event) => setNewForm({ ...newForm, task_type: event.target.value })}>
            <option value="DAILY">Ежедневная уборка</option>
            <option value="POST_CHECKOUT">После выезда</option>
            <option value="ON_REQUEST">По запросу</option>
          </Select>
          <Select label="Приоритет" value={newForm.priority} onChange={(event) => setNewForm({ ...newForm, priority: event.target.value })}>
            <option value="LOW">Низкий</option><option value="NORMAL">Обычный</option><option value="HIGH">Высокий</option><option value="URGENT">Срочный</option>
          </Select>
        </div>
      </Modal>

      <Modal open={writeOffOpen} title="Списание расходников" subtitle={selectedTask ? `Задание #${selectedTask.task_id}` : ""} onClose={() => setWriteOffOpen(false)} footer={<><Button variant="secondary" onClick={() => setWriteOffOpen(false)}>Отмена</Button><Button onClick={() => writeOffMutation.mutate()} disabled={writeOffMutation.isPending || !writeOffForm.consumable_id}>Подтвердить списание</Button></>}>
        <div className="space-y-3">
          <Select label="Материал" value={writeOffForm.consumable_id} onChange={(event) => setWriteOffForm({ ...writeOffForm, consumable_id: event.target.value })}>
            <option value="">Выберите материал</option>
            {(consumablesQuery.data ?? []).map((item: any) => <option key={item.consumable_id} value={item.consumable_id}>{item.name} · остаток {formatNumber(item.stock_quantity)} {item.unit}</option>)}
          </Select>
          <Input label="Количество" type="number" min={0.1} step={0.1} value={writeOffForm.quantity} onChange={(event) => setWriteOffForm({ ...writeOffForm, quantity: Number(event.target.value) })} />
        </div>
      </Modal>
    </div>
  );
}

export function MaintenancePage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState("OPEN");
  const [newOpen, setNewOpen] = useState(false);
  const [form, setForm] = useState({ room_id: "", description: "", priority: "NORMAL", assigned_to: "" });
  const query = useQuery({ queryKey: ["maintenance", tab], queryFn: () => api.get("/housekeeping/maintenance", { params: { status: tab === "all" ? undefined : tab } }).then((response) => response.data) });
  const roomsQuery = useQuery({ queryKey: ["housekeeping-rooms"], queryFn: () => api.get("/housekeeping/rooms").then((response) => response.data) });
  const staffQuery = useQuery({ queryKey: ["housekeeping-staff"], queryFn: () => api.get("/housekeeping/staff").then((response) => response.data) });

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) => api.patch(`/housekeeping/maintenance/${id}/status`, { status }),
    onSuccess: () => { toast("Статус заявки обновлён", "success"); queryClient.invalidateQueries({ queryKey: ["maintenance"] }); },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const createMutation = useMutation({
    mutationFn: () => api.post("/housekeeping/maintenance", {
      room_id: Number(form.room_id),
      description: form.description,
      priority: form.priority,
      assigned_to: form.assigned_to ? Number(form.assigned_to) : null,
    }),
    onSuccess: () => {
      toast("Заявка создана", "success");
      setNewOpen(false);
      setForm({ room_id: "", description: "", priority: "NORMAL", assigned_to: "" });
      queryClient.invalidateQueries({ queryKey: ["maintenance"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  return (
    <div>
      <PageHeader title="Заявки на техобслуживание" subtitle="Неисправности номеров, приоритеты и назначение исполнителей." actions={<Button onClick={() => setNewOpen(true)}><Plus size={15} /> Новая заявка</Button>} />
      <Tabs className="mb-4" value={tab} onChange={setTab} items={[
        { value: "all", label: "Все" },
        { value: "OPEN", label: "Открытые" },
        { value: "IN_PROGRESS", label: "В работе" },
        { value: "DONE", label: "Выполненные" },
        { value: "CANCELLED", label: "Отменённые" },
      ]} />
      {query.isLoading && <Spinner />}
      {query.isError && <ErrorState message={getErrorMessage(query.error)} />}
      {!query.isLoading && !query.isError && (
        <div className="table-wrap">
          <table className="table-base">
            <thead><tr><th>Номер</th><th>Проблема</th><th>Приоритет</th><th>Статус</th><th>Исполнитель</th><th>Создана</th><th /></tr></thead>
            <tbody>
              {(query.data ?? []).map((request: any) => (
                <tr key={request.request_id}>
                  <td className="font-semibold">№{request.room_number}<p className="text-xs text-muted">{request.floor} этаж</p></td>
                  <td className="max-w-[320px]">{request.description}</td>
                  <td><Badge tone={request.priority === "URGENT" || request.priority === "HIGH" ? "danger" : "neutral"}>{PRIORITY_LABELS[request.priority] ?? request.priority}</Badge></td>
                  <td><div className="flex flex-wrap items-center gap-1"><StatusPill status={request.status} />{["OPEN", "IN_PROGRESS"].includes(request.status) && Date.now() - new Date(request.created_at).getTime() > 24 * 60 * 60 * 1000 && <Badge tone="danger">Просрочено</Badge>}</div></td>
                  <td>{request.assignee_name ?? "—"}</td>
                  <td>{formatDateTime(request.created_at)}</td>
                  <td className="text-right">
                    <div className="flex justify-end gap-1">
                      {request.status === "OPEN" && <Button variant="ghost" size="sm" onClick={() => statusMutation.mutate({ id: request.request_id, status: "IN_PROGRESS" })}><Play size={14} /> В работу</Button>}
                      {["OPEN", "IN_PROGRESS"].includes(request.status) && <Button variant="ghost" size="sm" onClick={() => statusMutation.mutate({ id: request.request_id, status: "DONE" })}><Check size={14} /> Завершить</Button>}
                      {["OPEN", "IN_PROGRESS"].includes(request.status) && <Button variant="ghost" size="sm" onClick={() => statusMutation.mutate({ id: request.request_id, status: "CANCELLED" })}><X size={14} /> Отменить</Button>}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!(query.data ?? []).length && <EmptyState title="Заявок нет" />}
        </div>
      )}
      <Modal open={newOpen} title="Новая заявка на ремонт" onClose={() => setNewOpen(false)} footer={<><Button variant="secondary" onClick={() => setNewOpen(false)}>Отмена</Button><Button onClick={() => createMutation.mutate()} disabled={createMutation.isPending || !form.room_id || !form.description}>Создать заявку</Button></>}>
        <div className="space-y-3">
          <Select label="Номер" value={form.room_id} onChange={(event) => setForm({ ...form, room_id: event.target.value })}>
            <option value="">Выберите номер</option>
            {(roomsQuery.data ?? []).map((room: any) => <option key={room.room_id} value={room.room_id}>№{room.room_number} · {room.room_type}</option>)}
          </Select>
          <Textarea label="Описание" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} placeholder="Что случилось?" />
          <Select label="Приоритет" value={form.priority} onChange={(event) => setForm({ ...form, priority: event.target.value })}>
            <option value="LOW">Низкий</option><option value="NORMAL">Обычный</option><option value="HIGH">Высокий</option><option value="URGENT">Срочный</option>
          </Select>
          <Select label="Исполнитель" value={form.assigned_to} onChange={(event) => setForm({ ...form, assigned_to: event.target.value })}>
            <option value="">Не назначен</option>
            {(staffQuery.data ?? []).map((member: any) => <option key={member.user_id} value={member.user_id}>{member.full_name}</option>)}
          </Select>
        </div>
      </Modal>
    </div>
  );
}

export function ConsumablesPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [writeOffOpen, setWriteOffOpen] = useState(false);
  const [form, setForm] = useState({ task_id: "", consumable_id: "", quantity: 1 });
  const consumablesQuery = useQuery({ queryKey: ["housekeeping-consumables"], queryFn: () => api.get("/housekeeping/consumables").then((response) => response.data) });
  const tasksQuery = useQuery({ queryKey: ["housekeeping-tasks"], queryFn: () => api.get("/housekeeping/tasks").then((response) => response.data) });
  const mutation = useMutation({
    mutationFn: () => api.post(`/housekeeping/tasks/${form.task_id}/consumables`, { consumable_id: Number(form.consumable_id), quantity: Number(form.quantity) }),
    onSuccess: () => {
      toast("Расходник списан", "success");
      setWriteOffOpen(false);
      setForm({ task_id: "", consumable_id: "", quantity: 1 });
      queryClient.invalidateQueries({ queryKey: ["housekeeping-consumables"] });
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  return (
    <div>
      <PageHeader title="Расходные материалы" subtitle="Остатки, списания и дефицит по хозяйственным материалам." actions={<Button onClick={() => setWriteOffOpen(true)}><Package size={15} /> Списать</Button>} />
      {consumablesQuery.isLoading && <Spinner />}
      {consumablesQuery.isError && <ErrorState message={getErrorMessage(consumablesQuery.error)} />}
      {!consumablesQuery.isLoading && !consumablesQuery.isError && (
        <div className="table-wrap">
          <table className="table-base">
            <thead><tr><th>Материал</th><th>Ед.</th><th>Остаток</th><th>Минимум</th><th>Использовано</th><th>Дефицит</th><th /></tr></thead>
            <tbody>
              {(consumablesQuery.data ?? []).map((item: any) => {
                const min = Number(item.min_stock || 0);
                const stock = Number(item.stock_quantity || 0);
                const ratio = min > 0 ? stock / min : 1;
                const tone = ratio <= 0.5 ? "danger" : ratio <= 1 ? "warning" : "success";
                const label = ratio <= 0.5 ? "Критично мало" : ratio <= 1 ? "Ниже нормы" : "В норме";
                return (
                  <tr key={item.consumable_id}>
                    <td className="font-medium">{item.name}</td>
                    <td>{item.unit}</td>
                    <td className="font-semibold">{formatNumber(stock)}</td>
                    <td>{formatNumber(min)}</td>
                    <td>{formatNumber(item.used_total)}</td>
                    <td><Badge tone={tone}>{label}</Badge></td>
                    <td className="text-right"><Button variant="ghost" size="sm" onClick={() => { setForm({ ...form, consumable_id: String(item.consumable_id) }); setWriteOffOpen(true); }}>Списать</Button></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      <Modal open={writeOffOpen} title="Списание расходника" onClose={() => setWriteOffOpen(false)} footer={<><Button variant="secondary" onClick={() => setWriteOffOpen(false)}>Отмена</Button><Button onClick={() => mutation.mutate()} disabled={mutation.isPending || !form.task_id || !form.consumable_id}>Подтвердить списание</Button></>}>
        <div className="space-y-3">
          <Select label="Задание" value={form.task_id} onChange={(event) => setForm({ ...form, task_id: event.target.value })}>
            <option value="">Выберите задание</option>
            {(tasksQuery.data ?? []).filter((task: any) => ["ASSIGNED", "IN_PROGRESS"].includes(task.status)).map((task: any) => <option key={task.task_id} value={task.task_id}>#{task.task_id} · №{task.room_number} · {TASK_TYPE_LABELS[task.task_type] ?? task.task_type}</option>)}
          </Select>
          <Select label="Материал" value={form.consumable_id} onChange={(event) => setForm({ ...form, consumable_id: event.target.value })}>
            <option value="">Выберите материал</option>
            {(consumablesQuery.data ?? []).map((item: any) => <option key={item.consumable_id} value={item.consumable_id}>{item.name} · остаток {formatNumber(item.stock_quantity)}</option>)}
          </Select>
          <Input label="Количество" type="number" min={0.1} step={0.1} value={form.quantity} onChange={(event) => setForm({ ...form, quantity: Number(event.target.value) })} />
        </div>
      </Modal>
    </div>
  );
}
