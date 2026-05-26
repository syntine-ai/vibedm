import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { supabase } from "@/integrations/supabase/client";

import {
  authApi,
  automationApi,
  billingApi,
  contactApi,
  dashboardApi,
  getActiveWorkspace,
  instagramApi,
  workspaceApi,
  type AutomationFilters,
  type ContactFilters,
} from "./resources";
import type {
  AutomationCreate,
  AutomationUpdate,
  BillingCycle,
  ContactCreate,
  ContactUpdate,
  TriggerType,
  WorkspaceSummary,
} from "./types";

export const queryKeys = {
  session: ["auth", "session"] as const,
  authMe: ["auth", "me"] as const,
  workspaces: ["workspaces"] as const,
  workspaceMembers: (workspaceId: string) => ["workspaces", workspaceId, "members"] as const,
  dashboardStats: (workspaceId: string) => ["dashboard", workspaceId, "stats"] as const,
  dashboardActivity: (workspaceId: string) => ["dashboard", workspaceId, "activity"] as const,
  usage: (workspaceId: string) => ["usage", workspaceId] as const,
  automations: (workspaceId: string, filters?: AutomationFilters) =>
    ["automations", workspaceId, filters ?? {}] as const,
  automation: (workspaceId: string, automationId: string) =>
    ["automations", workspaceId, automationId] as const,
  automationRuns: (workspaceId: string, automationId: string) =>
    ["automations", workspaceId, automationId, "runs"] as const,
  contacts: (workspaceId: string, filters?: ContactFilters) =>
    ["contacts", workspaceId, filters ?? {}] as const,
  contact: (workspaceId: string, contactId: string) =>
    ["contacts", workspaceId, contactId] as const,
  billingPlans: ["billing", "plans"] as const,
  billingSubscription: (workspaceId: string) => ["billing", workspaceId, "subscription"] as const,
  billingInvoices: (workspaceId: string) => ["billing", workspaceId, "invoices"] as const,
};

export function useSessionQuery() {
  return useQuery({
    queryKey: queryKeys.session,
    queryFn: async () => {
      const { data, error } = await supabase.auth.getSession();
      if (error) throw error;
      return data.session;
    },
    staleTime: 30_000,
  });
}

export function useAuthMeQuery(enabled = true) {
  return useQuery({
    queryKey: queryKeys.authMe,
    queryFn: authApi.me,
    enabled,
    retry: false,
  });
}

export function useCurrentUser() {
  const sessionQuery = useSessionQuery();
  const meQuery = useAuthMeQuery(Boolean(sessionQuery.data));
  const activeWorkspace = getActiveWorkspace(meQuery.data?.workspaces);
  return { sessionQuery, meQuery, user: meQuery.data?.user, activeWorkspace };
}

export function useActiveWorkspace() {
  const { activeWorkspace, meQuery } = useCurrentUser();
  return { activeWorkspace, workspaces: meQuery.data?.workspaces ?? [], meQuery };
}

export function useInvalidateWorkspaceData() {
  const queryClient = useQueryClient();
  return async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: queryKeys.authMe }),
      queryClient.invalidateQueries({ queryKey: queryKeys.workspaces }),
      queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
      queryClient.invalidateQueries({ queryKey: ["usage"] }),
      queryClient.invalidateQueries({ queryKey: ["billing"] }),
      queryClient.invalidateQueries({ queryKey: ["automations"] }),
      queryClient.invalidateQueries({ queryKey: ["contacts"] }),
    ]);
  };
}

export function useLogoutMutation(onLoggedOut: () => void) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      await authApi.logout().catch(() => undefined);
      await supabase.auth.signOut();
    },
    onSettled: async () => {
      queryClient.clear();
      onLoggedOut();
    },
  });
}

export function useStartInstagramOauth(intent: "onboarding" | "add_workspace") {
  return useMutation({
    mutationFn: async () => {
      const response = await instagramApi.startOauth();
      localStorage.setItem("vibedm.instagram_intent", intent);

      // Open Meta OAuth in a centered popup instead of redirecting the whole page
      const width = 600;
      const height = 700;
      const left = Math.round(window.screenX + (window.outerWidth - width) / 2);
      const top = Math.round(window.screenY + (window.outerHeight - height) / 2);
      window.open(
        response.url,
        "instagram_oauth",
        `width=${width},height=${height},left=${left},top=${top},toolbar=no,menubar=no,scrollbars=yes,resizable=yes`,
      );

      return response;
    },
  });
}

export function useWorkspacesQuery(enabled = true) {
  return useQuery({
    queryKey: queryKeys.workspaces,
    queryFn: workspaceApi.list,
    enabled,
  });
}

export function useWorkspaceMembersQuery(workspaceId: string | null | undefined) {
  return useQuery({
    queryKey: workspaceId
      ? queryKeys.workspaceMembers(workspaceId)
      : ["workspaces", "members", "none"],
    queryFn: () => workspaceApi.members(workspaceId!),
    enabled: Boolean(workspaceId),
  });
}

export function useActivateWorkspaceMutation() {
  const invalidate = useInvalidateWorkspaceData();
  return useMutation({
    mutationFn: workspaceApi.activate,
    onSuccess: invalidate,
  });
}

export function useUpdateWorkspaceMutation() {
  const invalidate = useInvalidateWorkspaceData();
  return useMutation({
    mutationFn: ({ workspaceId, name }: { workspaceId: string; name: string }) =>
      workspaceApi.update(workspaceId, { name }),
    onSuccess: invalidate,
  });
}

export function useDeleteWorkspaceMutation() {
  const invalidate = useInvalidateWorkspaceData();
  return useMutation({
    mutationFn: workspaceApi.delete,
    onSuccess: invalidate,
  });
}

export function useInviteMemberMutation(workspaceId: string | null | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: { email: string; role: string }) =>
      workspaceApi.inviteMember(workspaceId!, body),
    onSuccess: () => {
      if (workspaceId)
        queryClient.invalidateQueries({ queryKey: queryKeys.workspaceMembers(workspaceId) });
    },
  });
}

export function useUpdateMemberMutation(workspaceId: string | null | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: string }) =>
      workspaceApi.updateMember(workspaceId!, userId, { role }),
    onSuccess: () => {
      if (workspaceId)
        queryClient.invalidateQueries({ queryKey: queryKeys.workspaceMembers(workspaceId) });
    },
  });
}

export function useRemoveMemberMutation(workspaceId: string | null | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) => workspaceApi.removeMember(workspaceId!, userId),
    onSuccess: () => {
      if (workspaceId)
        queryClient.invalidateQueries({ queryKey: queryKeys.workspaceMembers(workspaceId) });
    },
  });
}

export function useDashboardQueries(workspaceId: string | null | undefined) {
  return {
    stats: useQuery({
      queryKey: workspaceId
        ? queryKeys.dashboardStats(workspaceId)
        : ["dashboard", "stats", "none"],
      queryFn: () => dashboardApi.stats(workspaceId!),
      enabled: Boolean(workspaceId),
    }),
    activity: useQuery({
      queryKey: workspaceId
        ? queryKeys.dashboardActivity(workspaceId)
        : ["dashboard", "activity", "none"],
      queryFn: () => dashboardApi.recentActivity(workspaceId!),
      enabled: Boolean(workspaceId),
    }),
    usage: useUsageQuery(workspaceId),
  };
}

export function useUsageQuery(workspaceId: string | null | undefined) {
  return useQuery({
    queryKey: workspaceId ? queryKeys.usage(workspaceId) : ["usage", "none"],
    queryFn: () => dashboardApi.usage(workspaceId!),
    enabled: Boolean(workspaceId),
  });
}

export function useAutomationsQuery(
  workspaceId: string | null | undefined,
  filters: AutomationFilters = {},
) {
  return useQuery({
    queryKey: workspaceId ? queryKeys.automations(workspaceId, filters) : ["automations", "none"],
    queryFn: () => automationApi.list(workspaceId!, filters),
    enabled: Boolean(workspaceId),
  });
}

export function useAutomationQuery(workspaceId: string | null | undefined, automationId: string) {
  return useQuery({
    queryKey:
      workspaceId && automationId !== "new"
        ? queryKeys.automation(workspaceId, automationId)
        : ["automations", "detail", "none"],
    queryFn: () => automationApi.detail(workspaceId!, automationId),
    enabled: Boolean(workspaceId && automationId !== "new"),
  });
}

export function useCreateAutomationMutation(workspaceId: string | null | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: AutomationCreate) => automationApi.create(workspaceId!, body),
    onSuccess: () => {
      if (workspaceId) queryClient.invalidateQueries({ queryKey: ["automations", workspaceId] });
    },
  });
}

export function useUpdateAutomationMutation(
  workspaceId: string | null | undefined,
  automationId: string,
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: AutomationUpdate) => automationApi.update(workspaceId!, automationId, body),
    onSuccess: () => {
      if (workspaceId) queryClient.invalidateQueries({ queryKey: ["automations", workspaceId] });
    },
  });
}

export function useAutomationStatusMutation(
  workspaceId: string | null | undefined,
  automationId: string,
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (status: "active" | "inactive") =>
      status === "active"
        ? automationApi.activate(workspaceId!, automationId)
        : automationApi.deactivate(workspaceId!, automationId),
    onSuccess: () => {
      if (workspaceId) queryClient.invalidateQueries({ queryKey: ["automations", workspaceId] });
    },
  });
}

export function useDeleteAutomationMutation(workspaceId: string | null | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (automationId: string) => automationApi.delete(workspaceId!, automationId),
    onSuccess: () => {
      if (workspaceId) queryClient.invalidateQueries({ queryKey: ["automations", workspaceId] });
    },
  });
}

export function useTestTriggerMutation(
  workspaceId: string | null | undefined,
  automationId: string,
) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      automationApi.testTrigger(workspaceId!, automationId, { source: "frontend_test" }),
    onSuccess: () => {
      if (workspaceId) {
        queryClient.invalidateQueries({
          queryKey: queryKeys.automationRuns(workspaceId, automationId),
        });
      }
    },
  });
}

export function useContactsQuery(
  workspaceId: string | null | undefined,
  filters: ContactFilters = {},
) {
  return useQuery({
    queryKey: workspaceId ? queryKeys.contacts(workspaceId, filters) : ["contacts", "none"],
    queryFn: () => contactApi.list(workspaceId!, filters),
    enabled: Boolean(workspaceId),
  });
}

export function useContactMutation(workspaceId: string | null | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: ContactCreate) => contactApi.create(workspaceId!, body),
    onSuccess: () => {
      if (workspaceId) queryClient.invalidateQueries({ queryKey: ["contacts", workspaceId] });
    },
  });
}

export function useUpdateContactMutation(workspaceId: string | null | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ contactId, body }: { contactId: string; body: ContactUpdate }) =>
      contactApi.update(workspaceId!, contactId, body),
    onSuccess: () => {
      if (workspaceId) queryClient.invalidateQueries({ queryKey: ["contacts", workspaceId] });
    },
  });
}

export function useDeleteContactMutation(workspaceId: string | null | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (contactId: string) => contactApi.delete(workspaceId!, contactId),
    onSuccess: () => {
      if (workspaceId) queryClient.invalidateQueries({ queryKey: ["contacts", workspaceId] });
    },
  });
}

export function useBillingQueries(workspaceId: string | null | undefined) {
  return {
    plans: useQuery({ queryKey: queryKeys.billingPlans, queryFn: billingApi.plans }),
    subscription: useQuery({
      queryKey: workspaceId
        ? queryKeys.billingSubscription(workspaceId)
        : ["billing", "subscription", "none"],
      queryFn: () => billingApi.subscription(workspaceId!),
      enabled: Boolean(workspaceId),
    }),
    invoices: useQuery({
      queryKey: workspaceId
        ? queryKeys.billingInvoices(workspaceId)
        : ["billing", "invoices", "none"],
      queryFn: () => billingApi.invoices(workspaceId!),
      enabled: Boolean(workspaceId),
    }),
  };
}

export function useCheckoutMutation(workspaceId: string | null | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ plan_id, cycle }: { plan_id: string; cycle: BillingCycle }) =>
      billingApi.checkout(workspaceId!, { plan_id, cycle }),
    onSuccess: (response) => {
      if (workspaceId && response.activated) {
        queryClient.invalidateQueries({ queryKey: queryKeys.billingSubscription(workspaceId) });
        queryClient.invalidateQueries({ queryKey: queryKeys.authMe });
      }
      if (response.checkout_url) {
        window.location.assign(response.checkout_url);
      }
    },
  });
}

export function useBillingPortalMutation(workspaceId: string | null | undefined) {
  return useMutation({
    mutationFn: () => billingApi.portal(workspaceId!),
    onSuccess: (response) => window.location.assign(response.portal_url),
  });
}

export function useCancelSubscriptionMutation(workspaceId: string | null | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => billingApi.cancel(workspaceId!),
    onSuccess: () => {
      if (workspaceId)
        queryClient.invalidateQueries({ queryKey: queryKeys.billingSubscription(workspaceId) });
    },
  });
}

export function hasInstagramConnection(workspace: WorkspaceSummary | null | undefined) {
  return Boolean(workspace?.ig_username);
}
