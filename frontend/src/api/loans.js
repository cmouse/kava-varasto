import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import apiClient from "./client";

export function useLoans({ enabled = true } = {}) {
  return useQuery({
    queryKey: ["loans"],
    queryFn: async () => {
      const { data } = await apiClient.get("loans/");
      return data;
    },
    enabled,
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
