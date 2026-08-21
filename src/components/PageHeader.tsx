import type { ReactNode } from "react";

export function PageHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-4 mb-6">
      <div>
        <h1 className="text-[28px] font-bold tracking-tight">{title}</h1>
        {subtitle && <p className="text-[14px] text-muted-foreground mt-1">{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}
