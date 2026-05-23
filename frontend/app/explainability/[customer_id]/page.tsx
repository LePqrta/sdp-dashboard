"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { CustomerCard } from "@/components/CustomerCard";
import { LoadingState } from "@/components/LoadingState";
import { ModelExplanationCard } from "@/components/ModelExplanationCard";
import { PageHeader } from "@/components/PageHeader";
import { RecommendationCard } from "@/components/RecommendationCard";
import { api, Customer, ExplanationFeature, ExplanationResponse } from "@/lib/api";

type ExplainabilityPageProps = {
  params: { customer_id: string };
};

export default function ExplainabilityPage({ params }: ExplainabilityPageProps) {
  const customerId = decodeURIComponent(params.customer_id);
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [explanation, setExplanation] = useState<ExplanationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.getCustomers(), api.getExplanations(customerId)])
      .then(([customers, explanationData]) => {
        setCustomer(customers.find((item) => item.customer_id === customerId) ?? null);
        setExplanation(explanationData);
      })
      .catch(() => setError("Could not load explainability data for this customer."));
  }, [customerId]);

  const modelFeatures = useMemo(() => {
    if (!explanation) return null;
    return {
      tft: explanation.features,
      tabnet: scaleFeatures(explanation.features, 0.86),
      nhits: scaleFeatures(explanation.features, 0.52),
    };
  }, [explanation]);

  return (
    <div>
      <PageHeader
        eyebrow="Explainability"
        title={`Explainability: ${customerId}`}
        description="A focused placeholder page for model-specific interpretation outputs that can later be replaced with real SHAP, attention, masks, or post-hoc explainers."
        actions={
          <>
            <Link href={`/predictions/${customerId}`} className="rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white hover:bg-[#256864]">
              Back to Predictions
            </Link>
            <Link href="/customers" className="rounded-md border border-line bg-panel px-4 py-2 text-sm font-semibold text-ink hover:bg-mint/10">
              Select Another Customer
            </Link>
          </>
        }
      />

      {error ? <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">{error}</div> : null}
      {!explanation && !error ? <LoadingState label="Loading mock explainability output..." /> : null}

      {explanation && modelFeatures ? (
        <div className="space-y-6">
          {customer ? <CustomerCard customer={customer} /> : null}

          <RecommendationCard
            title="Top churn reasons"
            body={explanation.summary.join(" ")}
            tone="blue"
          />

          <ModelExplanationCard
            modelName="TFT"
            badge="Attention and variable importance"
            description="Mock attention-style variable importance for the temporal fusion transformer. Real attention weights and static covariate importances can be plugged in later."
            features={modelFeatures.tft}
            summary={[
              "Highlights temporal and static drivers together.",
              "Useful for explaining why risk rises across recent customer behavior.",
              "Future version can display attention heatmaps by timestep.",
            ]}
          />

          <ModelExplanationCard
            modelName="TabNet"
            badge="Local feature masks"
            description="Mock TabNet feature mask interpretation. This section is designed for local feature selection strengths and per-decision-step masks."
            features={modelFeatures.tabnet}
            summary={[
              "Emphasizes sparse local feature selection.",
              "Good fit for tabular customer attributes.",
              "Future version can expose mask values per decision step.",
            ]}
          />

          <ModelExplanationCard
            modelName="NHiTS"
            badge="Post-hoc placeholder"
            description="NHiTS explainability is represented as a placeholder for now. Deeper post-hoc explainability may be added later with perturbation, SHAP, or feature attribution methods."
            features={modelFeatures.nhits}
            summary={[
              "Keeps the explanation page complete for all three models.",
              "Documents the planned post-hoc interpretation path.",
              "Can later connect to model-specific time-series attribution outputs.",
            ]}
          />
        </div>
      ) : null}
    </div>
  );
}

function scaleFeatures(features: ExplanationFeature[], factor: number) {
  return features.map((item) => ({
    ...item,
    contribution: Number((item.contribution * factor).toFixed(3)),
  }));
}
