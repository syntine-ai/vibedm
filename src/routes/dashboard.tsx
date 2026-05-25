import { createFileRoute, Link } from "@tanstack/react-router";
import { PageHeader } from "@/components/PageHeader";
import { ArrowRight, Send, Workflow, TrendingUp } from "lucide-react";
import { automations, user } from "@/lib/mock-data";

export const Route = createFileRoute("/dashboard")({
  head: () => ({ meta: [{ title: "Dashboard — DMFlow" }] }),
  component: Dashboard,
});

function Dashboard() {
  const stats = [
    { label: "DMs sent this month", value: user.dmUsage.toLocaleString(), icon: Send, accent: "text-primary" },
    { label: "Active automations", value: automations.filter((a) => a.status === "active").length, icon: Workflow, accent: "text-success" },
    { label: "Conversion rate", value: "—", icon: TrendingUp, accent: "text-muted-foreground" },
  ];

  return (
    <>
      <PageHeader
        title={`Welcome back, ${user.firstName}`}
        subtitle="Here's how your automations are performing this month."
        action={
          <Link
            to="/automations/$id/edit"
            params={{ id: "new" }}
            className="inline-flex items-center gap-2 h-10 px-4 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary-dark transition"
          >
            Create Automation <ArrowRight className="w-4 h-4" />
          </Link>
        }
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map((s) => {
          const Icon = s.icon;
          return (
            <div key={s.label} className="bg-card rounded-2xl p-5 shadow-[var(--shadow-card)] border border-border/60">
              <div className="flex items-center justify-between">
                <div className="text-xs text-muted-foreground font-medium">{s.label}</div>
                <Icon className={`w-4 h-4 ${s.accent}`} />
              </div>
              <div className="mt-2 flex items-end gap-2">
                <div className="text-3xl font-bold">{s.value}</div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] overflow-hidden">
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <h2 className="text-base font-semibold">Recent automations</h2>
          <Link to="/automations" className="text-xs text-primary font-semibold">View all</Link>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-[11px] uppercase tracking-wider text-muted-foreground">
              <th className="text-left font-semibold px-6 py-3">Name</th>
              <th className="text-left font-semibold px-6 py-3">Status</th>
              <th className="text-left font-semibold px-6 py-3">Last modified</th>
            </tr>
          </thead>
          <tbody>
            {automations.slice(0, 3).map((a) => (
              <tr key={a.id} className="border-t border-border hover:bg-muted/40">
                <td className="px-6 py-4 font-medium">{a.name}</td>
                <td className="px-6 py-4">
                  <StatusPill active={a.status === "active"} />
                </td>
                <td className="px-6 py-4 text-muted-foreground">{a.modifiedAt}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

function StatusPill({ active }: { active: boolean }) {
  return (
    <span
      className="inline-flex items-center gap-1.5 text-[12px] font-medium px-3 py-1 rounded-full"
      style={
        active
          ? { background: "#dcfce7", color: "#16a34a" }
          : { background: "#f1f5f9", color: "#64748b" }
      }
    >
      <span className="w-1.5 h-1.5 rounded-full" style={{ background: active ? "#22c55e" : "#94a3b8" }} />
      {active ? "Active" : "Inactive"}
    </span>
  );
}
