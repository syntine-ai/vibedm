import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { ImageIcon, Instagram, MoreHorizontal, Pencil, Plus, Trash2 } from "lucide-react";
import { useState } from "react";

import { PageHeader } from "@/components/PageHeader";
import {
  hasInstagramConnection,
  useActiveWorkspace,
  useAutomationsQuery,
  useCreateAutomationMutation,
  useDeleteAutomationMutation,
} from "@/lib/api/hooks";
import type { AutomationFilters } from "@/lib/api/resources";
import type { TriggerType } from "@/lib/api/types";

export const Route = createFileRoute("/automations/")({
  head: () => ({ meta: [{ title: "Automations - DMFlow" }] }),
  component: AutomationsPage,
});

function AutomationsPage() {
  const navigate = useNavigate({ from: "/automations" });
  const { activeWorkspace } = useActiveWorkspace();
  const [filters, setFilters] = useState<AutomationFilters>({});
  const automationsQuery = useAutomationsQuery(activeWorkspace?.id, filters);
  const createMutation = useCreateAutomationMutation(activeWorkspace?.id);
  const deleteMutation = useDeleteAutomationMutation(activeWorkspace?.id);

  const createAutomation = async () => {
    const automation = await createMutation.mutateAsync({ name: "Untitled automation" });
    navigate({ to: "/automations/$id/edit", params: { id: automation.id } });
  };

  if (!hasInstagramConnection(activeWorkspace)) return <NotConnected />;

  return (
    <>
      <PageHeader
        title="Automations"
        action={
          <button
            onClick={createAutomation}
            disabled={createMutation.isPending}
            className="inline-flex items-center gap-2 h-10 px-4 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary-dark transition disabled:opacity-60"
          >
            <Plus className="w-4 h-4" /> {createMutation.isPending ? "Creating..." : "Create"}
          </button>
        }
      />

      <div className="mb-4 flex flex-wrap gap-3">
        <input
          value={filters.q ?? ""}
          onChange={(event) => setFilters((current) => ({ ...current, q: event.target.value }))}
          placeholder="Search automations"
          className="h-10 px-3 rounded-lg border border-border bg-card text-sm outline-none"
        />
        <select
          value={filters.status ?? ""}
          onChange={(event) =>
            setFilters((current) => ({ ...current, status: event.target.value }))
          }
          className="h-10 px-3 rounded-lg border border-border bg-card text-sm"
        >
          <option value="">All statuses</option>
          <option value="draft">Draft</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
        <select
          value={filters.trigger_type ?? ""}
          onChange={(event) =>
            setFilters((current) => ({
              ...current,
              trigger_type: event.target.value as TriggerType | "",
            }))
          }
          className="h-10 px-3 rounded-lg border border-border bg-card text-sm"
        >
          <option value="">All triggers</option>
          <option value="comment_post">Comment post/reel</option>
          <option value="dm">DM</option>
          <option value="live_comment">Live comment</option>
          <option value="story_reply">Story reply</option>
        </select>
      </div>

      <div className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-[11px] uppercase tracking-wider text-muted-foreground">
              <th className="text-left font-semibold px-6 py-3 w-20">Image</th>
              <th className="text-left font-semibold px-6 py-3">Name</th>
              <th className="text-left font-semibold px-6 py-3 w-36">Status</th>
              <th className="text-left font-semibold px-6 py-3 w-48">Trigger</th>
              <th className="text-right font-semibold px-6 py-3 w-56">Actions</th>
            </tr>
          </thead>
          <tbody>
            {automationsQuery.data?.map((automation) => (
              <tr key={automation.id} className="border-t border-border hover:bg-muted/40 h-16">
                <td className="px-6">
                  <div className="w-12 h-12 rounded-lg bg-muted flex items-center justify-center">
                    <ImageIcon className="w-5 h-5 text-muted-foreground" />
                  </div>
                </td>
                <td className="px-6 font-semibold">{automation.name}</td>
                <td className="px-6">
                  <StatusPill status={automation.status} />
                </td>
                <td className="px-6 text-muted-foreground">
                  {formatTrigger(automation.trigger_type)}
                </td>
                <td className="px-6">
                  <div className="flex items-center justify-end gap-2">
                    <Link
                      to="/contacts"
                      search={{ source_automation_id: automation.id }}
                      className="text-xs font-semibold text-primary border border-primary/30 px-3 py-1.5 rounded-md hover:bg-accent transition"
                    >
                      Leads Data
                    </Link>
                    <Link
                      to="/automations/$id/edit"
                      params={{ id: automation.id }}
                      className="w-8 h-8 rounded-md hover:bg-muted flex items-center justify-center"
                    >
                      <Pencil className="w-4 h-4 text-muted-foreground" />
                    </Link>
                    <button
                      onClick={() => deleteMutation.mutate(automation.id)}
                      className="w-8 h-8 rounded-md hover:bg-muted flex items-center justify-center"
                    >
                      <Trash2 className="w-4 h-4 text-muted-foreground" />
                    </button>
                    <button className="w-8 h-8 rounded-md hover:bg-muted flex items-center justify-center">
                      <MoreHorizontal className="w-4 h-4 text-muted-foreground" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {automationsQuery.isLoading && (
          <div className="px-6 py-8 text-sm text-muted-foreground">Loading automations...</div>
        )}
        {!automationsQuery.isLoading && !automationsQuery.data?.length && (
          <div className="px-6 py-8 text-sm text-muted-foreground">No automations found.</div>
        )}
      </div>
    </>
  );
}

function NotConnected() {
  return (
    <>
      <PageHeader title="Automations" />
      <div className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] p-16 text-center">
        <div className="w-16 h-16 mx-auto rounded-2xl bg-accent flex items-center justify-center mb-5">
          <Instagram className="w-8 h-8 text-primary" />
        </div>
        <h2 className="text-lg font-semibold mb-2">Connect Instagram to view automations</h2>
        <p className="text-sm text-muted-foreground max-w-md mx-auto mb-6">
          Your automation list, editor access, and create actions stay hidden until an Instagram
          account is connected.
        </p>
        <Link
          to="/settings"
          className="inline-flex items-center justify-center h-12 px-6 min-w-[200px] rounded-lg bg-primary text-primary-foreground font-semibold hover:bg-primary-dark transition"
        >
          Connect Instagram
        </Link>
      </div>
    </>
  );
}

function StatusPill({ status }: { status: string }) {
  const active = status === "active";
  return (
    <span
      className="inline-flex items-center gap-1.5 text-[12px] font-medium px-3 py-1 rounded-full"
      style={
        active
          ? { background: "#dcfce7", color: "#16a34a" }
          : { background: "#f1f5f9", color: "#64748b" }
      }
    >
      <span
        className="w-1.5 h-1.5 rounded-full"
        style={{ background: active ? "#22c55e" : "#94a3b8" }}
      />
      {status}
    </span>
  );
}

function formatTrigger(trigger: TriggerType | null | undefined) {
  if (!trigger) return "Not configured";
  return trigger
    .split("_")
    .map((word) => word[0]?.toUpperCase() + word.slice(1))
    .join(" ");
}
