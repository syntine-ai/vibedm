import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/PageHeader";
import { Copy, Share2, Gift, Users, DollarSign } from "lucide-react";
import { useState } from "react";

export const Route = createFileRoute("/refer")({
  head: () => ({ meta: [{ title: "Refer & Earn — DMFlow" }] }),
  component: ReferPage,
});

function ReferPage() {
  const [copied, setCopied] = useState(false);
  const link = "https://dmflow.app/r/alex-morgan";

  return (
    <>
      <PageHeader title="Refer & Earn" subtitle="Invite creators and earn credits when they upgrade." />

      <div className="bg-gradient-to-br from-primary to-[var(--banner-to)] rounded-2xl p-8 text-white mb-6">
        <Gift className="w-10 h-10 mb-3 opacity-90" />
        <h2 className="text-2xl font-bold mb-1">Earn $20 for every friend</h2>
        <p className="text-white/80 text-sm mb-5">They get 20% off their first month. You get cash credit.</p>

        <div className="flex items-center gap-2 bg-white/15 backdrop-blur rounded-lg p-2 max-w-lg">
          <code className="flex-1 px-3 text-sm">{link}</code>
          <button
            onClick={() => {
              navigator.clipboard?.writeText(link);
              setCopied(true);
              setTimeout(() => setCopied(false), 1500);
            }}
            className="inline-flex items-center gap-2 bg-white text-primary px-4 py-2 rounded-md font-semibold text-sm"
          >
            <Copy className="w-3.5 h-3.5" /> {copied ? "Copied" : "Copy"}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <Stat icon={Users} label="Referrals" value="0" />
        <Stat icon={DollarSign} label="Earned" value="$0" />
        <Stat icon={Share2} label="Clicks" value="0" />
      </div>

      <div className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] p-6">
        <h3 className="font-semibold mb-4">How it works</h3>
        <ol className="space-y-3 text-sm text-muted-foreground">
          {["Share your unique link", "Friend signs up & upgrades to Pro", "You earn $20 credit"].map((s, i) => (
            <li key={i} className="flex items-start gap-3">
              <span className="w-6 h-6 rounded-full bg-accent text-primary text-xs font-bold flex items-center justify-center shrink-0">
                {i + 1}
              </span>
              <span>{s}</span>
            </li>
          ))}
        </ol>
      </div>
    </>
  );
}

function Stat({ icon: Icon, label, value }: { icon: typeof Users; label: string; value: string }) {
  return (
    <div className="bg-card rounded-2xl p-5 border border-border/60 shadow-[var(--shadow-card)]">
      <Icon className="w-5 h-5 text-primary mb-3" />
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="text-2xl font-bold mt-1">{value}</div>
    </div>
  );
}
