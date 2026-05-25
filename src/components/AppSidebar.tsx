import { Link, useRouterState, useNavigate } from "@tanstack/react-router";
import {
  Home,
  PlayCircle,
  Workflow,
  Users,
  Briefcase,
  Monitor,
  CircleDollarSign,
  Settings,
  Send,
  User as UserIcon,
  Crown,
  LogOut,
  MessageCircle,
  Heart,
} from "lucide-react";
import { user } from "@/lib/mock-data";

type NavItem = {
  label: string;
  icon: typeof Home;
  to: string;
  badge?: string;
};

const nav: NavItem[] = [
  { label: "Home", icon: Home, to: "/dashboard" },
  { label: "Automations", icon: Workflow, to: "/automations" },
  { label: "Settings", icon: Settings, to: "/settings" },
];

export function AppSidebar() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const navigate = useNavigate();
  const initials = (user.firstName[0] + user.lastName[0]).toUpperCase();

  const dmPct = Math.min(100, (user.dmUsage / user.dmLimit) * 100);
  const ctPct = Math.min(100, (user.contactUsage / user.contactLimit) * 100);

  return (
    <aside
      className="w-[260px] shrink-0 bg-sidebar border-r border-border flex flex-col h-screen sticky top-0"
      style={{ boxShadow: "var(--shadow-sidebar)" }}
    >
      {/* Logo */}
      <div className="h-16 flex items-center gap-2 px-5">
        <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center text-primary-foreground">
          <Heart className="w-4 h-4 fill-current" />
        </div>
        <span className="font-bold text-[16px] tracking-tight">DMFlow</span>
      </div>

      {/* User block */}
      <div className="mx-3 mb-3 p-3 rounded-xl bg-muted/60 flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-semibold">
          {initials}
        </div>
        <div className="min-w-0">
          <div className="text-[14px] font-semibold truncate">
            {user.firstName} {user.lastName}
          </div>
          <div className="flex items-center gap-1.5 text-[12px]">
            <span
              className="w-2 h-2 rounded-full"
              style={{ background: user.igConnected ? "var(--success)" : "var(--warning)" }}
            />
            <span className="text-muted-foreground truncate">
              {user.igConnected ? `@${user.igUsername}` : "IG not connected"}
            </span>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 overflow-y-auto">
        <ul className="space-y-1">
          {nav.map((item) => {
            const active =
              item.to === "/dashboard"
                ? pathname === "/dashboard"
                : pathname === item.to || pathname.startsWith(item.to + "/");
            const Icon = item.icon;
            return (
              <li key={item.to}>
                <Link
                  to={item.to}
                  className={[
                    "relative flex items-center gap-3 px-3 py-2.5 rounded-lg text-[14px] transition-colors",
                    active
                      ? "bg-sidebar-active-bg text-sidebar-active-text font-semibold"
                      : "text-foreground/80 hover:bg-muted",
                  ].join(" ")}
                >
                  {active && (
                    <span className="absolute left-0 top-1.5 bottom-1.5 w-[3px] rounded-r bg-primary" />
                  )}
                  <Icon className={["w-[18px] h-[18px]", active ? "text-primary" : "text-muted-foreground"].join(" ")} />
                  <span className="flex-1">{item.label}</span>
                  {item.badge && (
                    <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-warning text-warning-foreground">
                      {item.badge}
                    </span>
                  )}
                </Link>
              </li>
            );
          })}
        </ul>

        {/* Usage meters */}
        <div className="mt-6 space-y-4 px-1">
          <Meter icon={<Send className="w-3.5 h-3.5" />} label={`${user.dmUsage}/${user.dmLimit} DM per month`} pct={dmPct} />
          <Meter icon={<UserIcon className="w-3.5 h-3.5" />} label={`${user.contactUsage}/${user.contactLimit} contacts per month`} pct={ctPct} />
        </div>
      </nav>

      {/* Footer */}
      <div className="p-3 space-y-2 border-t border-border">
        <button onClick={() => navigate({ to: "/login" })} className="w-full flex items-center justify-center gap-2 px-3 py-2 text-[13px] text-muted-foreground hover:text-foreground transition">
          <LogOut className="w-4 h-4" />
          Logout
        </button>
        <button className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-lg text-white text-[13px] font-semibold hover:opacity-90 transition" style={{ background: "var(--whatsapp)" }}>
          <MessageCircle className="w-4 h-4" />
          Support / Feedback
        </button>
      </div>
    </aside>
  );
}

function Meter({ icon, label, pct }: { icon: React.ReactNode; label: string; pct: number }) {
  return (
    <div>
      <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground mb-1.5">
        {icon}
        <span>{label}</span>
      </div>
      <div className="h-1.5 rounded-full bg-muted overflow-hidden">
        <div className="h-full bg-primary rounded-full" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
