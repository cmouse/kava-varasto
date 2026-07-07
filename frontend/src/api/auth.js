import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import apiClient from "./client";

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
    onSuccess: (data) => queryClient.setQueryData(["currentUser"], data),
  });
}

export function useLogout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      await apiClient.post("accounts/logout/");
    },
    onSuccess: () => queryClient.setQueryData(["currentUser"], { authenticated: false, user: null }),
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
