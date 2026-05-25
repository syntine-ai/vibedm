import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/PageHeader";
import { orders } from "@/lib/mock-data";

export const Route = createFileRoute("/orders")({
  head: () => ({ meta: [{ title: "Orders — DMFlow" }] }),
  component: OrdersPage,
});

const statusStyle = {
  completed: { bg: "#dcfce7", color: "#16a34a", label: "Completed" },
  pending: { bg: "#fef3c7", color: "#b45309", label: "Pending" },
  cancelled: { bg: "#fee2e2", color: "#dc2626", label: "Cancelled" },
} as const;

function OrdersPage() {
  return (
    <>
      <PageHeader title="Orders" subtitle="Sales collected through your automations." />

      <div className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] overflow-hidden">
        <div className="p-4 border-b border-border flex items-center gap-2">
          {(["all", "pending", "completed", "cancelled"] as const).map((s, i) => (
            <button
              key={s}
              className={`px-3 py-1.5 rounded-md text-xs font-semibold capitalize ${i === 0 ? "bg-accent text-primary" : "text-muted-foreground hover:bg-muted"}`}
            >
              {s}
            </button>
          ))}
        </div>

        <table className="w-full text-sm">
          <thead>
            <tr className="text-[11px] uppercase tracking-wider text-muted-foreground">
              <th className="text-left font-semibold px-6 py-3">Contact</th>
              <th className="text-left font-semibold px-6 py-3">Product</th>
              <th className="text-left font-semibold px-6 py-3">Amount</th>
              <th className="text-left font-semibold px-6 py-3">Status</th>
              <th className="text-left font-semibold px-6 py-3">Date</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((o) => {
              const s = statusStyle[o.status];
              return (
                <tr key={o.id} className="border-t border-border hover:bg-muted/40 h-14">
                  <td className="px-6 font-semibold text-primary">{o.contact}</td>
                  <td className="px-6">{o.product}</td>
                  <td className="px-6 font-semibold">${o.amount}</td>
                  <td className="px-6">
                    <span className="inline-flex items-center text-[12px] font-medium px-3 py-1 rounded-full" style={{ background: s.bg, color: s.color }}>
                      {s.label}
                    </span>
                  </td>
                  <td className="px-6 text-muted-foreground">{o.date}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}
