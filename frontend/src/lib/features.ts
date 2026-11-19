import { useQuery } from "@tanstack/react-query";
import { api } from "./api";

export function useFeatures() {
  const query = useQuery({
    queryKey: ["public-config"],
    queryFn: () => api.get("/public/config").then((response) => response.data),
    staleTime: 120000,
  });
  const flags = query.data?.features ?? {};
  return {
    reviews: flags.reviews !== false,
    waitlist: flags.waitlist !== false,
    loyalty: flags.loyalty !== false,
    special_requests: flags.special_requests !== false,
  };
}
