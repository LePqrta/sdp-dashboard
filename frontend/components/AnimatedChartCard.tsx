import type { ReactNode } from "react";

export function AnimatedChartCard({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <section className="research-card fade-in rounded-2xl p-5 transition-transform duration-200 hover:-translate-y-1">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-ink">{title}</h2>
        {description ? <p className="mt-1 text-sm text-muted">{description}</p> : null}
      </div>
      {children}
    </section>
  );
}
