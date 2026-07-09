import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import apiClient from "./client";

export function useLoans({ enabled = true, archived = false } = {}) {
  return useQuery({
    queryKey: archived ? ["loans", "archived"] : ["loans"],
    queryFn: async () => {
      const { data } = await apiClient.get("loans/", {
        params: archived ? { archived: "true" } : undefined,
      });
      return data;
    },
    enabled,
  });
}

export function useLoan(id, { enabled = true } = {}) {
  return useQuery({
    queryKey: ["loans", id],
    queryFn: async () => {
      const { data } = await apiClient.get(`loans/${id}/`);
      return data;
    },
    enabled,
    retry: (failureCount, error) => error?.response?.status !== 404 && failureCount < 3,
  });
}

export function useLoanableEquipment({ enabled = true } = {}) {
  return useQuery({
    queryKey: ["loanableEquipment"],
    queryFn: async () => {
      const { data } = await apiClient.get("loans/loanable-equipment/");
      return data;
    },
    enabled,
  });
}

export function useCreateLoan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (loan) => {
      const { data } = await apiClient.post("loans/", loan);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["loanableEquipment"] });
      queryClient.invalidateQueries({ queryKey: ["loans"] });
    },
  });
}

export function useReturnLoan() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ loanId, items }) => {
      const { data } = await apiClient.post(`loans/${loanId}/return/`, { items });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["loanableEquipment"] });
      queryClient.invalidateQueries({ queryKey: ["loans"] });
    },
  });
}
