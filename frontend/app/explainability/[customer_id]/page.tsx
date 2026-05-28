"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CustomerCard } from "@/components/CustomerCard";
import { LoadingState } from "@/components/LoadingState";
import { ModelExplanationCard } from "@/components/ModelExplanationCard";
import { PageHeader } from "@/components/PageHeader";
import { RecommendationCard } from "@/components/RecommendationCard";
import { api, Customer, ExplanationResponse } from "@/lib/api";

type ExplainabilityPageProps = {
  params: { customer_id: string };
};

export default function ExplainabilityPage({ params }: ExplainabilityPageProps) {
  const customerId = decodeURIComponent(params.customer_id);
  const [customer, setCustomer] = useState<Customer | null>(null);
  const [explanation, setExplanation] = useState<ExplanationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.getCustomer(customerId), api.getExplanations(customerId)])
      .then(([customerData, explanationData]) => {
        setCustomer(customerData);
        setExplanation(explanationData);
      })
      .catch(() => setError("Could not load explainability data for this customer."));
  }, [customerId]);

  return (
    <div>
      <PageHeader
        eyebrow="Explainability"
        title={`Explainability: ${customerId}`}
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
      {!explanation && !error ? <LoadingState label="Loading explainability output..." /> : null}

      {explanation ? (
        <div className="space-y-6">
          {customer ? <CustomerCard customer={customer} /> : null}

          <RecommendationCard
            title="Top model factors"
            body="These factors are compact precomputed local importances from the selected model artifacts."
            tone="blue"
          />

          {explanation.warnings.length ? (
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-800">
              {explanation.warnings.map((warning) => (
                <p key={warning}>{warning}</p>
              ))}
            </div>
          ) : null}

          <div className="space-y-5">
            {explanation.models.map((modelExplanation) => (
              <ModelExplanationCard key={modelExplanation.model} explanation={modelExplanation} />
            ))}
          </div>

        </div>
      ) : null}
    </div>
  );
}
