import { useEffect } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { ACCESS_KEY } from "./api";

export function useRealtime(enabled: boolean) {
  const queryClient = useQueryClient();
  useEffect(() => {
    if (!enabled) return;
    const token = localStorage.getItem(ACCESS_KEY);
    if (!token) return;
    const source = new EventSource(`/api/manager/events?token=${encodeURIComponent(token)}`);
    source.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type && message.type !== "connected") {
          queryClient.invalidateQueries();
        }
      } catch {
        /* ignore */
      }
    };
    return () => source.close();
  }, [enabled, queryClient]);
}
