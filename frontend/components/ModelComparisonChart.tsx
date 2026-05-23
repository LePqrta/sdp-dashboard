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
  const chartHeight = 280;
  const top = 24;
  const bottom = 46;
  const left = 42;
  const right = 18;
  const width = 720;
  const innerHeight = chartHeight - top - bottom;
  const innerWidth = width - left - right;
  const groupWidth = innerWidth / metrics.length;
  const barWidth = Math.min(28, (groupWidth - 30) / keys.length);

  return (
    <div className="overflow-x-auto">
      <svg viewBox={`0 0 ${width} ${chartHeight}`} className="h-80 min-w-[640px]">
        {[0.7, 0.8, 0.9, 1].map((tick) => {
          const y = top + (1 - (tick - 0.7) / 0.3) * innerHeight;
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
              {keys.map((key, keyIndex) => {
                const value = model[metricMap[key]];
                const normalized = Math.max(0, Math.min(1, (value - 0.7) / 0.3));
                const barHeight = normalized * innerHeight;
                const x = groupX - (keys.length * barWidth) / 2 + keyIndex * (barWidth + 4);
                const y = top + innerHeight - barHeight;
                return (
                  <g key={key}>
                    <rect
                      x={x}
                      y={y}
                      width={barWidth}
                      height={barHeight}
                      rx={6}
                      fill={colors[key]}
                      className="origin-bottom animate-chart-rise"
                    />
                    {keys.length === 1 ? (
                      <text x={x + barWidth / 2} y={y - 8} textAnchor="middle" className="fill-ink text-[12px] font-semibold">
                        {(value * 100).toFixed(1)}%
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
        {keys.map((key) => (
          <span key={key} className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: colors[key] }} />
            {key}
          </span>
        ))}
      </div>
    </div>
  );
}
