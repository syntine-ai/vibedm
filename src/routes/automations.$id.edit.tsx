import { createFileRoute, Link } from "@tanstack/react-router";
import {
  ArrowLeft,
  Zap,
  Instagram,
  MessageSquare,
  Radio,
  AtSign,
  ChevronRight,
  Info,
  Crown,
  Plus,
  Image as ImageIcon,
  Type,
  MessageCircle,
  Play,
} from "lucide-react";
import { useState } from "react";

export const Route = createFileRoute("/automations/$id/edit")({
  head: () => ({ meta: [{ title: "Edit automation — DMFlow" }] }),
  component: EditorPage,
});

const triggers = [
  { id: "comment-post", icon: Instagram, label: "User Comments on your post or reel" },
  { id: "dm", icon: MessageSquare, label: "User DMs to you" },
  { id: "live", icon: Radio, label: "User Comments on your LIVE" },
  { id: "story-reply", icon: MessageCircle, label: "User replies to your stories" },
  { id: "story-mention", icon: AtSign, label: "User mentions you in story", soon: true },
];

function EditorPage() {
  const { id } = Route.useParams();
  const [name, setName] = useState(id === "new" ? "Untitled automation" : "Reel Giveaway — Summer Drop");
  const [active, setActive] = useState(false);
  const [trigger, setTrigger] = useState<string | null>(null);
  const [opening, setOpening] = useState(false);

  return (
    <>
      {/* Top bar */}
      <div className="flex items-center justify-between mb-6 -mt-2">
        <div className="flex items-center gap-3 min-w-0">
          <Link to="/automations" className="w-9 h-9 rounded-md hover:bg-muted flex items-center justify-center shrink-0">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="text-[18px] font-bold bg-transparent outline-none focus:bg-muted px-2 py-1 rounded min-w-0"
          />
        </div>
        <div className="flex items-center gap-2">
          {trigger && (
            <button className="inline-flex items-center gap-1.5 h-10 px-3 rounded-lg border border-border bg-card text-sm font-medium hover:bg-muted">
              <Play className="w-3.5 h-3.5" /> Re-Trigger
            </button>
          )}
          <button
            onClick={() => setActive((v) => !v)}
            disabled={!trigger}
            className={`relative w-11 h-6 rounded-full transition ${active ? "bg-success" : "bg-muted"} ${!trigger ? "opacity-40 cursor-not-allowed" : ""}`}
          >
            <span
              className="absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition"
              style={{ left: active ? "22px" : "2px" }}
            />
          </button>
          <button className="h-10 px-4 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary-dark transition">
            Save Changes
          </button>
        </div>
      </div>

      <div className="max-w-[720px] mx-auto space-y-6">
        {/* Section 1: trigger */}
        <Section
          icon={<div className="w-9 h-9 rounded-lg bg-orange-100 text-orange-500 flex items-center justify-center"><Zap className="w-4 h-4" /></div>}
          title="Select a Trigger"
          subtitle="When to run automation"
        >
          {!trigger ? (
            <div className="space-y-2">
              <div className="text-xs font-medium text-muted-foreground mb-2">Select trigger type</div>
              {triggers.map((t) => {
                const Icon = t.icon;
                return (
                  <button
                    key={t.id}
                    disabled={t.soon}
                    onClick={() => setTrigger(t.id)}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg border border-border bg-card text-left text-sm transition ${t.soon ? "opacity-60 cursor-not-allowed" : "hover:bg-muted"}`}
                  >
                    <Icon className="w-4 h-4 text-primary shrink-0" />
                    <span className="flex-1">{t.label}</span>
                    {t.soon ? (
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-accent text-primary">Coming Soon</span>
                    ) : (
                      <ChevronRight className="w-4 h-4 text-muted-foreground" />
                    )}
                  </button>
                );
              })}
            </div>
          ) : (
            <TriggerDetails trigger={trigger} onClose={() => setTrigger(null)} />
          )}
        </Section>

        {/* Section 2: response */}
        <Section title="Response Flow">
          <ToggleRow
            label="Opening Message"
            hint="Pre-message sent before the main response."
            on={opening}
            onChange={setOpening}
          />
          {opening && (
            <textarea
              className="mt-3 w-full min-h-[100px] p-3 rounded-lg border border-border text-sm outline-none focus:border-primary"
              placeholder="Write the opening message..."
            />
          )}

          <button className="mt-4 w-full h-12 rounded-lg bg-primary text-primary-foreground font-semibold inline-flex items-center justify-center gap-2 hover:bg-primary-dark transition">
            <Plus className="w-4 h-4" /> Add Response
          </button>

          <div className="mt-4 border-t border-border pt-4 flex items-start gap-3">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold">Follow-up Message</span>
                <ProBadge />
              </div>
              <div className="text-xs text-muted-foreground mt-1">
                Send after automation completes (delay: 1min to 23h 30min).
              </div>
              <div className="text-xs mt-1.5" style={{ color: "#d97706" }}>
                ⚠ Available only for Post/Live triggers with Opening Message enabled.
              </div>
            </div>
            <button disabled className="relative w-11 h-6 rounded-full bg-muted opacity-50 cursor-not-allowed">
              <span className="absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white" />
            </button>
          </div>
        </Section>
      </div>
    </>
  );
}

function TriggerDetails({ trigger, onClose }: { trigger: string; onClose: () => void }) {
  const t = triggers.find((x) => x.id === trigger)!;
  const Icon = t.icon;
  return (
    <div>
      <div className="flex items-center gap-3 mb-4 p-3 rounded-lg bg-accent">
        <Icon className="w-4 h-4 text-primary" />
        <span className="flex-1 text-sm font-semibold">{t.label}</span>
        <button onClick={onClose} className="text-xs text-muted-foreground hover:text-foreground">✕</button>
      </div>
      <div className="space-y-3">
        {trigger === "comment-post" && (
          <SubCard icon={<ImageIcon className="w-5 h-5" />} title="Select Post or Reel" hint="Which Post or Reel do you want to use?" />
        )}
        {trigger === "story-reply" && (
          <SubCard icon={<ImageIcon className="w-5 h-5" />} title="Select Story" hint="Which story do you want to use?" />
        )}
        <SubCard icon={<Type className="w-5 h-5" />} title="Setup Keywords" hint="What keywords will start your automation?" />
        {(trigger === "comment-post" || trigger === "live") && (
          <SubCard icon={<MessageCircle className="w-5 h-5" />} title="Setup Comment Replies" hint="What do you want to reply to those comments?" />
        )}
      </div>
    </div>
  );
}

function SubCard({ icon, title, hint }: { icon: React.ReactNode; title: string; hint: string }) {
  return (
    <button className="w-full flex items-center gap-4 p-4 rounded-xl border-2 border-dashed border-border bg-muted/30 hover:bg-muted text-left transition">
      <div className="w-10 h-10 rounded-lg bg-card border border-border flex items-center justify-center text-muted-foreground">
        {icon}
      </div>
      <div className="flex-1">
        <div className="text-xs text-muted-foreground">{hint}</div>
        <div className="text-sm font-semibold mt-0.5">{title}</div>
      </div>
      <ChevronRight className="w-4 h-4 text-muted-foreground" />
    </button>
  );
}

function Section({
  icon,
  title,
  subtitle,
  children,
}: {
  icon?: React.ReactNode;
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] p-6">
      <div className="flex items-start gap-3 mb-5">
        {icon}
        <div>
          <div className="text-base font-bold">{title}</div>
          {subtitle && <div className="text-xs text-muted-foreground mt-0.5">{subtitle}</div>}
        </div>
      </div>
      {children}
    </div>
  );
}

function ToggleRow({
  label,
  hint,
  on,
  onChange,
}: {
  label: string;
  hint?: string;
  on: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1">
        <div className="flex items-center gap-1.5">
          <span className="text-sm font-semibold">{label}</span>
          <Info className="w-3.5 h-3.5 text-muted-foreground" />
        </div>
        {hint && <div className="text-xs text-muted-foreground mt-0.5">{hint}</div>}
      </div>
      <button
        onClick={() => onChange(!on)}
        className={`relative w-11 h-6 rounded-full transition ${on ? "bg-primary" : "bg-muted"}`}
      >
        <span className="absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition" style={{ left: on ? "22px" : "2px" }} />
      </button>
    </div>
  );
}

function ProBadge() {
  return (
    <span
      className="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full"
      style={{ background: "var(--pro-bg)", color: "var(--pro-text)" }}
    >
      <Crown className="w-3 h-3" /> PRO
    </span>
  );
}
