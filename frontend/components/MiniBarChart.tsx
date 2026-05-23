export function MiniBarChart({
  data,
  suffix,
  color,
  domain,
}: {
  data: { model: string; value: number }[];
  suffix: string;
  color: string;
  domain?: [number, number];
}) {
  const values = data.map((item) => item.value);
  const min = domain?.[0] ?? 0;
  const max = domain?.[1] ?? Math.max(...values, 1);

  return (
    <div className="space-y-4 py-2">
      {data.map((item) => {
        const width = Math.max(6, ((item.value - min) / Math.max(max - min, 1)) * 100);
        return (
          <div key={item.model}>
            <div className="mb-2 flex items-center justify-between text-sm">
              <span className="font-semibold text-ink">{item.model}</span>
              <span className="text-muted">
                {item.value}
                {suffix}
              </span>
            </div>
            <div className="h-3 rounded-full bg-vellum">
              <div
                className="h-3 rounded-full animate-width-in"
                style={{ width: `${width}%`, backgroundColor: color }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
