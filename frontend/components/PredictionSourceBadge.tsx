import type { PredictionResult } from "@/lib/api";

const badgeStyles: Record<string, string> = {
  live_model: "border-emerald-200 bg-emerald-50 text-emerald-700",
  cached_fallback: "border-blue-200 bg-blue-50 text-blue-700",
  mock_baseline: "border-amber-200 bg-amber-50 text-amber-700",
  unavailable: "border-rose-200 bg-rose-50 text-rose-700",
};

const labels: Record<string, string> = {
  live_model: "Live Model",
  cached_fallback: "Cached Fallback",
  mock_baseline: "Mock Baseline",
  unavailable: "Unavailable",
};

export function PredictionSourceBadge({ prediction }: { prediction: PredictionResult }) {
  const source = prediction.source ?? "unavailable";
  const className = badgeStyles[source] ?? "border-slate-200 bg-slate-50 text-slate-700";

  return (
    <span className={`rounded-full border px-2.5 py-1 text-xs font-semibold ${className}`}>
      {labels[source] ?? source.replaceAll("_", " ")}
    </span>
  );
}
