"use client";

import Link from "next/link";
import { GlareCard } from "@/components/GlareCard";
import { ShimmerText } from "@/components/ShimmerText";

const features = [
  {
    title: "Global model comparison",
    body: "Review validation metrics for TFT and TabNet with balanced accuracy, recall, F1, ROC-AUC, size, and speed views.",
  },
  {
    title: "Customer-level prediction",
    body: "Select one representative demo customer and run the same prediction request through both model interfaces.",
  },
  {
    title: "Explainability placeholders",
    body: "Reserve a dedicated analysis surface for SHAP-style feature contributions, attention, and model-specific explanations.",
  },
];

const workflow = ["Compare models", "Select customer", "Run predictions", "Explain drivers"];

export default function LandingPage() {
  return (
    <div className="space-y-10">
      <div className="fade-in">
        <section className="research-card overflow-hidden rounded-[28px]">
          <div className="lab-strip h-3" />
          <div className="grid gap-8 p-7 sm:p-10 lg:grid-cols-[1.2fr_0.8fr] lg:p-12">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-teal-700">
                Graduation project research studio
              </p>
              <h1 className="mt-5 max-w-4xl text-4xl font-semibold tracking-tight text-ink sm:text-6xl">
                <ShimmerText>Churn Prediction</ShimmerText>{" "}
                Model Comparison Dashboard
              </h1>
              <p className="mt-5 max-w-3xl text-lg leading-8 text-slate-600">
                This dashboard compares TFT and TabNet models for customer churn prediction
                using a representative customer sample dataset.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <Link
                  href="/models"
                  className="rounded-md bg-accent px-5 py-3 text-sm font-semibold text-white shadow-[0_14px_28px_rgba(47,125,120,0.24)] hover:bg-[#256864]"
                >
                  View Model Comparison
                </Link>
                <Link
                  href="/customers"
                  className="rounded-md border border-line bg-panel px-5 py-3 text-sm font-semibold text-ink hover:border-mint hover:bg-mint/10"
                >
                  Start Customer Analysis
                </Link>
              </div>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-[#1c2430] p-5 text-white shadow-[0_24px_60px_rgba(28,36,48,0.22)]">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-blue-200">Evaluation slate</p>
              <div className="grid gap-4">
                {["TFT", "TabNet"].map((model, index) => (
                  <div
                    key={model}
                    className="rounded-xl border border-white/10 bg-white/8 p-4 shadow-sm backdrop-blur"
                    style={{ animationDelay: `${index * 80}ms` }}
                  >
                    <p className="text-sm font-semibold text-blue-100">Candidate model</p>
                    <p className="mt-1 text-2xl font-semibold text-white">{model}</p>
                    <div className="mt-3 h-2 rounded-full bg-white/10">
                      <div
                        className="h-2 rounded-full bg-gradient-to-r from-teal-300 via-blue-300 to-amber-300"
                        style={{ width: `${86 - index * 8}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      </div>

      <div className="grid gap-5 md:grid-cols-3">
        {features.map((feature) => (
          <article
            key={feature.title}
            className="fade-in rounded-xl border border-line bg-panel/88 p-6 shadow-soft transition-transform duration-200 hover:-translate-y-1"
          >
            <h2 className="text-lg font-semibold text-ink">{feature.title}</h2>
            <p className="mt-3 text-sm leading-6 text-muted">{feature.body}</p>
          </article>
        ))}
      </div>

      <div className="fade-in">
        <section className="research-card rounded-2xl p-6">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h2 className="text-2xl font-semibold text-ink">Dashboard workflow</h2>
              <p className="mt-2 text-sm text-muted">
                The app separates global evaluation from customer-level analysis for a cleaner demo story.
              </p>
            </div>
          </div>
          <div className="mt-6 grid gap-3 md:grid-cols-4">
            {workflow.map((step, index) => (
              <GlareCard key={step} className="p-4">
                <p className="relative text-sm font-semibold text-accent">Step {index + 1}</p>
                <p className="mt-2 text-base font-semibold text-ink">{step}</p>
              </GlareCard>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
