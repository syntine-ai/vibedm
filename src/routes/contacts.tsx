import { createFileRoute } from "@tanstack/react-router";
import { Download, Plus, Trash2, Upload } from "lucide-react";
import { useState } from "react";

import { FormField } from "@/components/FormField";
import { PageHeader } from "@/components/PageHeader";
import {
  useActiveWorkspace,
  useContactMutation,
  useContactsQuery,
  useDeleteContactMutation,
  useUpdateContactMutation,
} from "@/lib/api/hooks";
import { contactApi } from "@/lib/api/resources";
import type { Contact } from "@/lib/api/types";

export const Route = createFileRoute("/contacts")({
  validateSearch: (search) => ({
    source_automation_id:
      typeof search.source_automation_id === "string" ? search.source_automation_id : undefined,
    tag: typeof search.tag === "string" ? search.tag : undefined,
    q: typeof search.q === "string" ? search.q : undefined,
  }),
  head: () => ({ meta: [{ title: "Contacts - Vibe DM" }] }),
  component: ContactsPage,
});

function ContactsPage() {
  const search = Route.useSearch();
  const { activeWorkspace } = useActiveWorkspace();
  const [q, setQ] = useState(search.q ?? "");
  const [tag, setTag] = useState(search.tag ?? "");
  const contactsQuery = useContactsQuery(activeWorkspace?.id, {
    q,
    tag,
    source_automation_id: search.source_automation_id,
  });
  const createMutation = useContactMutation(activeWorkspace?.id);
  const updateMutation = useUpdateContactMutation(activeWorkspace?.id);
  const deleteMutation = useDeleteContactMutation(activeWorkspace?.id);
  const [editing, setEditing] = useState<Contact | null>(null);
  const [form, setForm] = useState({ ig_username: "", name: "", email: "", phone: "", tags: "" });

  const resetForm = () => {
    setEditing(null);
    setForm({ ig_username: "", name: "", email: "", phone: "", tags: "" });
  };

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const body = {
      ig_username: form.ig_username || null,
      name: form.name || null,
      email: form.email || null,
      phone: form.phone || null,
      tags: form.tags
        .split(",")
        .flatMap((value) => {
          const trimmed = value.trim();
          return trimmed ? [trimmed] : [];
        }),
    };
    if (editing) {
      await updateMutation.mutateAsync({ contactId: editing.id, body });
    } else {
      await createMutation.mutateAsync(body);
    }
    resetForm();
  };

  const exportCsv = async () => {
    if (!activeWorkspace?.id) return;
    const csv = await contactApi.exportCsv(activeWorkspace.id);
    const url = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = "contacts.csv";
    link.click();
    URL.revokeObjectURL(url);
  };

  const importCsv = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file || !activeWorkspace?.id) return;
    await contactApi.importCsv(activeWorkspace.id, file);
    await contactsQuery.refetch();
    event.target.value = "";
  };

  return (
    <>
      <PageHeader
        title="Contacts"
        subtitle={
          search.source_automation_id
            ? "Filtered by automation source."
            : "Workspace-scoped captured leads."
        }
        action={
          <div className="flex gap-2">
            <button
              type="button"
              onClick={exportCsv}
              className="inline-flex items-center gap-2 h-10 px-4 rounded-lg border border-border text-sm font-semibold"
            >
              <Download className="size-4" /> Export
            </button>
            <label className="inline-flex items-center gap-2 h-10 px-4 rounded-lg border border-border text-sm font-semibold cursor-pointer">
              <Upload className="size-4" /> Import
              <input type="file" accept=".csv,text/csv" className="hidden" onChange={importCsv} />
            </label>
          </div>
        }
      />

      <div className="grid grid-cols-1 xl:grid-cols-[1fr_360px] gap-6">
        <div className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] overflow-hidden">
          <div className="p-4 flex flex-wrap gap-3 border-b border-border">
            <input
              value={q}
              onChange={(event) => setQ(event.target.value)}
              placeholder="Search name, email, phone, username"
              className="h-10 px-3 rounded-lg border border-border bg-card text-sm outline-none min-w-[260px]"
            />
            <input
              value={tag}
              onChange={(event) => setTag(event.target.value)}
              placeholder="Filter by tag"
              className="h-10 px-3 rounded-lg border border-border bg-card text-sm outline-none"
            />
          </div>

          <table className="w-full text-sm">
            <thead>
              <tr className="text-[11px] uppercase tracking-wider text-muted-foreground">
                <th className="text-left font-semibold px-6 py-3">Instagram</th>
                <th className="text-left font-semibold px-6 py-3">Name</th>
                <th className="text-left font-semibold px-6 py-3">Email</th>
                <th className="text-left font-semibold px-6 py-3">Phone</th>
                <th className="text-right font-semibold px-6 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {contactsQuery.data?.map((contact) => (
                <tr key={contact.id} className="border-t border-border hover:bg-muted/40">
                  <td className="px-6 py-4 font-medium">
                    {contact.ig_username ? `@${contact.ig_username}` : "-"}
                  </td>
                  <td className="px-6 py-4">{contact.name ?? "-"}</td>
                  <td className="px-6 py-4 text-muted-foreground">{contact.email ?? "-"}</td>
                  <td className="px-6 py-4 text-muted-foreground">{contact.phone ?? "-"}</td>
                  <td className="px-6 py-4">
                    <div className="flex justify-end gap-2">
                      <button
                        type="button"
                        onClick={() => {
                          setEditing(contact);
                          setForm({
                            ig_username: contact.ig_username ?? "",
                            name: contact.name ?? "",
                            email: contact.email ?? "",
                            phone: contact.phone ?? "",
                            tags: contact.tags?.join(", ") ?? "",
                          });
                        }}
                        className="text-xs font-semibold text-primary"
                      >
                        Edit
                      </button>
                      <button
                        type="button"
                        aria-label="Delete contact"
                        onClick={() => deleteMutation.mutate(contact.id)}
                        className="text-destructive"
                      >
                        <Trash2 className="size-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {contactsQuery.isLoading && (
            <div className="px-6 py-8 text-sm text-muted-foreground">Loading contacts...</div>
          )}
          {!contactsQuery.isLoading && !contactsQuery.data?.length && (
            <div className="px-6 py-8 text-sm text-muted-foreground">No contacts found.</div>
          )}
        </div>

        <form
          onSubmit={submit}
          className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] p-6 h-fit"
        >
          <h3 className="font-semibold flex items-center gap-2">
            <Plus className="size-4" /> {editing ? "Edit contact" : "Create contact"}
          </h3>
          <div className="mt-5 space-y-3">
            <FormField label="Instagram username">
              <input
                className="ipt"
                value={form.ig_username}
                onChange={(event) =>
                  setForm((current) => ({ ...current, ig_username: event.target.value }))
                }
              />
            </FormField>
            <FormField label="Name">
              <input
                className="ipt"
                value={form.name}
                onChange={(event) =>
                  setForm((current) => ({ ...current, name: event.target.value }))
                }
              />
            </FormField>
            <FormField label="Email">
              <input
                className="ipt"
                type="email"
                value={form.email}
                onChange={(event) =>
                  setForm((current) => ({ ...current, email: event.target.value }))
                }
              />
            </FormField>
            <FormField label="Phone">
              <input
                className="ipt"
                value={form.phone}
                onChange={(event) =>
                  setForm((current) => ({ ...current, phone: event.target.value }))
                }
              />
            </FormField>
            <FormField label="Tags">
              <input
                className="ipt"
                value={form.tags}
                onChange={(event) =>
                  setForm((current) => ({ ...current, tags: event.target.value }))
                }
                placeholder="lead, giveaway"
              />
            </FormField>
          </div>
          <div className="mt-5 flex gap-2">
            <button type="submit" className="h-10 px-4 rounded-lg bg-primary text-primary-foreground text-sm font-semibold">
              {editing ? "Save" : "Create"}
            </button>
            {editing && (
              <button
                type="button"
                onClick={resetForm}
                className="h-10 px-4 rounded-lg border border-border text-sm font-semibold"
              >
                Cancel
              </button>
            )}
          </div>
          <InputStyles />
        </form>
      </div>
    </>
  );
}

export function InputStyles() {
  return (
    <style>{`.ipt { width:100%; height:42px; padding:0 12px; border:1px solid var(--border); border-radius:10px; font-size:14px; outline:none; background:var(--surface); }
.ipt:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(61,58,238,0.12); }`}</style>
  );
}
