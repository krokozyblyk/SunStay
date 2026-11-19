import { useEffect, useState } from "react";
import QRCode from "qrcode";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, getErrorMessage } from "../lib/api";
import { Button, Card, Input } from "./ui";
import { useToast } from "./ui";

export function TwoFactorSetup() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [secret, setSecret] = useState("");
  const [qr, setQr] = useState("");
  const [code, setCode] = useState("");
  const [recovery, setRecovery] = useState<string[]>([]);
  const [disableCode, setDisableCode] = useState("");

  const statusQuery = useQuery({
    queryKey: ["2fa-status"],
    queryFn: () => api.get("/auth/2fa/status").then((response) => response.data),
  });
  const setupRequested = Boolean(statusQuery.data?.setup_requested || statusQuery.data?.has_secret);

  const refresh = () => queryClient.invalidateQueries({ queryKey: ["2fa-status"] });

  useEffect(() => {
    if (!secret) return;
    const uri = `otpauth://totp/SunStay?secret=${encodeURIComponent(secret)}&issuer=SunStay&algorithm=SHA1&digits=6&period=30`;
    QRCode.toDataURL(uri, { width: 180, margin: 1 }).then(setQr).catch(() => {});
  }, [secret]);

  const setup = useMutation({
    mutationFn: () => api.post("/auth/2fa/setup").then((response) => response.data),
    onSuccess: (data) => {
      setSecret(data.secret);
      refresh();
      toast("Секрет создан. Отсканируйте QR-код.", "success");
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const enable = useMutation({
    mutationFn: () => api.post("/auth/2fa/enable", { code }).then((response) => response.data),
    onSuccess: (data) => {
      setRecovery(data.recovery_codes ?? []);
      refresh();
      toast("2FA включена", "success");
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });
  const disable = useMutation({
    mutationFn: () => api.post("/auth/2fa/disable-with-code", { code: disableCode }),
    onSuccess: () => {
      setSecret("");
      setQr("");
      setRecovery([]);
      setDisableCode("");
      refresh();
      toast("2FA отключена", "success");
    },
    onError: (error) => toast(getErrorMessage(error), "error"),
  });

  return (
    <Card className="space-y-3">
      <h2 className="font-display text-2xl font-semibold">Двухфакторная аутентификация</h2>
      <p className="text-sm text-muted">
        {statusQuery.data?.enabled
          ? "2FA включена. Для отключения введите код из приложения."
          : "Подключите SunStay в Google Authenticator или другом приложении."}
      </p>
      {!setupRequested && (
        <Button variant="secondary" onClick={() => setup.mutate()} disabled={setup.isPending}>
          Создать секрет
        </Button>
      )}
      {qr && (
        <div className="flex flex-wrap items-center gap-4 rounded-xl bg-surface2 p-3">
          <img src={qr} alt="QR-код 2FA" className="h-[180px] w-[180px] rounded-lg bg-white" />
          <div className="space-y-2">
            <p className="break-all font-mono text-xs text-muted">{secret}</p>
            <Input label="Код из приложения" value={code} onChange={(event) => setCode(event.target.value)} placeholder="123456" />
            <Button onClick={() => enable.mutate()} disabled={enable.isPending || code.length !== 6}>Включить 2FA</Button>
          </div>
        </div>
      )}
      {recovery.length > 0 && (
        <div className="rounded-xl border border-line p-3 text-xs">
          <p className="font-semibold">Резервные коды (сохраните):</p>
          <div className="mt-2 grid grid-cols-2 gap-1 font-mono">{recovery.map((item) => <span key={item}>{item}</span>)}</div>
        </div>
      )}
      {setupRequested && (
        <div className="rounded-xl border border-line p-3">
          <p className="text-sm font-semibold">Отключить 2FA</p>
          <div className="mt-2 flex gap-2">
            <Input label="Код из приложения" value={disableCode} onChange={(event) => setDisableCode(event.target.value)} placeholder="123456" />
            <Button variant="danger" className="mt-6" onClick={() => disable.mutate()} disabled={disable.isPending || disableCode.length !== 6}>Отключить</Button>
          </div>
        </div>
      )}
    </Card>
  );
}
