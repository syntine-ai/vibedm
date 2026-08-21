import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight, Send, TrendingUp, UserPlus, Workflow } from "lucide-react";

import { PageHeader } from "@/components/PageHeader";
import { useActiveWorkspace, useDashboardQueries } from "@/lib/api/hooks";

export const Route = createFileRoute("/dashboard")({
  head: () => ({ meta: [{ title: "Dashboard - Vibe DM" }] }),
  component: Dashboard,
});

function Dashboard() {
  const { activeWorkspace, meQuery, user } = useActiveWorkspace();
  const dashboard = useDashboardQueries(activeWorkspace?.id);
  const stats = dashboard.stats.data;
  const firstName = user?.first_name || user?.email?.split("@")[0] || "there";

  if (!activeWorkspace) {
    return (
      <>
        <PageHeader
          title={`Welcome, ${firstName}`}
          subtitle="Connect Instagram to create your first workspace."
        />
        <div className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] p-10 text-center">
          <h2 className="text-lg font-semibold">No active workspace</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Finish onboarding from Settings to start using automations.
          </p>
          <Link
            to="/settings"
            className="mt-6 inline-flex items-center justify-center h-11 px-5 rounded-lg bg-primary text-primary-foreground font-semibold"
          >
            Connect Instagram
          </Link>
        </div>
      </>
    );
  }

  const statCards = [
    {
      label: "DMs sent this month",
      value: stats?.dms_sent ?? 0,
      icon: Send,
      accent: "text-primary",
    },
    {
      label: "Active automations",
      value: stats?.active_automations ?? 0,
      icon: Workflow,
      accent: "text-success",
    },
    {
      label: "Contacts captured",
      value: stats?.contacts_captured ?? 0,
      icon: UserPlus,
      accent: "text-primary",
    },
    {
      label: "Revenue",
      value: formatInr(stats?.revenue_paise ?? 0),
      icon: TrendingUp,
      accent: "text-muted-foreground",
    },
  ];

  return (
    <>
      <PageHeader
        title={`Welcome back, ${firstName}`}
        subtitle={`Workspace: ${activeWorkspace.name}`}
        action={
          <Link
            to="/automations/$id/edit"
            params={{ id: "new" }}
            className="inline-flex items-center gap-2 h-10 px-4 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary-dark transition"
          >
            Create Automation <ArrowRight className="size-4" />
          </Link>
        }
      />

      {meQuery.error && <p className="mb-4 text-sm text-destructive">{meQuery.error.message}</p>}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map((card) => {
          const Icon = card.icon;
          return (
            <div
              key={card.label}
              className="bg-card rounded-2xl p-5 shadow-[var(--shadow-card)] border border-border/60"
            >
              <div className="flex items-center justify-between">
                <div className="text-xs text-muted-foreground font-medium">{card.label}</div>
                <Icon className={`size-4 ${card.accent}`} />
              </div>
              <div className="mt-2 text-3xl font-bold">{card.value.toLocaleString()}</div>
            </div>
          );
        })}
      </div>

      <div className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] overflow-hidden">
        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
          <h2 className="text-base font-semibold">Recent activity</h2>
          <Link to="/automations" className="text-xs text-primary font-semibold">
            View automations
          </Link>
        </div>
        <div className="divide-y divide-border">
          {dashboard.activity.data?.map((activity) => (
            <div key={activity.id} className="px-6 py-4 text-sm flex items-center justify-between">
              <div>
                <div className="font-medium">{activity.label}</div>
                <div className="text-xs text-muted-foreground">{activity.type}</div>
              </div>
              <div className="text-xs text-muted-foreground">
                {new Date(activity.created_at).toLocaleString()}
              </div>
            </div>
          ))}
          {dashboard.activity.isLoading && (
            <div className="px-6 py-8 text-sm text-muted-foreground">Loading activity…</div>
          )}
          {!dashboard.activity.isLoading && !dashboard.activity.data?.length && (
            <div className="px-6 py-8 text-sm text-muted-foreground">No recent activity yet.</div>
          )}
        </div>
      </div>
    </>
  );
}

function formatInr(paise: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(paise / 100);
}
