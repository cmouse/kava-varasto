import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import apiClient from "./client";

export function useRepairs({ enabled = true, includeArchived = false } = {}) {
  return useQuery({
    queryKey: includeArchived ? ["repairs", "all"] : ["repairs"],
    queryFn: async () => {
      // The queue shows what was resolved within the past year, so finishing
      // a repair doesn't make it vanish from under the person who finished
      // it. Only the toggle reaches further back than that.
      const { data } = await apiClient.get("repairs/", {
        params: includeArchived ? { status: "all" } : { resolved: "recent" },
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
