import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import apiClient from "./client";
import { clearLoanDraft } from "../utils/loanDraft";

export function useCurrentUser() {
  return useQuery({
    queryKey: ["currentUser"],
    queryFn: async () => {
      const { data } = await apiClient.get("accounts/me/");
      return data;
    },
  });
}

export function useLogin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ username, password }) => {
      const { data } = await apiClient.post("accounts/login/", { username, password });
      return data;
    },
    // A shared browser must not hand the next signed-in user the previous
    // one's in-progress loan draft -- borrower_name/borrower_phone is
    // third-party personal data. Clearing here is cheaper than namespacing
    // the draft's storage key per user.
    onSuccess: (data) => {
      clearLoanDraft();
      queryClient.setQueryData(["currentUser"], data);
    },
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      await apiClient.post("accounts/logout/");
    },
    onSuccess: () => {
      clearLoanDraft();
      queryClient.setQueryData(["currentUser"], { authenticated: false, user: null });
    },
  });
}

export function useChangePassword() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ current_password, new_password }) => {
      const { data } = await apiClient.post("accounts/change-password/", { current_password, new_password });
      return data;
    },
    onSuccess: (data) => queryClient.setQueryData(["currentUser"], data),
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (profile) => {
      const { data } = await apiClient.patch("accounts/profile/", profile);
      return data;
    },
    onSuccess: (data) => queryClient.setQueryData(["currentUser"], data),
  });
}
