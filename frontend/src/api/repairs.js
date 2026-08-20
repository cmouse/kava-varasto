import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import apiClient from "./client";

export function useRepairs({ enabled = true, includeClosed = false } = {}) {
  return useQuery({
    queryKey: includeClosed ? ["repairs", "recent"] : ["repairs"],
    queryFn: async () => {
      // "recent", not "all": the server drops tickets resolved over a year
      // ago, so the toggle stays readable as history piles up.
      const { data } = await apiClient.get("repairs/", {
        params: includeClosed ? { resolved: "recent" } : undefined,
      });
      return data;
    },
    enabled,
    // Toggling "show resolved" switches to a query key that has never been
    // fetched. Without this the hook reports isLoading, the page unmounts,
    // and a half-filled report form loses its state mid-typing.
    placeholderData: keepPreviousData,
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
