"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { AnimatedChartCard } from "@/components/AnimatedChartCard";
import { BestModelCard } from "@/components/BestModelCard";
import { LoadingState } from "@/components/LoadingState";
import { MetricCard } from "@/components/MetricCard";
import { MiniBarChart } from "@/components/MiniBarChart";
import { ModelComparisonChart } from "@/components/ModelComparisonChart";
import { PageHeader } from "@/components/PageHeader";
import { api, BestModel, ModelMetrics } from "@/lib/api";

export default function ModelsPage() {
  const [metrics, setMetrics] = useState<ModelMetrics[]>([]);
  const [bestModel, setBestModel] = useState<BestModel | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.getMetrics(), api.getBestModel()])
      .then(([metricsData, bestModelData]) => {
        setMetrics(metricsData);
        setBestModel(bestModelData);
      })
      .catch(() => setError("Could not load model metrics. Make sure the backend is running."));
  }, []);

  const sizeData = useMemo(
    () => metrics.map((item) => ({ model: item.model_name, value: item.model_size_mb })),
    [metrics],
  );
  const inferenceData = useMemo(
    () => metrics.map((item) => ({ model: item.model_name, value: item.average_inference_ms })),
    [metrics],
  );

  return (
    <div>
      <PageHeader
        eyebrow="Global evaluation"
        title="Model Comparison"
        description="A dedicated analytics view for static validation performance, operational size, and inference latency across TFT, NHiTS, and TabNet."
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
          <div className="mt-6 grid gap-4 lg:grid-cols-3">
            {[0, 1, 2].map((item) => (
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
          <div className="grid gap-4 lg:grid-cols-3">
            {metrics.map((item) => (
              <div key={item.model_name} className="fade-in">
                <MetricCard metrics={item} isBest={item.model_name === bestModel?.model_name} />
              </div>
            ))}
          </div>

          <section className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <AnimatedChartCard
                title="Core Performance Metrics"
                description="ROC-AUC, F1-score, recall, and precision shown side-by-side."
              >
                <ModelComparisonChart metrics={metrics} />
              </AnimatedChartCard>
            </div>
            <BestModelCard bestModel={bestModel} />
          </section>

          <section className="grid gap-6 lg:grid-cols-2">
            <AnimatedChartCard title="ROC-AUC Comparison" description="Ranking models by discriminative performance.">
              <ModelComparisonChart metrics={metrics} keys={["ROC-AUC"]} />
            </AnimatedChartCard>
            <AnimatedChartCard title="F1-score and Recall" description="Balanced churn identification and sensitivity.">
              <ModelComparisonChart metrics={metrics} keys={["F1-score", "Recall"]} />
            </AnimatedChartCard>
            <AnimatedChartCard title="Model Size Comparison" description="Operational deployment footprint.">
              <MiniBarChart data={sizeData} suffix=" MB" color="#7f69ab" />
            </AnimatedChartCard>
            <AnimatedChartCard title="Inference Time Comparison" description="Average response time per customer.">
              <MiniBarChart data={inferenceData} suffix=" ms" color="#d99145" />
            </AnimatedChartCard>
          </section>
        </div>
      ) : null}
    </div>
  );
}
