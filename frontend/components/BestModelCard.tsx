import type { BestModel } from "@/lib/api";

export function BestModelCard({
  bestModel,
  recommendation,
}: {
  bestModel: BestModel | null;
  recommendation?: string;
}) {
  return (
    <section className="overflow-hidden rounded-2xl border border-mint/50 bg-gradient-to-br from-[#e9fbf7] via-panel to-[#fff6e7] shadow-soft">
      <div className="lab-strip h-2" />
      <div className="p-5">
        <p className="text-sm font-medium text-muted">Metric overview</p>
        <h2 className="mt-1 text-2xl font-semibold text-ink">{bestModel?.model_name ?? "Loading..."}</h2>
        <p className="mt-2 text-sm text-muted">
          Compare model results across individual metrics.
        </p>
        <p className="mt-4 text-sm leading-6 text-slate-700">{bestModel?.reason}</p>
        {recommendation ? (
          <div className="mt-4 rounded-md border border-mint/50 bg-mint/10 p-4">
            <p className="text-sm font-semibold text-ink">Final Recommendation</p>
            <p className="mt-1 text-sm text-slate-700">{recommendation}</p>
          </div>
        ) : null}
      </div>
    </section>
  );
}
