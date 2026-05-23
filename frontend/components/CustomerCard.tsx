import type { Customer } from "@/lib/api";

export function CustomerCard({ customer }: { customer: Customer }) {
  const segment = getSegment(customer);
  const rows = [
    ["Customer ID", customer.customer_id],
    ["Age", customer.age],
    ["Tenure", `${customer.tenure_months} months`],
    ["Contract", customer.contract_type],
    ["Internet", customer.internet_service],
    ["Payment", customer.payment_method],
    ["Monthly Charges", `$${customer.monthly_charges.toFixed(2)}`],
    ["Total Charges", `$${customer.total_charges.toFixed(2)}`],
    ["Support Tickets", customer.support_tickets],
    ["Late Payments", customer.late_payments],
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
  if (customer.contract_type === "Month-to-month" && customer.late_payments > 1) {
    return "High-risk flexible";
  }
  if (customer.tenure_months > 48) {
    return "Loyal long-tenure";
  }
  return "Standard monitored";
}
