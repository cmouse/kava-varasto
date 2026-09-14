import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import apiClient from "./client";

// Enabled only once the caller knows the session is authenticated and not
// mid forced-password-change -- the endpoint is IsAuthenticatedAndPasswordCurrent,
// same as the dialog's own render gate, so an unconditional query would 403
// on every login screen load.
export function useWhatsNew(enabled) {
  return useQuery({
    queryKey: ["whatsNew"],
    queryFn: async () => {
      const { data } = await apiClient.get("accounts/whats-new/");
      return data;
    },
    enabled,
  });
}

export function useAckWhatsNew() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data } = await apiClient.post("accounts/whats-new/");
      return data;
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["currentUser"], data);
      queryClient.setQueryData(["whatsNew"], (previous) =>
        previous ? { ...previous, unseen: false } : previous,
      );
    },
  });
}
