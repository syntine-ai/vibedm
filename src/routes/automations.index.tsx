import { createFileRoute, Link } from "@tanstack/react-router";
import { PageHeader } from "@/components/PageHeader";
import { Plus, ImageIcon, Pencil, MoreHorizontal, Instagram } from "lucide-react";
import { automations, user } from "@/lib/mock-data";

export const Route = createFileRoute("/automations/")({
  head: () => ({ meta: [{ title: "Automations — DMFlow" }] }),
  component: AutomationsPage,
});

function AutomationsPage() {
  if (!user.igConnected) return <NotConnected />;
  return (
    <>
      <PageHeader
        title="Automations"
        action={
          <Link
            to="/automations/$id/edit"
            params={{ id: "new" }}
            className="inline-flex items-center gap-2 h-10 px-4 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary-dark transition"
          >
            <Plus className="w-4 h-4" /> Create
          </Link>
        }
      />

      <div className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-[11px] uppercase tracking-wider text-muted-foreground">
              <th className="text-left font-semibold px-6 py-3 w-20">Image</th>
              <th className="text-left font-semibold px-6 py-3">Name</th>
              <th className="text-left font-semibold px-6 py-3 w-36">Status</th>
              <th className="text-left font-semibold px-6 py-3 w-40">Created</th>
              <th className="text-left font-semibold px-6 py-3 w-40">Last modified</th>
              <th className="text-right font-semibold px-6 py-3 w-48">Actions</th>
            </tr>
          </thead>
          <tbody>
            {automations.map((a) => (
              <tr key={a.id} className="border-t border-border hover:bg-muted/40 h-16">
                <td className="px-6">
                  <div className="w-12 h-12 rounded-lg bg-muted flex items-center justify-center">
                    <ImageIcon className="w-5 h-5 text-muted-foreground" />
                  </div>
                </td>
                <td className="px-6 font-semibold">{a.name}</td>
                <td className="px-6">
                  <StatusPill active={a.status === "active"} />
                </td>
                <td className="px-6 text-muted-foreground">{a.createdAt}</td>
                <td className="px-6 text-muted-foreground">{a.modifiedAt}</td>
                <td className="px-6">
                  <div className="flex items-center justify-end gap-2">
                    <button className="text-xs font-semibold text-primary border border-primary/30 px-3 py-1.5 rounded-md hover:bg-accent transition">
                      Leads Data
                    </button>
                    <Link
                      to="/automations/$id/edit"
                      params={{ id: a.id }}
                      className="w-8 h-8 rounded-md hover:bg-muted flex items-center justify-center"
                    >
                      <Pencil className="w-4 h-4 text-muted-foreground" />
                    </Link>
                    <button className="w-8 h-8 rounded-md hover:bg-muted flex items-center justify-center">
                      <MoreHorizontal className="w-4 h-4 text-muted-foreground" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <div className="flex items-center justify-between px-6 py-3 border-t border-border text-xs text-muted-foreground">
          <div>Showing 1–{automations.length} of {automations.length}</div>
          <div className="flex items-center gap-2">
            <span>Rows per page</span>
            <select className="border border-border rounded-md px-2 py-1 bg-card">
              <option>10</option>
              <option>25</option>
            </select>
          </div>
        </div>
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
          Your automation list, editor access, and create actions stay hidden until an Instagram account is connected.
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

function StatusPill({ active }: { active: boolean }) {
  return (
    <span
      className="inline-flex items-center gap-1.5 text-[12px] font-medium px-3 py-1 rounded-full"
      style={active ? { background: "#dcfce7", color: "#16a34a" } : { background: "#f1f5f9", color: "#64748b" }}
    >
      <span className="w-1.5 h-1.5 rounded-full" style={{ background: active ? "#22c55e" : "#94a3b8" }} />
      {active ? "Active" : "Inactive"}
    </span>
  );
}
