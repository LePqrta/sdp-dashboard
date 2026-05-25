import type { Customer } from "@/lib/api";

export function CustomerCard({ customer }: { customer: Customer }) {
  const segment = getSegment(customer);
  const rows = [
    ["Customer ID", customer.customer_id],
    ["History", `${customer.history_months_available ?? customer.age} months`],
    ["Tenure", `${customer.tenure_months} months`],
    ["Sample Split", customer.split ?? customer.internet_service],
    ["Latest Time Index", customer.latest_time_idx ?? "N/A"],
    ["3M Transactions", formatNumber(customer.txn_count_3m ?? customer.support_tickets)],
    ["3M Spend", formatMoney(customer.spend_3m ?? customer.monthly_charges)],
    ["Avg Transaction", formatMoney(customer.avg_txn_amt_3m ?? customer.monthly_charges)],
    ["Lifetime Spend", formatMoney(customer.total_lifetime_spend ?? customer.total_charges)],
    ["Lifetime Transactions", formatNumber(customer.total_transaction_count ?? customer.support_tickets)],
    ["Days Since Last Txn", formatNumber(customer.days_since_last_txn ?? customer.late_payments)],
    ["Customer Segment", segment],
  ];

  return (
    <article className="research-card overflow-hidden rounded-2xl">
      <div className="lab-strip h-2" />
      <div className="p-5">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-muted">Selected customer</p>
          <h2 className="mt-1 text-2xl font-semibold text-ink">{customer.customer_id}</h2>
        </div>
        <span className="w-fit rounded-full bg-blue-50 px-3 py-1 text-sm font-semibold text-accent">
          {segment}
        </span>
      </div>
      <dl className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {rows.map(([label, value]) => (
          <div key={label} className="rounded-lg border border-line bg-slate-50/80 p-3">
            <dt className="text-xs font-semibold uppercase tracking-wide text-muted">{label}</dt>
            <dd className="mt-1 text-sm font-semibold text-ink">{value}</dd>
          </div>
        ))}
      </dl>
      </div>
    </article>
  );
}

function getSegment(customer: Customer) {
  if (customer.customer_segment) {
    return customer.customer_segment;
  }
  if (customer.contract_type === "Month-to-month" && customer.late_payments > 1) {
    return "High-risk flexible";
  }
  if (customer.tenure_months > 48) {
    return "Loyal long-tenure";
  }
  return "Standard monitored";
}

function formatMoney(value: number) {
  return `$${value.toFixed(2)}`;
}

function formatNumber(value: number) {
  return Number.isInteger(value) ? value.toString() : value.toFixed(1);
}
