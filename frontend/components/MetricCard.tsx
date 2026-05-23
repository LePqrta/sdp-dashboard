import type { ModelMetrics } from "@/lib/api";

type MetricCardProps = {
  metrics: ModelMetrics;
  isBest?: boolean;
};

export function MetricCard({ metrics, isBest }: MetricCardProps) {
  return (
    <section className="research-card rounded-2xl p-5 transition-transform duration-200 hover:-translate-y-1">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-muted">Model</p>
          <h3 className="mt-1 text-2xl font-semibold text-ink">{metrics.model_name}</h3>
        </div>
        {isBest ? (
          <span className="rounded-full bg-[#fff8e8] px-3 py-1 text-xs font-semibold text-amber-700 ring-1 ring-amber-200">
            Best global
          </span>
        ) : null}
      </div>
      <div className="mt-5 grid grid-cols-2 gap-3 text-sm">
        <Metric label="Accuracy" value={metrics.accuracy} tone="bg-blue-50 text-blue-700" />
        <Metric label="ROC-AUC" value={metrics.roc_auc} tone="bg-teal-50 text-teal-700" />
        <Metric label="F1-score" value={metrics.f1_score} tone="bg-amber-50 text-amber-700" />
        <Metric label="Recall" value={metrics.recall} tone="bg-violet-50 text-violet-700" />
      </div>
      <div className="mt-4 border-t border-line pt-4 text-sm text-muted">
        {metrics.model_size_mb} MB · {metrics.average_inference_ms} ms avg · threshold{" "}
        {metrics.threshold}
      </div>
    </section>
  );
}

function Metric({ label, value, tone }: { label: string; value: number; tone: string }) {
  return (
    <div className={`rounded-lg p-3 ${tone}`}>
      <p className="text-xs font-semibold uppercase tracking-wide opacity-80">{label}</p>
      <p className="text-lg font-semibold text-ink">{(value * 100).toFixed(1)}%</p>
    </div>
  );
}
