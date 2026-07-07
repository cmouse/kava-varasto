import { useQuery } from "@tanstack/react-query";

import apiClient from "./client";

export function useEquipmentList({ enabled = true } = {}) {
  return useQuery({
    queryKey: ["equipment"],
    queryFn: async () => {
      const { data } = await apiClient.get("inventory/equipment/");
      return data;
    },
    enabled,
  });
}
