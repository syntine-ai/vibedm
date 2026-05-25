import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/PageHeader";
import { Plus, ExternalLink, ImageIcon } from "lucide-react";
import { products } from "@/lib/mock-data";

export const Route = createFileRoute("/products")({
  head: () => ({ meta: [{ title: "Products — DMFlow" }] }),
  component: ProductsPage,
});

function ProductsPage() {
  return (
    <>
      <PageHeader
        title="Products"
        subtitle="Items you can link inside DM responses."
        action={
          <button className="inline-flex items-center gap-2 h-10 px-4 rounded-lg bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary-dark transition">
            <Plus className="w-4 h-4" /> Add Product
          </button>
        }
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {products.map((p) => (
          <div key={p.id} className="bg-card rounded-2xl border border-border/60 shadow-[var(--shadow-card)] overflow-hidden hover:shadow-md transition">
            <div className="aspect-square bg-muted flex items-center justify-center">
              <ImageIcon className="w-10 h-10 text-muted-foreground" />
            </div>
            <div className="p-4">
              <div className="font-semibold text-sm">{p.name}</div>
              <div className="flex items-center justify-between mt-2">
                <div className="text-lg font-bold text-primary">${p.price}</div>
                <a href={p.link} className="text-xs text-muted-foreground inline-flex items-center gap-1 hover:text-foreground">
                  Link <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
