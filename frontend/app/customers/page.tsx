"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { CustomerCard } from "@/components/CustomerCard";
import { LoadingState } from "@/components/LoadingState";
import { PageHeader } from "@/components/PageHeader";
import { api, Customer } from "@/lib/api";

export default function CustomersPage() {
  const router = useRouter();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [loadingCustomer, setLoadingCustomer] = useState(false);
  const [loadingList, setLoadingList] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getCustomers()
      .then(setCustomers)
      .catch(() => setError("Could not load sample customers."))
      .finally(() => setLoadingList(false));
  }, []);

  async function selectRandomCustomer() {
    setLoadingCustomer(true);
    setError(null);
    try {
      setSelectedCustomer(await api.getRandomCustomer());
    } catch {
      setError("Could not select a random customer.");
    } finally {
      setLoadingCustomer(false);
    }
  }

  function runPrediction() {
    if (selectedCustomer) {
      router.push(`/predictions/${selectedCustomer.customer_id}`);
    }
  }

  return (
    <div>
      <PageHeader
        eyebrow="Customer sample"
        title="Select a Customer"
        description="Choose one representative customer from the demo sample. The full source dataset remains outside the dashboard runtime."
      />

      {error ? <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">{error}</div> : null}
      {loadingList ? (
        <div className="mb-6">
          <LoadingState label="Loading customer sample..." />
        </div>
      ) : null}

      <section className="grid gap-6 lg:grid-cols-[1fr_0.9fr]">
        <div className="fade-in">
          <div className="research-card rounded-2xl p-6">
            <h2 className="text-2xl font-semibold text-ink">Representative sample workflow</h2>
            <p className="mt-3 text-sm leading-6 text-muted">
              Select a random customer, inspect their profile, then continue into the model prediction
              comparison. Customer selection only happens on this page to keep the analysis flow clear.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <button
                onClick={selectRandomCustomer}
                disabled={loadingCustomer}
                className="rounded-md bg-accent px-5 py-3 text-sm font-semibold text-white hover:bg-[#256864] disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loadingCustomer ? "Selecting..." : "Select Random Customer"}
              </button>
              <button
                onClick={runPrediction}
                disabled={!selectedCustomer}
                className="rounded-md border border-line bg-panel px-5 py-3 text-sm font-semibold text-ink hover:border-mint hover:bg-mint/10 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Run Prediction
              </button>
            </div>
          </div>
        </div>

        <div className="fade-in">
          <div className="overflow-hidden rounded-2xl border border-mint/50 bg-gradient-to-br from-[#e9fbf7] via-panel to-[#fff6e7] shadow-soft">
            <div className="lab-strip h-2" />
            <div className="p-6">
            <p className="text-sm font-semibold uppercase tracking-wide text-accent">Dataset boundary</p>
            <p className="mt-3 text-3xl font-semibold text-ink">1000-5000</p>
            <p className="mt-2 text-sm leading-6 text-muted">
              Intended demo sample size. This keeps the dashboard responsive while preserving a realistic
              customer-level story for presentation.
            </p>
            </div>
          </div>
        </div>
      </section>

      <div className="mt-6">
        {selectedCustomer ? (
          <div className="fade-in">
            <CustomerCard customer={selectedCustomer} />
          </div>
        ) : (
          <div className="rounded-xl border border-dashed border-line bg-white/70 p-8 text-center text-sm text-muted shadow-soft">
            No customer selected yet.
          </div>
        )}
      </div>

      <section className="research-card mt-6 rounded-2xl p-5">
        <h2 className="text-xl font-semibold text-ink">Sample Customer List</h2>
        {loadingList ? (
          <div className="mt-4"><LoadingState label="Loading sample customers..." /></div>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="text-muted">
                <tr className="border-b border-line">
                  <th className="py-3 pr-4 font-semibold">Customer</th>
                  <th className="py-3 pr-4 font-semibold">Age</th>
                  <th className="py-3 pr-4 font-semibold">Tenure</th>
                  <th className="py-3 pr-4 font-semibold">Contract</th>
                  <th className="py-3 pr-4 font-semibold">Activity</th>
                </tr>
              </thead>
              <tbody>
                {customers.map((customer) => (
                  <tr key={customer.customer_id} className="border-b border-line last:border-0 hover:bg-slate-50">
                    <td className="py-3 pr-4 font-semibold text-ink">{customer.customer_id}</td>
                    <td className="py-3 pr-4">{customer.age}</td>
                    <td className="py-3 pr-4">{customer.tenure_months} months</td>
                    <td className="py-3 pr-4">{customer.contract_type}</td>
                    <td className="py-3 pr-4">
                      {customer.support_tickets} tickets · {customer.late_payments} late payments
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
