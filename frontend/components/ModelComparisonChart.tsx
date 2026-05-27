import type { ModelMetrics } from "@/lib/api";

const metricMap = {
  "ROC-AUC": "roc_auc",
  "F1-score": "f1_score",
  Recall: "recall",
  Precision: "precision",
} as const;

const colors: Record<string, string> = {
  "ROC-AUC": "#2f7d78",
  "F1-score": "#7f69ab",
  Recall: "#d99145",
  Precision: "#84ccc5",
};

export function ModelComparisonChart({
  metrics,
  keys = ["ROC-AUC", "F1-score", "Recall", "Precision"],
}: {
  metrics: ModelMetrics[];
  keys?: Array<keyof typeof metricMap>;
}) {
  const availableKeys = keys.filter((key) =>
    metrics.some((model) => typeof model[metricMap[key]] === "number"),
  );
  const values = availableKeys.flatMap((key) =>
    metrics.flatMap((model) => {
      const value = model[metricMap[key]];
      return typeof value === "number" ? [value] : [];
    }),
  );

  if (!availableKeys.length || !values.length) {
    return (
      <div className="rounded-lg border border-dashed border-line bg-white/70 p-5 text-sm text-muted">
        No available metrics for this comparison.
      </div>
    );
  }

  const chartHeight = 280;
  const top = 24;
  const bottom = 46;
  const left = 42;
  const right = 18;
  const width = 720;
  const innerHeight = chartHeight - top - bottom;
  const innerWidth = width - left - right;
  const groupWidth = innerWidth / Math.max(metrics.length, 1);
  const barWidth = Math.max(10, Math.min(30, (groupWidth - 34) / availableKeys.length - 4));
  const rawMin = Math.min(...values);
  const minTick = Math.max(0, Math.floor((rawMin - 0.05) * 10) / 10);
  const maxTick = 1;
  const tickRange = Math.max(maxTick - minTick, 0.1);
  const ticks = Array.from({ length: 4 }, (_, index) => minTick + (tickRange / 3) * index);

  return (
    <div>
      <svg viewBox={`0 0 ${width} ${chartHeight}`} className="h-80 w-full">
        {ticks.map((tick) => {
          const y = top + (1 - (tick - minTick) / tickRange) * innerHeight;
          return (
            <g key={tick}>
              <line x1={left} x2={width - right} y1={y} y2={y} stroke="#dbe5dc" strokeDasharray="4 6" />
              <text x={12} y={y + 4} className="fill-slate-500 text-[11px]">
                {Math.round(tick * 100)}%
              </text>
            </g>
          );
        })}
        {metrics.map((model, modelIndex) => {
          const groupX = left + modelIndex * groupWidth + groupWidth / 2;
          return (
            <g key={model.model_name}>
              {availableKeys.map((key, keyIndex) => {
                const value = model[metricMap[key]];
                const normalized =
                  typeof value === "number"
                    ? Math.max(0, Math.min(1, (value - minTick) / tickRange))
                    : 0;
                const barHeight = normalized * innerHeight;
                const x =
                  groupX -
                  (availableKeys.length * barWidth + (availableKeys.length - 1) * 4) / 2 +
                  keyIndex * (barWidth + 4);
                const y = top + innerHeight - barHeight;
                return (
                  <g key={key}>
                    {typeof value === "number" ? (
                      <rect
                        x={x}
                        y={y}
                        width={barWidth}
                        height={Math.max(3, barHeight)}
                        rx={6}
                        fill={colors[key]}
                        className="origin-bottom animate-chart-rise"
                      />
                    ) : (
                      <text
                        x={x + barWidth / 2}
                        y={top + innerHeight - 8}
                        textAnchor="middle"
                        className="fill-slate-400 text-[10px] font-semibold"
                      >
                        N/A
                      </text>
                    )}
                    {availableKeys.length === 1 ? (
                      <text
                        x={x + barWidth / 2}
                        y={y - 8}
                        textAnchor="middle"
                        className="fill-ink text-[12px] font-semibold"
                      >
                        {typeof value === "number" ? `${(value * 100).toFixed(1)}%` : ""}
                      </text>
                    ) : null}
                  </g>
                );
              })}
              <text x={groupX} y={chartHeight - 16} textAnchor="middle" className="fill-slate-600 text-[12px] font-semibold">
                {model.model_name}
              </text>
            </g>
          );
        })}
      </svg>
      <div className="mt-2 flex flex-wrap gap-3 text-xs font-semibold text-slate-600">
        {availableKeys.map((key) => (
          <span key={key} className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: colors[key] }} />
            {key}
          </span>
        ))}
      </div>
    </div>
  );
}
