"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AnimatedChartCard } from "@/components/AnimatedChartCard";
import { CustomerCard } from "@/components/CustomerCard";
import { LoadingState } from "@/components/LoadingState";
import { PageHeader } from "@/components/PageHeader";
import { PredictionCard } from "@/components/PredictionCard";
import { PredictionTable } from "@/components/PredictionTable";
import { ProbabilityChart } from "@/components/ProbabilityChart";
import { RecommendationCard } from "@/components/RecommendationCard";
import { SlowLoadingNotice } from "@/components/SlowLoadingNotice";
import { api, Customer, PredictionResponse } from "@/lib/api";

type PredictionPageProps = {
  params: { customer_id: string };
};

export default function PredictionPage({ params }: PredictionPageProps) {
  const customerId = decodeURIComponent(params.customer_id);
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.getCustomer(customerId), api.predict(customerId)])
      .then(([customerData, predictionData]) => {
        setCustomer(customerData);
        setPrediction(predictionData);
      })
      .catch(() => setError("Could not load prediction results for this customer."));
  }, [customerId]);

  const highest = prediction?.highest_probability_model;
  const highestPrediction = prediction?.predictions.find((item) => item.model_name === highest);

  return (
    <div>
      <PageHeader
        eyebrow="Customer prediction"
        title={`Prediction Results: ${customerId}`}
        description="Compare live TFT and TabNet churn outputs for the selected customer sample."
        actions={
          <>
            <Link href={`/explainability/${customerId}`} className="rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white hover:bg-[#256864]">
              View Explainability
            </Link>
            <Link href="/customers" className="rounded-md border border-line bg-panel px-4 py-2 text-sm font-semibold text-ink hover:bg-mint/10">
              Select Another Customer
            </Link>
            <Link href="/models" className="rounded-md border border-line bg-panel px-4 py-2 text-sm font-semibold text-ink hover:bg-mint/10">
              View Model Stats
            </Link>
          </>
        }
      />

      {error ? <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">{error}</div> : null}
      {!prediction && !error ? (
        <div>
          <LoadingState label="Running model predictions..." />
          <SlowLoadingNotice
            delayMs={2200}
            message="TFT and TabNet may take a little time on first load. Keep this page open while inference finishes."
          />
        </div>
      ) : null}

      {prediction ? (
        <div className="space-y-6">
          {customer ? <CustomerCard customer={customer} /> : null}

          <div className="grid gap-4 lg:grid-cols-2">
            {prediction.predictions.map((item) => (
              <div key={item.model_name} className="fade-in">
                <PredictionCard prediction={item} highlight={item.model_name === prediction.highest_probability_model} />
              </div>
            ))}
          </div>

          <section className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
                <AnimatedChartCard title="Churn Probability Comparison" description="Customer-level probability output from TFT and TabNet with source labels.">
                <ProbabilityChart predictions={prediction.predictions} />
              </AnimatedChartCard>
            </div>
            <div className="space-y-6">
              <RecommendationCard
                title="Highest churn probability"
                body={`${highestPrediction?.model_name ?? "Model"} reports ${(Number(highestPrediction?.churn_probability ?? 0) * 100).toFixed(1)}% churn probability.`}
                tone={highestPrediction?.prediction_label === "Churn" ? "amber" : "green"}
              />
              <RecommendationCard
                title="Prediction summary"
                body={prediction.recommendation}
                tone="blue"
              />
            </div>
          </section>

          <PredictionTable
            predictions={prediction.predictions}
            highlightedModel={prediction.highest_probability_model}
          />
        </div>
      ) : null}
    </div>
  );
}
