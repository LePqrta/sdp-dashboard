import type { ExplanationFeature } from "@/lib/api";

export function ShapBarChart({ features }: { features: ExplanationFeature[] }) {
  const max = Math.max(...features.map((item) => Math.abs(item.contribution)), 0.01);

  return (
    <div className="space-y-3">
      {features.map((item) => {
        const positive = item.contribution >= 0;
        const width = (Math.abs(item.contribution) / max) * 100;
        return (
          <div key={item.feature} className="grid gap-2 md:grid-cols-[180px_1fr_56px] md:items-center">
            <p className="text-sm font-semibold text-ink">{item.feature}</p>
            <div className="h-3 rounded-full bg-vellum">
              <div
                className="h-3 rounded-full animate-width-in"
                style={{
                  width: `${width}%`,
                  backgroundColor: positive ? "#7f69ab" : "#84ccc5",
                }}
              />
            </div>
            <p className="text-right text-sm font-semibold text-muted">{item.contribution.toFixed(3)}</p>
          </div>
        );
      })}
    </div>
  );
}
