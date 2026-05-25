import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/PageHeader";
import { Search, Download, Crown } from "lucide-react";
import { contacts } from "@/lib/mock-data";

export const Route = createFileRoute("/contacts")({
  head: () => ({ meta: [{ title: "Contacts — DMFlow" }] }),
  component: ContactsPage,
});

function ContactsPage() {
  return (
    <>
      <PageHeader
        title="Contacts"
        subtitle="People collected from your automations."
        action={
          <button className="inline-flex items-center gap-2 h-10 px-4 rounded-lg border border-border bg-card text-sm font-semibold opacity-60 cursor-not-allowed">
            <Download className="w-4 h-4" /> Export CSV
            <span className="inline-flex items-center gap-1 text-[10px] font-bold px-1.5 py-0.5 rounded-full ml-1" style={{ background: "var(--pro-bg)", color: "var(--pro-text)" }}>
              <Crown className="w-3 h-3" /> PRO
            </span>
          </button>
        }
      />

      <div className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] overflow-hidden">
        <div className="p-4 border-b border-border">
          <div className="relative max-w-sm">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input placeholder="Search contacts..." className="w-full h-10 pl-9 pr-3 rounded-lg border border-border bg-card text-sm outline-none focus:border-primary" />
          </div>
        </div>

        <table className="w-full text-sm">
          <thead>
            <tr className="text-[11px] uppercase tracking-wider text-muted-foreground">
              <th className="text-left font-semibold px-6 py-3">IG Username</th>
              <th className="text-left font-semibold px-6 py-3">Name</th>
              <th className="text-left font-semibold px-6 py-3">Phone</th>
              <th className="text-left font-semibold px-6 py-3">Email</th>
              <th className="text-left font-semibold px-6 py-3">Source</th>
              <th className="text-left font-semibold px-6 py-3">Date</th>
            </tr>
          </thead>
          <tbody>
            {contacts.map((c) => (
              <tr key={c.id} className="border-t border-border hover:bg-muted/40 h-14">
                <td className="px-6 font-semibold text-primary">@{c.username}</td>
                <td className="px-6">{c.name}</td>
                <td className="px-6 text-muted-foreground">{c.phone || "—"}</td>
                <td className="px-6 text-muted-foreground">{c.email || "—"}</td>
                <td className="px-6 text-muted-foreground">{c.source}</td>
                <td className="px-6 text-muted-foreground">{c.date}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
