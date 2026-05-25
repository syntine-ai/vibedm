import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/PageHeader";
import { PlayCircle } from "lucide-react";

export const Route = createFileRoute("/learn")({
  component: () => (
    <>
      <PageHeader title="Learn" subtitle="Short tutorials to get the most out of DMFlow." />
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="bg-card rounded-2xl overflow-hidden border border-border/60 shadow-[var(--shadow-card)]">
            <div className="aspect-video bg-muted flex items-center justify-center">
              <PlayCircle className="w-12 h-12 text-primary" />
            </div>
            <div className="p-4">
              <div className="text-sm font-semibold">Lesson {i + 1}</div>
              <div className="text-xs text-muted-foreground mt-1">Set up your first automation in under 3 minutes.</div>
            </div>
          </div>
        ))}
      </div>
    </>
  ),
});
