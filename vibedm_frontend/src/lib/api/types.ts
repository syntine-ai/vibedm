import type { components } from "./openapi";

export type Schema<Name extends keyof components["schemas"]> = components["schemas"][Name];

export type UserProfile = Schema<"UserProfile">;
export type WorkspaceSummary = Schema<"WorkspaceSummary">;
export type Workspace = Schema<"WorkspaceResponse">;
export type WorkspaceMember = Schema<"WorkspaceMemberResponse">;
export type AuthMe = Schema<"AuthMeResponse">;

export type OAuthStart = Schema<"OAuthStartResponse">;
export type InstagramWorkspaceResponse = Schema<"InstagramWorkspaceResponse">;

export type DashboardStats = Schema<"DashboardStatsResponse">;
export type DashboardActivity = Schema<"ActivityResponse">;
export type Usage = Schema<"UsageResponse">;

export type AutomationSummary = Schema<"AutomationSummary">;
export type AutomationDetail = Schema<"AutomationDetail">;
export type AutomationCreate = Schema<"AutomationCreateRequest">;
export type AutomationUpdate = Schema<"AutomationUpdateRequest">;
export type AutomationRun = Schema<"AutomationRunResponse">;
export type AutomationStep = Schema<"AutomationStep">;
export type TriggerType = NonNullable<AutomationSummary["trigger_type"]>;

export type Contact = Schema<"ContactResponse">;
export type ContactCreate = Schema<"ContactCreateRequest">;
export type ContactUpdate = Schema<"ContactUpdateRequest">;

export type Plan = Schema<"PlanResponse">;
export type Subscription = Schema<"SubscriptionResponse">;
export type CheckoutRequest = Schema<"CheckoutRequest">;
export type CheckoutResponse = Schema<"CheckoutResponse">;
export type PortalResponse = Schema<"PortalResponse">;
export type Invoice = Schema<"InvoiceResponse">;
export type BillingCycle = CheckoutRequest["cycle"];
