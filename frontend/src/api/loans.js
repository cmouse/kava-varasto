import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import apiClient from "./client";

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
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["loanableEquipment"] }),
  });
}
