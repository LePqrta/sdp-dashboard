import type { ExplanationFeature } from "@/lib/api";

export function ShapBarChart({ features }: { features: ExplanationFeature[] }) {
  const max = Math.max(...features.map((item) => Math.abs(item.importance)), 0.01);

  return (
    <div className="space-y-3">
      {features.map((item) => {
        const width = (Math.abs(item.importance) / max) * 100;
        return (
          <div key={item.name} className="grid gap-2 md:grid-cols-[200px_1fr_72px] md:items-center">
            <div>
              <p className="text-sm font-semibold text-ink">{item.name}</p>
              {item.display_value ? (
                <p className="text-xs text-muted">Value: {item.display_value}</p>
              ) : null}
            </div>
            <div className="h-3 rounded-full bg-vellum">
              <div
                className="h-3 rounded-full animate-width-in"
                style={{
                  width: `${width}%`,
                  backgroundColor: "#7f69ab",
                }}
              />
            </div>
            <p className="text-right text-sm font-semibold text-muted">{item.importance.toFixed(3)}</p>
          </div>
        );
      })}
    </div>
  );
}
