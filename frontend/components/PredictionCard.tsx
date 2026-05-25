import type { PredictionResult } from "@/lib/api";
import { PredictionSourceBadge } from "@/components/PredictionSourceBadge";

export function PredictionCard({
  prediction,
  highlight,
}: {
  prediction: PredictionResult;
  highlight?: boolean;
}) {
  return (
    <article
      className={[
        "rounded-2xl border p-5 shadow-soft",
        highlight ? "border-apricot/50 bg-[#fff6e7]" : "border-white/70 bg-panel/90",
      ].join(" ")}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-muted">Model</p>
          <h3 className="mt-1 text-2xl font-semibold text-ink">{prediction.model_name}</h3>
        </div>
        <div className="flex flex-col items-end gap-2">
          <PredictionSourceBadge prediction={prediction} />
          {highlight ? (
            <span className="rounded-full bg-accent px-3 py-1 text-xs font-semibold text-white">
              Highest risk
            </span>
          ) : null}
        </div>
      </div>
      <div className="mt-5">
        <p className="text-sm text-muted">Churn probability</p>
        <p className="mt-1 text-4xl font-semibold text-ink">
          {(prediction.churn_probability * 100).toFixed(1)}%
        </p>
        <div className="mt-3 h-2 rounded-full bg-slate-200">
          <div
            className="h-2 rounded-full bg-gradient-to-r from-teal-600 via-blue-600 to-amber-500"
            style={{ width: `${prediction.churn_probability * 100}%` }}
          />
        </div>
      </div>
      <div className="mt-5 grid grid-cols-3 gap-3 text-sm">
        <Info label="Label" value={prediction.prediction_label} />
        <Info label="Confidence" value={`${(prediction.confidence * 100).toFixed(1)}%`} />
        <Info label="Inference" value={`${prediction.inference_ms.toFixed(1)} ms`} />
      </div>
      {prediction.message ? <p className="mt-4 text-xs leading-5 text-muted">{prediction.message}</p> : null}
    </article>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-muted">{label}</p>
      <p className="mt-1 font-semibold text-ink">{value}</p>
    </div>
  );
}
