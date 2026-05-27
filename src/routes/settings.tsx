import { createFileRoute } from "@tanstack/react-router";
import { Check, Instagram, Plus, Trash2 } from "lucide-react";
import { useState } from "react";

import { ConnectInstagramDialog } from "@/components/ConnectInstagramDialog";
import { FormField } from "@/components/FormField";
import { PageHeader } from "@/components/PageHeader";
import {
  useActivateWorkspaceMutation,
  useActiveWorkspace,
  useBillingPortalMutation,
  useBillingQueries,
  useCancelSubscriptionMutation,
  useCheckoutMutation,
  useDeleteWorkspaceMutation,
  useInviteMemberMutation,
  useRemoveMemberMutation,
  useUpdateMemberMutation,
  useUpdateWorkspaceMutation,
  useWorkspaceMembersQuery,
  useWorkspacesQuery,
} from "@/lib/api/hooks";
import { instagramApi } from "@/lib/api/resources";
import type { BillingCycle, Plan, WorkspaceSummary } from "@/lib/api/types";

export const Route = createFileRoute("/settings")({
  head: () => ({ meta: [{ title: "Settings - Vibe DM" }] }),
  component: SettingsPage,
});

const tabs = ["General", "Instagram Accounts", "Workspaces", "Billing"] as const;

function SettingsPage() {
  const [tab, setTab] = useState<(typeof tabs)[number]>("General");

  return (
    <>
      <PageHeader title="Settings" subtitle="Manage your account and workspace preferences." />

      <div className="flex items-center gap-1 mb-6 border-b border-border overflow-x-auto">
        {tabs.map((item) => (
          <button
            type="button"
            key={item}
            onClick={() => setTab(item)}
            className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition -mb-px whitespace-nowrap ${
              tab === item
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {item}
          </button>
        ))}
      </div>

      {tab === "General" && <GeneralTab />}
      {tab === "Instagram Accounts" && <InstagramTab />}
      {tab === "Workspaces" && <WorkspacesTab />}
      {tab === "Billing" && <BillingTab />}
    </>
  );
}

export function GeneralTab() {
  const { meQuery } = useActiveWorkspace();
  const user = meQuery.data?.user;

  return (
    <div className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] p-6 max-w-3xl">
      <h3 className="font-semibold">General Settings</h3>
      <p className="text-xs text-muted-foreground mb-5">
        Profile data is synced from Supabase Auth.
      </p>
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <FormField label="First Name">
            <input className="ipt" value={user?.first_name ?? ""} readOnly />
          </FormField>
          <FormField label="Last Name">
            <input className="ipt" value={user?.last_name ?? ""} readOnly />
          </FormField>
        </div>
        <FormField label="Email">
          <input type="email" className="ipt" value={user?.email ?? ""} readOnly />
        </FormField>
        <FormField label="Phone Number">
          <input type="tel" className="ipt" value={user?.phone ?? ""} readOnly />
        </FormField>
      </div>
      <InputStyles />
    </div>
  );
}

export function InstagramTab() {
  const { activeWorkspace } = useActiveWorkspace();
  const [connectDialogOpen, setConnectDialogOpen] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const disconnect = async () => {
    if (!activeWorkspace?.id) return;
    setDisconnecting(true);
    setError(null);
    try {
      await instagramApi.disconnect(activeWorkspace.id);
      window.location.reload();
    } catch (disconnectError) {
      setError(disconnectError instanceof Error ? disconnectError.message : "Disconnect failed");
    } finally {
      setDisconnecting(false);
    }
  };

  return (
    <div className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] p-6 max-w-3xl">
      <h3 className="font-semibold">Instagram Accounts</h3>
      <p className="text-xs text-muted-foreground mb-5">
        Manage the Instagram account for the active workspace.
      </p>

      {!activeWorkspace?.ig_username ? (
        <div className="rounded-xl border-2 border-dashed border-border p-10 text-center">
          <div className="w-14 h-14 mx-auto rounded-2xl bg-accent flex items-center justify-center mb-4">
            <Instagram className="size-7 text-primary" />
          </div>
          <h4 className="font-semibold mb-1">No account connected</h4>
          <p className="text-sm text-muted-foreground mb-5">
            Connect your Instagram Business account to start building automations.
          </p>
          <button
            type="button"
            onClick={() => setConnectDialogOpen(true)}
            className="h-11 px-5 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary-dark transition"
          >
            Connect Instagram
          </button>
        </div>
      ) : (
        <div className="rounded-xl border border-border p-6 max-w-sm">
          <div className="w-20 h-20 rounded-full bg-primary mx-auto mb-3 flex items-center justify-center text-primary-foreground font-bold text-2xl">
            {activeWorkspace.ig_username[0]?.toUpperCase()}
          </div>
          <div className="text-center mb-1 font-bold">@{activeWorkspace.ig_username}</div>
          <div className="text-center text-sm text-muted-foreground mb-4">
            {activeWorkspace.name}
          </div>
          {error && <p className="text-xs text-destructive mb-3">{error}</p>}
          <div className="flex flex-col gap-2">
            <button
              type="button"
              onClick={() => setConnectDialogOpen(true)}
              className="w-full h-10 rounded-lg border border-border text-foreground hover:bg-accent text-sm font-semibold transition"
            >
              Reconnect / Update
            </button>
            <button
              type="button"
              onClick={disconnect}
              disabled={disconnecting}
              className="w-full h-10 rounded-lg bg-destructive text-destructive-foreground text-sm font-semibold disabled:opacity-60 hover:bg-destructive/90 transition"
            >
              {disconnecting ? "Disconnecting..." : "Disconnect"}
            </button>
          </div>
        </div>
      )}

      <ConnectInstagramDialog
        open={connectDialogOpen}
        onOpenChange={setConnectDialogOpen}
        intent="add_workspace"
      />
    </div>
  );
}

export function WorkspacesTab() {
  const workspacesQuery = useWorkspacesQuery();
  const activateMutation = useActivateWorkspaceMutation();
  const updateMutation = useUpdateWorkspaceMutation();
  const deleteMutation = useDeleteWorkspaceMutation();
  const [connectDialogOpen, setConnectDialogOpen] = useState(false);

  const workspaces = workspacesQuery.data ?? [];

  return (
    <>
      <div className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] p-6 max-w-3xl mb-6">
        <div className="flex items-start justify-between mb-5">
          <div>
            <h3 className="font-semibold">Your workspaces</h3>
            <p className="text-xs text-primary mt-0.5">
              {workspaces.length} workspace{workspaces.length === 1 ? "" : "s"} connected
            </p>
          </div>
          <button
            type="button"
            onClick={() => setConnectDialogOpen(true)}
            className="h-10 px-4 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary-dark transition flex items-center gap-1.5"
          >
            <Plus className="size-4" /> Add workspace
          </button>
        </div>

        <p className="text-sm text-muted-foreground mb-4">
          Each workspace is linked to one Instagram account. Switch between them anytime.
        </p>

        <div className="space-y-2.5">
          {workspacesQuery.isLoading && (
            <p className="text-sm text-muted-foreground">Loading workspaces...</p>
          )}
          {workspaces.map((workspace) => (
            <WorkspaceRow
              key={workspace.id}
              workspace={workspace}
              onActivate={() => activateMutation.mutate(workspace.id)}
              onRename={(name) => updateMutation.mutate({ workspaceId: workspace.id, name })}
              onDelete={() => {
                if (window.confirm(`Delete workspace "${workspace.name}"?`)) {
                  deleteMutation.mutate(workspace.id);
                }
              }}
            />
          ))}
          {!workspacesQuery.isLoading && workspaces.length === 0 && (
            <p className="text-sm text-muted-foreground">
              Connect Instagram to create your first workspace.
            </p>
          )}
        </div>
      </div>

      <MembersPanel activeWorkspace={workspaces.find((workspace) => workspace.active) ?? null} />

      <ConnectInstagramDialog
        open={connectDialogOpen}
        onOpenChange={setConnectDialogOpen}
        intent="add_workspace"
      />
    </>
  );
}

export function WorkspaceRow({
  workspace,
  onActivate,
  onRename,
  onDelete,
}: {
  workspace: WorkspaceSummary;
  onActivate: () => void;
  onRename: (name: string) => void;
  onDelete: () => void;
}) {
  const [name, setName] = useState(workspace.name);

  return (
    <div
      className={`flex items-center gap-3 rounded-xl border p-3.5 transition ${
        workspace.active ? "border-primary/40 bg-accent" : "border-border hover:bg-accent/50"
      }`}
    >
      <div className="w-12 h-12 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-bold shrink-0">
        {workspace.name[0]}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            onBlur={() => name.trim() && name !== workspace.name && onRename(name.trim())}
            className="font-semibold truncate bg-transparent outline-none focus:bg-background rounded px-1"
          />
          {workspace.active && (
            <span className="text-[11px] font-semibold text-primary bg-primary/10 px-2 py-0.5 rounded">
              Active
            </span>
          )}
        </div>
        <div className="flex items-center gap-1 text-xs text-muted-foreground mt-0.5">
          <Instagram className="size-3.5" />{" "}
          {workspace.ig_username ? `@${workspace.ig_username}` : "No IG account"}
        </div>
      </div>
      <button
        type="button"
        aria-label={workspace.active ? "Active workspace" : "Set as active"}
        onClick={onActivate}
        disabled={workspace.active}
        className={`w-9 h-9 rounded-full flex items-center justify-center transition ${
          workspace.active
            ? "bg-primary text-primary-foreground"
            : "bg-accent text-muted-foreground hover:bg-primary hover:text-primary-foreground"
        }`}
        title={workspace.active ? "Active workspace" : "Set as active"}
      >
        <Check className="size-4" />
      </button>
      <button
        type="button"
        aria-label="Delete workspace"
        onClick={onDelete}
        className="w-9 h-9 rounded-full flex items-center justify-center text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition"
        title="Delete workspace"
      >
        <Trash2 className="size-4" />
      </button>
    </div>
  );
}

export function MembersPanel({ activeWorkspace }: { activeWorkspace: WorkspaceSummary | null }) {
  const membersQuery = useWorkspaceMembersQuery(activeWorkspace?.id);
  const inviteMutation = useInviteMemberMutation(activeWorkspace?.id);
  const updateMemberMutation = useUpdateMemberMutation(activeWorkspace?.id);
  const removeMemberMutation = useRemoveMemberMutation(activeWorkspace?.id);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("member");

  if (!activeWorkspace) return null;

  return (
    <div className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] p-6 max-w-3xl">
      <h3 className="font-semibold">Members</h3>
      <p className="text-xs text-muted-foreground mb-5">
        Manage access for {activeWorkspace.name}.
      </p>
      <form
        className="flex gap-2 mb-5"
        onSubmit={(event) => {
          event.preventDefault();
          inviteMutation.mutate({ email, role });
          setEmail("");
        }}
      >
        <input
          className="ipt flex-1"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          placeholder="member@example.com"
          required
        />
        <select
          className="ipt max-w-[140px]"
          value={role}
          onChange={(event) => setRole(event.target.value)}
        >
          <option value="member">Member</option>
          <option value="admin">Admin</option>
        </select>
        <button type="submit" className="h-11 px-4 rounded-lg bg-primary text-primary-foreground text-sm font-semibold">
          Invite
        </button>
      </form>
      <div className="space-y-2">
        {membersQuery.data?.map((member) => (
          <div
            key={member.user_id}
            className="flex items-center gap-3 rounded-lg border border-border p-3"
          >
            <div className="flex-1">
              <div className="text-sm font-semibold">{member.email ?? member.user_id}</div>
              <div className="text-xs text-muted-foreground">
                {member.active ? "Active workspace" : "Member"}
              </div>
            </div>
            <select
              className="ipt max-w-[130px]"
              value={member.role}
              onChange={(event) =>
                updateMemberMutation.mutate({ userId: member.user_id, role: event.target.value })
              }
            >
              <option value="owner">Owner</option>
              <option value="admin">Admin</option>
              <option value="member">Member</option>
            </select>
            <button
              type="button"
              onClick={() => removeMemberMutation.mutate(member.user_id)}
              className="text-xs font-semibold text-destructive"
            >
              Remove
            </button>
          </div>
        ))}
        {membersQuery.isLoading && (
          <p className="text-sm text-muted-foreground">Loading members...</p>
        )}
      </div>
      <InputStyles />
    </div>
  );
}

export function BillingTab() {
  const { activeWorkspace } = useActiveWorkspace();
  const [cycle, setCycle] = useState<BillingCycle>("monthly");
  const billing = useBillingQueries(activeWorkspace?.id);
  const checkoutMutation = useCheckoutMutation(activeWorkspace?.id);
  const portalMutation = useBillingPortalMutation(activeWorkspace?.id);
  const cancelMutation = useCancelSubscriptionMutation(activeWorkspace?.id);
  const subscription = billing.subscription.data;

  if (!activeWorkspace) {
    return (
      <div className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] p-10 text-center">
        <CreditCardFallback />
        <h3 className="mt-4 font-semibold">No active workspace</h3>
        <p className="mt-2 text-sm text-muted-foreground">
          Connect Instagram to create a workspace before managing billing.
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] p-6 mb-6">
        <div className="flex items-center justify-between gap-4 mb-6">
          <div>
            <h3 className="font-semibold">Billing</h3>
            <p className="text-xs text-muted-foreground">
              Plan for {activeWorkspace?.name ?? "your active workspace"}.
            </p>
          </div>
          <div className="inline-flex rounded-lg border border-border p-1">
            {(["monthly", "yearly"] as BillingCycle[]).map((item) => (
              <button
                type="button"
                key={item}
                onClick={() => setCycle(item)}
                className={`px-3 py-1.5 rounded-md text-xs font-semibold ${
                  cycle === item ? "bg-primary text-primary-foreground" : "text-muted-foreground"
                }`}
              >
                {item === "monthly" ? "Monthly" : "Yearly"}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          {billing.plans.data?.map((plan) => (
            <PlanCard
              key={plan.id}
              plan={plan}
              cycle={cycle}
              active={subscription?.plan_id === plan.id}
              onCheckout={() => checkoutMutation.mutate({ plan_id: plan.id, cycle })}
            />
          ))}
        </div>

        {subscription && (
          <div className="mt-6 rounded-xl border border-border p-4 flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className="text-sm font-semibold">
                Current subscription: {subscription.plan_id}
              </div>
              <div className="text-xs text-muted-foreground">
                {subscription.status} / {subscription.cycle}
                {subscription.cancel_at_period_end ? " / cancels at period end" : ""}
              </div>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => portalMutation.mutate()}
                className="h-10 px-4 rounded-lg border border-border text-sm font-semibold"
              >
                Billing portal
              </button>
              <button
                type="button"
                onClick={() => cancelMutation.mutate()}
                className="h-10 px-4 rounded-lg bg-destructive text-destructive-foreground text-sm font-semibold"
              >
                Cancel
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] p-6">
        <h3 className="font-semibold">Invoice History</h3>
        <div className="mt-4 space-y-2">
          {billing.invoices.data?.map((invoice) => (
            <div
              key={invoice.id}
              className="flex items-center justify-between rounded-lg border border-border p-3"
            >
              <div>
                <div className="text-sm font-semibold">{formatInr(invoice.amount_paise)}</div>
                <div className="text-xs text-muted-foreground">
                  {invoice.status} / {new Date(invoice.issued_at).toLocaleDateString()}
                </div>
              </div>
              {(invoice.pdf_url || invoice.hosted_invoice_url) && (
                <a
                  href={invoice.pdf_url ?? invoice.hosted_invoice_url ?? "#"}
                  target="_blank"
                  rel="noreferrer"
                  className="text-xs font-semibold text-primary"
                >
                  Download
                </a>
              )}
            </div>
          ))}
          {!billing.invoices.isLoading && !billing.invoices.data?.length && (
            <p className="text-sm text-muted-foreground">No invoices found yet</p>
          )}
        </div>
      </div>
    </>
  );
}

export function CreditCardFallback() {
  return (
    <div className="mx-auto w-16 h-16 rounded-2xl bg-accent flex items-center justify-center text-primary">
      <span className="text-lg font-bold">INR</span>
    </div>
  );
}

export function PlanCard({
  plan,
  cycle,
  active,
  onCheckout,
}: {
  plan: Plan;
  cycle: BillingCycle;
  active: boolean;
  onCheckout: () => void;
}) {
  const price = cycle === "monthly" ? plan.monthly_paise : plan.yearly_paise;

  return (
    <div
      className={`rounded-2xl border p-5 ${active ? "border-primary bg-accent" : "border-border bg-card"}`}
    >
      <div className="flex items-center justify-between gap-2">
        <h4 className="font-bold">{plan.display_name}</h4>
        {plan.is_popular && <span className="text-[10px] font-bold text-primary">Popular</span>}
      </div>
      <div className="mt-3 text-2xl font-bold">{formatInr(price)}</div>
      <div className="text-xs text-muted-foreground">
        {cycle === "monthly" ? "per month" : "per year"}
      </div>
      <ul className="mt-4 space-y-2 text-xs text-muted-foreground">
        {plan.features.map((feature) => (
          <li key={feature} className="flex gap-2">
            <Check className="size-3.5 text-success shrink-0" /> {feature}
          </li>
        ))}
      </ul>
      <button
        type="button"
        onClick={onCheckout}
        className="mt-5 w-full h-10 rounded-lg bg-primary text-primary-foreground text-sm font-semibold"
      >
        {active ? "Current plan" : plan.id === "free" ? "Start free" : "Subscribe"}
      </button>
    </div>
  );
}

export function formatInr(paise: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(paise / 100);
}

export function InputStyles() {
  return (
    <style>{`.ipt { width:100%; height:44px; padding:0 14px; border:1px solid var(--border); border-radius:10px; font-size:14px; outline:none; background:var(--surface); }
.ipt:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(61,58,238,0.12); }`}</style>
  );
}
