import type { ModelExplanation } from "@/lib/api";
import { ShapBarChart } from "@/components/ShapBarChart";

type ModelExplanationCardProps = {
  explanation: ModelExplanation;
};

export function ModelExplanationCard({ explanation }: ModelExplanationCardProps) {
  const probability =
    typeof explanation.churn_probability === "number"
      ? `${(explanation.churn_probability * 100).toFixed(1)}%`
      : "N/A";
  const details = [
    `Type: ${formatExplanationType(explanation.explanation_type)}`,
    `Probability: ${probability}`,
  ];

  return (
    <section className="rounded-xl border border-white/70 bg-white/92 p-5 shadow-soft">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-accent">Model-derived local importance</p>
          <h2 className="mt-1 text-2xl font-semibold text-ink">{explanation.model}</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
            Top model factors for this customer with model-derived local importance.
          </p>
        </div>
        {explanation.prediction_label ? (
          <span className="rounded-full border border-line bg-slate-50 px-3 py-1 text-xs font-semibold text-ink">
            {explanation.prediction_label}
          </span>
        ) : null}
      </div>
      <div className="mt-5">
        <ShapBarChart features={explanation.top_features} />
      </div>
      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        {details.map((item) => (
          <div key={item} className="rounded-lg border border-line bg-slate-50 p-4 text-sm leading-6 text-slate-700">
            {item}
          </div>
        ))}
      </div>
      {[...explanation.notes, ...explanation.warnings].length ? (
        <div className="mt-4 space-y-2">
          {[...explanation.notes, ...explanation.warnings].map((item) => (
            <p key={item} className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs leading-5 text-amber-800">
              {item}
            </p>
          ))}
        </div>
      ) : null}
    </section>
  );
}

function formatExplanationType(value: string) {
  return value.replace(/_/g, " ");
}
