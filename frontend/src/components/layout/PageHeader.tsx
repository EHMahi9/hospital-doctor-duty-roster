import type { ReactNode } from "react";

export function PageHeader({ title, eyebrow, actions }: { title: string; eyebrow?: string; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div>
        {eyebrow ? <p className="mb-1 text-sm font-medium text-primary">{eyebrow}</p> : null}
        <h2 className="text-2xl font-bold tracking-normal text-foreground md:text-3xl">{title}</h2>
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
    </div>
  );
}
