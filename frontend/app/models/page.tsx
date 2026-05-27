"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { AnimatedChartCard } from "@/components/AnimatedChartCard";
import { LoadingState } from "@/components/LoadingState";
import { MetricCard } from "@/components/MetricCard";
import { MiniBarChart } from "@/components/MiniBarChart";
import { ModelComparisonChart } from "@/components/ModelComparisonChart";
import { PageHeader } from "@/components/PageHeader";
import { api, ModelMetrics } from "@/lib/api";

export default function ModelsPage() {
  const [metrics, setMetrics] = useState<ModelMetrics[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getMetrics()
      .then((metricsData) => setMetrics(metricsData))
      .catch(() => setError("Could not load model metrics. Make sure the backend is running."));
  }, []);

  const sizeData = useMemo(
    () => metrics.map((item) => ({ model: item.model_name, value: item.model_size_mb })),
    [metrics],
  );
  const rocAucData = useMemo(
    () =>
      metrics.map((item) => ({
        model: item.model_name,
        value: typeof item.roc_auc === "number" ? Number((item.roc_auc * 100).toFixed(1)) : null,
      })),
    [metrics],
  );

  return (
    <div>
      <PageHeader
        eyebrow="Metric comparison"
        title="Model Comparison"
        description="TFT and TabNet perform differently across metrics, so this view compares each model side-by-side."
        actions={
          <Link
            href="/customers"
            className="rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white hover:bg-[#256864]"
          >
            Start Customer Analysis
          </Link>
        }
      />

      {error ? <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">{error}</div> : null}
      {!metrics.length && !error ? (
        <div>
          <LoadingState label="Loading model comparison data..." />
          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            {[0, 1].map((item) => (
              <div key={item} className="research-card rounded-2xl p-5">
                <div className="h-4 w-24 animate-pulse rounded bg-vellum" />
                <div className="mt-4 h-8 w-20 animate-pulse rounded bg-vellum" />
                <div className="mt-6 grid grid-cols-2 gap-3">
                  <div className="h-16 animate-pulse rounded-lg bg-vellum" />
                  <div className="h-16 animate-pulse rounded-lg bg-vellum" />
                  <div className="h-16 animate-pulse rounded-lg bg-vellum" />
                  <div className="h-16 animate-pulse rounded-lg bg-vellum" />
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}

      {metrics.length ? (
        <div className="space-y-6">
          <div className="grid gap-4 lg:grid-cols-2">
            {metrics.map((item) => (
              <div key={item.model_name} className="fade-in">
                <MetricCard metrics={item} />
              </div>
            ))}
          </div>

          <section className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <AnimatedChartCard
                title="Core Performance Metrics"
                description="Available ROC-AUC, F1-score, recall, and precision values shown side-by-side."
              >
                <ModelComparisonChart metrics={metrics} />
              </AnimatedChartCard>
            </div>
            <AnimatedChartCard
              title="Metric Overview"
              description="Compare each metric independently; no combined ranking is applied."
            >
              <div className="space-y-3 text-sm leading-6 text-slate-700">
                <p>TFT and TabNet can trade places depending on the metric.</p>
                <p>Use ROC-AUC, F1-score, recall, precision, and model size as separate comparison signals.</p>
              </div>
            </AnimatedChartCard>
          </section>

          <section className="grid gap-6 lg:grid-cols-2">
            <AnimatedChartCard title="ROC-AUC Comparison" description="Compact side-by-side discriminative performance.">
              <MiniBarChart data={rocAucData} suffix="%" color="#2f7d78" domain={[0, 100]} />
            </AnimatedChartCard>
            <AnimatedChartCard title="F1-score and Recall" description="Balanced churn identification and sensitivity.">
              <ModelComparisonChart metrics={metrics} keys={["F1-score", "Recall"]} />
            </AnimatedChartCard>
            <AnimatedChartCard title="Model Size Comparison" description="Shown when provided by the final summary files.">
              <MiniBarChart data={sizeData} suffix=" MB" color="#7f69ab" />
            </AnimatedChartCard>
          </section>
        </div>
      ) : null}
    </div>
  );
}
