import type { PredictionResult } from "@/lib/api";
import { PredictionSourceBadge } from "@/components/PredictionSourceBadge";

export function PredictionTable({
  predictions,
  highlightedModel,
}: {
  predictions: PredictionResult[];
  highlightedModel?: string;
}) {
  if (!predictions.length) {
    return null;
  }

  return (
    <section className="research-card rounded-2xl p-5">
      <h2 className="text-xl font-semibold text-ink">Prediction Results</h2>
      <div className="mt-4 overflow-x-auto">
        <table className="min-w-full text-left text-sm">
          <thead>
            <tr className="border-b border-line text-muted">
              <th className="py-3 pr-4 font-semibold">Model</th>
              <th className="py-3 pr-4 font-semibold">Churn Probability</th>
              <th className="py-3 pr-4 font-semibold">Prediction</th>
              <th className="py-3 pr-4 font-semibold">Confidence</th>
              <th className="py-3 pr-4 font-semibold">Inference</th>
              <th className="py-3 pr-4 font-semibold">Source</th>
            </tr>
          </thead>
          <tbody>
            {predictions.map((item) => {
              const highlighted = item.model_name === highlightedModel;
              return (
                <tr
                  key={item.model_name}
                  className={highlighted ? "bg-blue-50" : "border-b border-line last:border-0 hover:bg-slate-50"}
                >
                  <td className="py-3 pr-4 font-semibold text-ink">
                    {item.model_name}
                    {highlighted ? (
                      <span className="ml-2 rounded-full bg-accent px-2 py-0.5 text-xs text-white">
                        highest
                      </span>
                    ) : null}
                  </td>
                  <td className="py-3 pr-4">{(item.churn_probability * 100).toFixed(1)}%</td>
                  <td className="py-3 pr-4">
                    <span
                      className={
                        item.prediction_label === "Churn"
                          ? "font-semibold text-warning"
                          : "font-semibold text-success"
                      }
                    >
                      {item.prediction_label}
                    </span>
                  </td>
                  <td className="py-3 pr-4">{(item.confidence * 100).toFixed(1)}%</td>
                  <td className="py-3 pr-4">{item.inference_ms.toFixed(1)} ms</td>
                  <td className="py-3 pr-4"><PredictionSourceBadge prediction={item} /></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
