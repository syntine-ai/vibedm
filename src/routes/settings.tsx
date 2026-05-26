import { createFileRoute } from "@tanstack/react-router";
import { ConnectInstagramDialog } from "@/components/ConnectInstagramDialog";
import { PageHeader } from "@/components/PageHeader";
import { useState } from "react";
import { user, initialWorkspaces, type Workspace } from "@/lib/mock-data";
import { Instagram, Plus, Check, Trash2, CreditCard } from "lucide-react";

export const Route = createFileRoute("/settings")({
  head: () => ({ meta: [{ title: "Settings — DMFlow" }] }),
  component: SettingsPage,
});

const tabs = ["General", "Instagram Accounts", "Workspaces", "Billing"] as const;

function SettingsPage() {
  const [tab, setTab] = useState<(typeof tabs)[number]>("General");

  return (
    <>
      <PageHeader title="Settings" subtitle="Manage your account and preferences." />

      <div className="flex items-center gap-1 mb-6 border-b border-border">
        {tabs.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition -mb-px ${
              tab === t ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "General" && <GeneralTab />}
      {tab === "Instagram Accounts" && <IGTab />}
      {tab === "Workspaces" && <WorkspacesTab />}
          {tab === "Billing" && <BillingTab />}
    </>
  );
}

function WorkspacesTab() {
  const [workspaces, setWorkspaces] = useState<Workspace[]>(initialWorkspaces);
  const [connectDialogOpen, setConnectDialogOpen] = useState(false);

  const setActive = (id: string) =>
    setWorkspaces((ws) => ws.map((w) => ({ ...w, active: w.id === id })));

  const remove = (id: string) =>
    setWorkspaces((ws) => {
      const filtered = ws.filter((w) => w.id !== id);
      if (filtered.length && !filtered.some((w) => w.active)) filtered[0].active = true;
      return filtered;
    });

  const addConnectedWorkspace = () => {
    const id = `w${Date.now()}`;
    const connectedIgUsername = user.igUsername?.replace(/^@/, "").trim() || "connected.account";

    setWorkspaces((ws) => {
      const nextIndex = ws.length + 1;
      const autoName = `Workspace ${nextIndex}`;
      return [...ws.map((workspace) => ({ ...workspace, active: false })), { id, name: autoName, igUsername: connectedIgUsername, active: true }];
    });
  };

  return (
    <>
      <div className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] p-6 max-w-3xl">
        <div className="flex items-start justify-between mb-5">
          <div>
            <h3 className="font-semibold">Your workspaces</h3>
            <p className="text-xs text-primary mt-0.5">
              {workspaces.length} workspace{workspaces.length === 1 ? "" : "s"} connected
            </p>
          </div>
          <button
            onClick={() => {
              setConnectDialogOpen(true);
            }}
            className="h-10 px-4 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary-dark transition flex items-center gap-1.5"
          >
            <Plus className="w-4 h-4" /> Add workspace
          </button>
        </div>

        <p className="text-sm text-muted-foreground mb-4">
          Each workspace is linked to one Instagram account. Switch between them anytime.
        </p>

        <div className="space-y-2.5">
          {workspaces.map((w) => (
            <div
              key={w.id}
              className={`flex items-center gap-3 rounded-xl border p-3.5 transition ${
                w.active ? "border-primary/40 bg-accent" : "border-border hover:bg-accent/50"
              }`}
            >
              <div className="w-12 h-12 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-bold shrink-0">
                {w.name[0]}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-semibold truncate">{w.name}</span>
                  {w.active && (
                    <span className="text-[11px] font-semibold text-primary bg-primary/10 px-2 py-0.5 rounded">
                      Active
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-1 text-xs text-muted-foreground mt-0.5">
                  <Instagram className="w-3.5 h-3.5" /> @{w.igUsername}
                </div>
              </div>
              <button
                onClick={() => setActive(w.id)}
                disabled={w.active}
                className={`w-9 h-9 rounded-full flex items-center justify-center transition ${
                  w.active
                    ? "bg-primary text-primary-foreground"
                    : "bg-accent text-muted-foreground hover:bg-primary hover:text-primary-foreground"
                }`}
                title={w.active ? "Active workspace" : "Set as active"}
              >
                <Check className="w-4 h-4" />
              </button>
              {workspaces.length > 1 && (
                <button
                  onClick={() => remove(w.id)}
                  className="w-9 h-9 rounded-full flex items-center justify-center text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition"
                  title="Remove workspace"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              )}
            </div>
          ))}
        </div>
      </div>

      <ConnectInstagramDialog
        open={connectDialogOpen}
        onOpenChange={setConnectDialogOpen}
        onConnected={() => {
          setConnectDialogOpen(false);
          addConnectedWorkspace();
        }}
      />
    </>
  );
}

function GeneralTab() {
  return (
    <div className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] p-6 max-w-3xl">
      <h3 className="font-semibold">General Settings</h3>
      <p className="text-xs text-muted-foreground mb-5">Manage your workspace preferences</p>
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <F label="First Name"><input className="ipt" defaultValue={user.firstName} /></F>
          <F label="Last Name"><input className="ipt" defaultValue={user.lastName} /></F>
        </div>
        <F label="Email"><input type="email" className="ipt" defaultValue={user.email} /></F>
        <F label="Phone Number"><input type="tel" className="ipt" defaultValue={user.phone} /></F>
        <div className="flex justify-end pt-2">
          <button className="h-10 px-5 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary-dark transition">
            Save Changes
          </button>
        </div>
      </div>
      <style>{`.ipt { width:100%; height:44px; padding:0 14px; border:1px solid var(--border); border-radius:10px; font-size:14px; outline:none; background:var(--surface); }
.ipt:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(61,58,238,0.12); }`}</style>
    </div>
  );
}

function F({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="text-xs font-medium mb-1.5 block">{label}</span>
      {children}
    </label>
  );
}

function IGTab() {
  return (
    <div className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] p-6 max-w-3xl">
      <h3 className="font-semibold">Instagram Accounts</h3>
      <p className="text-xs text-muted-foreground mb-5">Manage your connected Instagram accounts</p>

      {!user.igConnected ? (
        <div className="rounded-xl border-2 border-dashed border-border p-10 text-center">
          <div className="w-14 h-14 mx-auto rounded-2xl bg-accent flex items-center justify-center mb-4">
            <Instagram className="w-7 h-7 text-primary" />
          </div>
          <h4 className="font-semibold mb-1">No accounts connected</h4>
          <p className="text-sm text-muted-foreground mb-5">Connect your Instagram Business account to start building automations.</p>
          <button className="h-11 px-5 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary-dark transition">
            Connect Instagram
          </button>
        </div>
      ) : (
        <div className="rounded-xl border border-border p-6 max-w-sm">
          <div className="w-20 h-20 rounded-full bg-primary mx-auto mb-3 flex items-center justify-center text-primary-foreground font-bold text-2xl">
            {user.igUsername[0].toUpperCase()}
          </div>
          <div className="text-center mb-1 font-bold">@{user.igUsername}</div>
          <div className="text-center text-sm text-muted-foreground mb-4">{user.firstName} {user.lastName}</div>
          <button className="w-full h-10 rounded-lg bg-destructive text-destructive-foreground text-sm font-semibold mb-2">Disconnect</button>
          <button className="w-full h-10 rounded-lg bg-success text-success-foreground text-sm font-semibold">Refresh Token</button>
        </div>
      )}
    </div>
  );
}

function BillingTab() {
  return (
    <>
      <div className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] p-6 max-w-3xl mb-6">
        <div className="flex flex-col items-center text-center py-8">
          <div className="w-20 h-20 rounded-2xl bg-accent flex items-center justify-center mb-4">
            <CreditCard className="w-8 h-8 text-primary" />
          </div>
          <h3 className="font-semibold mb-1">No Active Subscription</h3>
          <p className="text-sm text-muted-foreground mb-6">You don't have any active subscriptions yet. Activate a subscription to unlock all premium features.</p>
          <button className="h-11 px-5 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary-dark transition flex items-center gap-2">
            <Plus className="w-4 h-4" /> Activate Subscription
          </button>
        </div>
      </div>

      <div className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] p-6 max-w-3xl">
        <h3 className="font-semibold">Invoice History</h3>
        <p className="text-sm text-muted-foreground mt-4">No invoices found yet</p>
      </div>
    </>
  );
}

