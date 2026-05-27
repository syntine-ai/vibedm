import { createApiClient } from "./client";
import type {
  AuthMe,
  AutomationCreate,
  AutomationDetail,
  AutomationRun,
  AutomationSummary,
  AutomationUpdate,
  BillingCycle,
  CheckoutResponse,
  Contact,
  ContactCreate,
  ContactUpdate,
  DashboardActivity,
  DashboardStats,
  InstagramWorkspaceResponse,
  Invoice,
  OAuthStart,
  Plan,
  PortalResponse,
  Subscription,
  TriggerType,
  Usage,
  UserProfile,
  Workspace,
  WorkspaceMember,
  WorkspaceSummary,
} from "./types";

const api = createApiClient();

export type AutomationFilters = {
  status?: string;
  trigger_type?: TriggerType | "";
  q?: string;
};

export type ContactFilters = {
  q?: string;
  source_automation_id?: string;
  tag?: string;
};

export const authApi = {
  sync: (accessToken?: string | null) =>
    api.request<UserProfile>("/api/v1/auth/sync", { method: "POST", accessToken }),
  me: () => api.request<AuthMe>("/api/v1/auth/me"),
  logout: () => api.request<Record<string, boolean>>("/api/v1/auth/logout", { method: "POST" }),
};

export const workspaceApi = {
  list: () => api.request<Workspace[]>("/api/v1/workspaces"),
  detail: (workspaceId: string) =>
    api.request<Workspace>(`/api/v1/workspaces/${workspaceId}`, {
      workspaceScoped: true,
      workspaceId,
    }),
  update: (workspaceId: string, body: { name: string }) =>
    api.request<Workspace>(`/api/v1/workspaces/${workspaceId}`, {
      method: "PATCH",
      body,
      workspaceScoped: true,
      workspaceId,
    }),
  activate: (workspaceId: string) =>
    api.request<Record<string, boolean>>(`/api/v1/workspaces/${workspaceId}/activate`, {
      method: "POST",
      workspaceScoped: true,
      workspaceId,
    }),
  delete: (workspaceId: string) =>
    api.request<void>(`/api/v1/workspaces/${workspaceId}`, {
      method: "DELETE",
      workspaceScoped: true,
      workspaceId,
    }),
  members: (workspaceId: string) =>
    api.request<WorkspaceMember[]>(`/api/v1/workspaces/${workspaceId}/members`, {
      workspaceScoped: true,
      workspaceId,
    }),
  inviteMember: (workspaceId: string, body: { email: string; role: string }) =>
    api.request<Record<string, string>>(`/api/v1/workspaces/${workspaceId}/members`, {
      method: "POST",
      body,
      workspaceScoped: true,
      workspaceId,
    }),
  updateMember: (workspaceId: string, userId: string, body: { role: string }) =>
    api.request<WorkspaceMember>(`/api/v1/workspaces/${workspaceId}/members/${userId}`, {
      method: "PATCH",
      body,
      workspaceScoped: true,
      workspaceId,
    }),
  removeMember: (workspaceId: string, userId: string) =>
    api.request<void>(`/api/v1/workspaces/${workspaceId}/members/${userId}`, {
      method: "DELETE",
      workspaceScoped: true,
      workspaceId,
    }),
};

export const instagramApi = {
  startOauth: () => api.request<OAuthStart>("/api/v1/instagram/oauth/start"),
  completeOauth: (body: { code: string; state: string }) =>
    api.request<InstagramWorkspaceResponse>("/api/v1/instagram/oauth/callback", {
      method: "POST",
      body,
    }),
  connectWorkspace: (body: { code: string; state: string }, workspaceId?: string) =>
    api.request<InstagramWorkspaceResponse>("/api/v1/workspaces/connect-instagram", {
      method: "POST",
      body,
      workspaceScoped: true,
      workspaceId,
    }),
  disconnect: (workspaceId: string) =>
    api.request<Record<string, boolean>>("/api/v1/instagram/connection", {
      method: "DELETE",
      workspaceScoped: true,
      workspaceId,
    }),
  media: (workspaceId: string, query?: { limit?: number; after?: string }) =>
    api.request<{ data: any[]; paging?: { cursors?: { after?: string } } }>("/api/v1/instagram/media", {
      workspaceScoped: true,
      workspaceId,
      query,
    }),
};

export const dashboardApi = {
  stats: (workspaceId: string) =>
    api.request<DashboardStats>("/api/v1/dashboard/stats", { workspaceScoped: true, workspaceId }),
  recentActivity: (workspaceId: string) =>
    api.request<DashboardActivity[]>("/api/v1/dashboard/recent-activity", {
      workspaceScoped: true,
      workspaceId,
    }),
  usage: (workspaceId: string) =>
    api.request<Usage>("/api/v1/usage", { workspaceScoped: true, workspaceId }),
};

export const automationApi = {
  list: (workspaceId: string, filters: AutomationFilters = {}) =>
    api.request<AutomationSummary[]>("/api/v1/automations", {
      workspaceScoped: true,
      workspaceId,
      query: filters,
    }),
  create: (workspaceId: string, body: AutomationCreate) =>
    api.request<AutomationDetail>("/api/v1/automations", {
      method: "POST",
      body,
      workspaceScoped: true,
      workspaceId,
    }),
  detail: (workspaceId: string, automationId: string) =>
    api.request<AutomationDetail>(`/api/v1/automations/${automationId}`, {
      workspaceScoped: true,
      workspaceId,
    }),
  update: (workspaceId: string, automationId: string, body: AutomationUpdate) =>
    api.request<AutomationDetail>(`/api/v1/automations/${automationId}`, {
      method: "PATCH",
      body,
      workspaceScoped: true,
      workspaceId,
    }),
  activate: (workspaceId: string, automationId: string) =>
    api.request<AutomationDetail>(`/api/v1/automations/${automationId}/activate`, {
      method: "POST",
      workspaceScoped: true,
      workspaceId,
    }),
  deactivate: (workspaceId: string, automationId: string) =>
    api.request<AutomationDetail>(`/api/v1/automations/${automationId}/deactivate`, {
      method: "POST",
      workspaceScoped: true,
      workspaceId,
    }),
  delete: (workspaceId: string, automationId: string) =>
    api.request<void>(`/api/v1/automations/${automationId}`, {
      method: "DELETE",
      workspaceScoped: true,
      workspaceId,
    }),
  testTrigger: (workspaceId: string, automationId: string, event: Record<string, unknown>) =>
    api.request<AutomationRun>(`/api/v1/automations/${automationId}/test-trigger`, {
      method: "POST",
      body: { event },
      workspaceScoped: true,
      workspaceId,
    }),
  runs: (workspaceId: string, automationId: string) =>
    api.request<AutomationRun[]>(`/api/v1/automations/${automationId}/runs`, {
      workspaceScoped: true,
      workspaceId,
    }),
};

export const contactApi = {
  list: (workspaceId: string, filters: ContactFilters = {}) =>
    api.request<Contact[]>("/api/v1/contacts", {
      workspaceScoped: true,
      workspaceId,
      query: filters,
    }),
  create: (workspaceId: string, body: ContactCreate) =>
    api.request<Contact>("/api/v1/contacts", {
      method: "POST",
      body,
      workspaceScoped: true,
      workspaceId,
    }),
  detail: (workspaceId: string, contactId: string) =>
    api.request<Contact>(`/api/v1/contacts/${contactId}`, { workspaceScoped: true, workspaceId }),
  update: (workspaceId: string, contactId: string, body: ContactUpdate) =>
    api.request<Contact>(`/api/v1/contacts/${contactId}`, {
      method: "PATCH",
      body,
      workspaceScoped: true,
      workspaceId,
    }),
  delete: (workspaceId: string, contactId: string) =>
    api.request<Record<string, boolean>>(`/api/v1/contacts/${contactId}`, {
      method: "DELETE",
      workspaceScoped: true,
      workspaceId,
    }),
  exportCsv: (workspaceId: string) =>
    api.request<string>("/api/v1/contacts/export.csv", { workspaceScoped: true, workspaceId }),
  importCsv: (workspaceId: string, file: File) => {
    const body = new FormData();
    body.set("file", file);
    return api.request<{ imported: number; skipped: number; errors: unknown[] }>(
      "/api/v1/contacts/import",
      {
        method: "POST",
        body,
        workspaceScoped: true,
        workspaceId,
      },
    );
  },
};

export const billingApi = {
  plans: () => api.request<Plan[]>("/api/v1/billing/plans"),
  subscription: (workspaceId: string) =>
    api.request<Subscription>("/api/v1/billing/subscription", {
      workspaceScoped: true,
      workspaceId,
    }),
  checkout: (workspaceId: string, body: { plan_id: string; cycle: BillingCycle }) =>
    api.request<CheckoutResponse>("/api/v1/billing/checkout", {
      method: "POST",
      body,
      workspaceScoped: true,
      workspaceId,
    }),
  portal: (workspaceId: string) =>
    api.request<PortalResponse>("/api/v1/billing/portal", {
      method: "POST",
      workspaceScoped: true,
      workspaceId,
    }),
  cancel: (workspaceId: string) =>
    api.request<Record<string, boolean>>("/api/v1/billing/cancel", {
      method: "POST",
      workspaceScoped: true,
      workspaceId,
    }),
  invoices: (workspaceId: string) =>
    api.request<Invoice[]>("/api/v1/billing/invoices", { workspaceScoped: true, workspaceId }),
};

export function getActiveWorkspace(workspaces: WorkspaceSummary[] | undefined) {
  return workspaces?.find((workspace) => workspace.active) ?? null;
}
