import type { ExplanationFeature } from "@/lib/api";
import { ShapBarChart } from "@/components/ShapBarChart";

type ModelExplanationCardProps = {
  modelName: string;
  description: string;
  features: ExplanationFeature[];
  summary: string[];
  badge: string;
};

export function ModelExplanationCard({
  modelName,
  description,
  features,
  summary,
  badge,
}: ModelExplanationCardProps) {
  return (
    <section className="rounded-xl border border-white/70 bg-white/92 p-5 shadow-soft">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-accent">{badge}</p>
          <h2 className="mt-1 text-2xl font-semibold text-ink">{modelName}</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">{description}</p>
        </div>
      </div>
      <div className="mt-5">
        <ShapBarChart features={features} />
      </div>
      <div className="mt-5 grid gap-3 md:grid-cols-3">
        {summary.map((item) => (
          <div key={item} className="rounded-lg border border-line bg-slate-50 p-4 text-sm leading-6 text-slate-700">
            {item}
          </div>
        ))}
      </div>
    </section>
  );
}
