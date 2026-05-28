import type { ReactNode } from "react";

type PageHeaderProps = {
  eyebrow: string;
  title: string;
  description?: string;
  actions?: ReactNode;
};

export function PageHeader({ eyebrow, title, description, actions }: PageHeaderProps) {
  return (
    <header className="research-card mb-8 overflow-hidden rounded-2xl">
      <div className="lab-strip h-2" />
      <div className="flex flex-col gap-5 p-6 lg:flex-row lg:items-end lg:justify-between lg:p-8">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.22em] text-accent">{eyebrow}</p>
        <h1 className="mt-3 max-w-4xl text-3xl font-semibold tracking-tight text-ink sm:text-5xl">
          {title}
        </h1>
        {description ? <p className="mt-3 max-w-3xl text-base leading-7 text-muted">{description}</p> : null}
      </div>
      {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
      </div>
    </header>
  );
}
