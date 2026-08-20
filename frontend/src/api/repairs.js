import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import apiClient from "./client";

export function useRepairs({ enabled = true, includeClosed = false } = {}) {
  return useQuery({
    queryKey: includeClosed ? ["repairs", "all"] : ["repairs"],
    queryFn: async () => {
      const { data } = await apiClient.get("repairs/", {
        params: includeClosed ? { status: "all" } : undefined,
      });
      return data;
    },
    enabled,
  });
}

export function useCreateRepair() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (ticket) => {
      const { data } = await apiClient.post("repairs/", ticket);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["repairs"] });
    },
  });
}

export function useUpdateRepair() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...changes }) => {
      const { data } = await apiClient.patch(`repairs/${id}/`, changes);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["repairs"] });
    },
  });
}

export function useDeleteRepair() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id) => {
      await apiClient.delete(`repairs/${id}/`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["repairs"] });
    },
  });
}
