import type { PredictionResult } from "@/lib/api";
import { PredictionSourceBadge } from "@/components/PredictionSourceBadge";

export function ProbabilityChart({ predictions }: { predictions: PredictionResult[] }) {
  return (
    <div className="space-y-4 py-2">
      {predictions.map((item) => {
        const probability = item.churn_probability * 100;
        return (
          <div key={item.model_name} className="rounded-xl border border-line bg-panel/70 p-4">
            <div className="mb-3 flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-ink">{item.model_name}</p>
                <p className="text-xs text-muted">{item.prediction_label}</p>
              </div>
              <div className="flex flex-col items-end gap-2">
                <PredictionSourceBadge prediction={item} />
                <p className="text-xl font-semibold text-ink">{probability.toFixed(1)}%</p>
              </div>
            </div>
            <div className="h-3 rounded-full bg-vellum">
              <div
                className="h-3 rounded-full bg-gradient-to-r from-[#84ccc5] via-[#2f7d78] to-[#d99145] animate-width-in"
                style={{ width: `${probability}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
