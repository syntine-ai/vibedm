import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/PageHeader";
import { useState } from "react";
import { user } from "@/lib/mock-data";
import { Instagram } from "lucide-react";

export const Route = createFileRoute("/settings")({
  head: () => ({ meta: [{ title: "Settings — DMFlow" }] }),
  component: SettingsPage,
});

const tabs = ["General", "Instagram Accounts"] as const;

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

