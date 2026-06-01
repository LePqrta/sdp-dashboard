"use client";

import { Suspense, useEffect, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { CustomerCard } from "@/components/CustomerCard";
import { LoadingState } from "@/components/LoadingState";
import { PageHeader } from "@/components/PageHeader";
import {
  api,
  Customer,
  CustomerFilterKey,
  CustomerSortDirection,
  CustomerSortKey,
} from "@/lib/api";

const PAGE_SIZE = 25;

const FILTER_OPTIONS: Array<{ value: CustomerFilterKey; label: string }> = [
  { value: "all", label: "All customers" },
  { value: "churn", label: "Actual: Churn" },
  { value: "not_churn", label: "Actual: Not Churn" },
  { value: "train", label: "Train split" },
  { value: "validation", label: "Validation split" },
  { value: "test", label: "Test split" },
  { value: "sample", label: "Sample split" },
];

const CUSTOMER_TABLE_COLUMNS: Array<{ label: string; sort?: CustomerSortKey }> = [
  { label: "Customer", sort: "customer_id" },
  { label: "Actual", sort: "actual_label" },
  { label: "History", sort: "history" },
  { label: "Tenure", sort: "tenure" },
  { label: "Activity", sort: "activity" },
];

type CustomerListParams = {
  q: string;
  filter: CustomerFilterKey;
  sort: CustomerSortKey;
  direction: CustomerSortDirection;
  page: number;
};

type CustomerSearchParams = {
  get: (key: string) => string | null;
};

function isCustomerFilterKey(value: string | null): value is CustomerFilterKey {
  return FILTER_OPTIONS.some((option) => option.value === value);
}

function isCustomerSortKey(value: string | null): value is CustomerSortKey {
  return CUSTOMER_TABLE_COLUMNS.some((column) => column.sort === value);
}

function isCustomerSortDirection(value: string | null): value is CustomerSortDirection {
  return value === "asc" || value === "desc";
}

function parseCustomerListParams(searchParams: CustomerSearchParams): CustomerListParams {
  const rawPage = Number(searchParams.get("page"));
  const filter = searchParams.get("filter");
  const sort = searchParams.get("sort");
  const direction = searchParams.get("direction");

  return {
    q: searchParams.get("q")?.trim() ?? "",
    filter: isCustomerFilterKey(filter) ? filter : "all",
    sort: isCustomerSortKey(sort) ? sort : "customer_id",
    direction: isCustomerSortDirection(direction) ? direction : "asc",
    page: Number.isInteger(rawPage) && rawPage > 0 ? rawPage : 1,
  };
}

export default function CustomersPage() {
  return (
    <Suspense fallback={<LoadingState label="Loading customer controls..." />}>
      <CustomersPageContent />
    </Suspense>
  );
}

function CustomersPageContent() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const listParams = parseCustomerListParams(searchParams);

  const [customers, setCustomers] = useState<Customer[]>([]);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);
  const [loadingCustomer, setLoadingCustomer] = useState(false);
  const [loadingList, setLoadingList] = useState(true);
  const [totalCustomers, setTotalCustomers] = useState(0);
  const [listError, setListError] = useState<string | null>(null);
  const [selectionError, setSelectionError] = useState<string | null>(null);
  const [retryVersion, setRetryVersion] = useState(0);

  const totalPages = Math.max(1, Math.ceil(totalCustomers / PAGE_SIZE));
  const pageStart = (listParams.page - 1) * PAGE_SIZE;
  const showingStart = totalCustomers ? pageStart + 1 : 0;
  const showingEnd = Math.min(pageStart + PAGE_SIZE, totalCustomers);
  const hasActiveControls =
    listParams.q !== "" ||
    listParams.filter !== "all" ||
    listParams.sort !== "customer_id" ||
    listParams.direction !== "asc";

  function buildUrl(params: Partial<CustomerListParams>, resetPage = false) {
    const next = new URLSearchParams(searchParams.toString());
    const page = resetPage ? 1 : params.page;

    if (params.q !== undefined) {
      const q = params.q.trim();
      if (q) {
        next.set("q", q);
      } else {
        next.delete("q");
      }
    }

    if (params.filter !== undefined) {
      if (params.filter === "all") {
        next.delete("filter");
      } else {
        next.set("filter", params.filter);
      }
    }

    if (params.sort !== undefined) {
      if (params.sort === "customer_id") {
        next.delete("sort");
      } else {
        next.set("sort", params.sort);
      }
    }

    if (params.direction !== undefined) {
      if (params.direction === "asc") {
        next.delete("direction");
      } else {
        next.set("direction", params.direction);
      }
    }

    if (page !== undefined) {
      if (page <= 1) {
        next.delete("page");
      } else {
        next.set("page", String(page));
      }
    }

    const query = next.toString();
    return query ? `${pathname}?${query}` : pathname;
  }

  function updateListParams(params: Partial<CustomerListParams>, resetPage = true) {
    router.push(buildUrl(params, resetPage), { scroll: false });
  }

  function sortByColumn(sort: CustomerSortKey) {
    const direction =
      listParams.sort === sort && listParams.direction === "asc" ? "desc" : "asc";

    updateListParams({ sort, direction });
  }

  function clearControls() {
    router.push(pathname, { scroll: false });
  }

  useEffect(() => {
    let cancelled = false;

    setLoadingList(true);
    setListError(null);

    api
      .getCustomerPage({
        page: listParams.page,
        limit: PAGE_SIZE,
        q: listParams.q,
        filter: listParams.filter,
        sort: listParams.sort,
        direction: listParams.direction,
      })
      .then((page) => {
        if (cancelled) {
          return;
        }
        setCustomers(page.items);
        setTotalCustomers(page.total);
      })
      .catch(() => {
        if (!cancelled) {
          setCustomers([]);
          setTotalCustomers(0);
          setListError("Could not load sample customers.");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoadingList(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [
    listParams.direction,
    listParams.filter,
    listParams.page,
    listParams.q,
    listParams.sort,
    retryVersion,
  ]);

  useEffect(() => {
    if (!loadingList && listParams.page > totalPages) {
      router.replace(buildUrl({ page: totalPages }, false), { scroll: false });
    }
  }, [loadingList, listParams.page, totalPages, router]);

  async function selectRandomCustomer() {
    setLoadingCustomer(true);
    setSelectionError(null);
    try {
      setSelectedCustomer(await api.getRandomCustomer());
    } catch {
      setSelectionError("Could not select a random customer.");
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

      {selectionError ? (
        <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          {selectionError}
        </div>
      ) : null}

      <section className="grid items-stretch gap-6 lg:grid-cols-[1fr_0.9fr]">
        <div className="fade-in h-full">
          <div className="research-card h-full rounded-2xl p-6">
            <h2 className="text-2xl font-semibold text-ink">Representative sample workflow</h2>
            <p className="mt-3 text-sm leading-6 text-muted">
              Select a random customer, inspect their profile, then continue into the model prediction
              comparison.
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

        <div className="fade-in h-full">
          <div className="h-full overflow-hidden rounded-2xl border border-mint/50 bg-gradient-to-br from-[#e9fbf7] via-panel to-[#fff6e7] shadow-soft">
            <div className="lab-strip h-2" />
            <div className="p-6">
              <p className="text-sm font-semibold uppercase tracking-wide text-accent">
                Dataset boundary
              </p>
              <p className="mt-3 text-3xl font-semibold text-ink">1000-5000</p>
              <p className="mt-2 text-sm leading-6 text-muted">
                Intended demo sample size. This keeps the dashboard responsive while preserving a realistic
                customer-level story.
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
        <div className="flex flex-col gap-4">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <h2 className="text-xl font-semibold text-ink">Sample Customer List</h2>
              <p className="mt-1 text-sm text-muted">
                Showing {showingStart}-{showingEnd} of {totalCustomers} customers
              </p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => updateListParams({ page: Math.max(1, listParams.page - 1) }, false)}
                disabled={listParams.page === 1 || loadingList}
                className="rounded-md border border-line bg-panel px-3 py-2 text-sm font-semibold text-ink hover:bg-mint/10 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Previous
              </button>
              <span className="min-w-24 text-center text-sm font-semibold text-muted">
                Page {Math.min(listParams.page, totalPages)} / {totalPages}
              </span>
              <button
                onClick={() =>
                  updateListParams({ page: Math.min(totalPages, listParams.page + 1) }, false)
                }
                disabled={listParams.page >= totalPages || loadingList}
                className="rounded-md border border-line bg-panel px-3 py-2 text-sm font-semibold text-ink hover:bg-mint/10 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>

          <div className="grid gap-3 rounded-xl border border-line bg-white/70 p-4 md:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)_auto]">
            <label className="flex flex-col gap-1 text-sm font-semibold text-ink">
              Search
              <input
                value={listParams.q}
                onChange={(event) => updateListParams({ q: event.target.value })}
                placeholder="Customer, split, label..."
                className="h-10 rounded-md border border-line bg-panel px-3 text-sm font-normal text-ink outline-none transition focus:border-accent focus:ring-2 focus:ring-mint/40"
              />
            </label>
            <label className="flex flex-col gap-1 text-sm font-semibold text-ink">
              Filter
              <span className="relative block">
                <select
                  value={listParams.filter}
                  onChange={(event) =>
                    updateListParams({ filter: event.target.value as CustomerFilterKey })
                  }
                  className="h-10 w-full appearance-none rounded-md border border-line bg-panel py-0 pl-3 pr-10 text-sm font-normal text-ink outline-none transition focus:border-accent focus:ring-2 focus:ring-mint/40"
                >
                  {FILTER_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
                <span
                  aria-hidden="true"
                  className="pointer-events-none absolute right-4 top-1/2 h-0 w-0 -translate-y-1/2 border-l-[4px] border-r-[4px] border-t-[5px] border-l-transparent border-r-transparent border-t-slate-500"
                />
              </span>
            </label>
            <div className="flex items-end">
              <button
                onClick={clearControls}
                disabled={!hasActiveControls || loadingList}
                className="h-10 w-full rounded-md border border-line bg-panel px-3 text-sm font-semibold text-ink hover:bg-mint/10 disabled:cursor-not-allowed disabled:opacity-50 md:w-auto"
              >
                Clear filters
              </button>
            </div>
          </div>
        </div>

        {listError ? (
          <div className="mt-4 flex flex-col gap-3 rounded-xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-800 sm:flex-row sm:items-center sm:justify-between">
            <span>{listError}</span>
            <button
              onClick={() => setRetryVersion((version) => version + 1)}
              className="rounded-md border border-amber-300 bg-white px-3 py-2 text-sm font-semibold text-amber-900 hover:bg-amber-100"
            >
              Retry
            </button>
          </div>
        ) : loadingList ? (
          <div className="mt-4">
            <LoadingState label="Loading sample customers..." />
          </div>
        ) : customers.length === 0 ? (
          <div className="mt-4 rounded-xl border border-dashed border-line bg-white/70 p-8 text-center">
            <p className="text-sm font-semibold text-ink">No customers match these controls.</p>
            <p className="mt-2 text-sm text-muted">
              Try a different search term, filter, or sort direction.
            </p>
            {hasActiveControls ? (
              <button
                onClick={clearControls}
                className="mt-4 rounded-md border border-line bg-panel px-4 py-2 text-sm font-semibold text-ink hover:bg-mint/10"
              >
                Clear filters
              </button>
            ) : null}
          </div>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-[900px] w-full table-fixed text-left text-sm">
              <colgroup>
                <col className="w-[20%]" />
                <col className="w-[16%]" />
                <col className="w-[14%]" />
                <col className="w-[14%]" />
                <col className="w-[36%]" />
              </colgroup>
              <thead className="text-muted">
                <tr className="border-b border-line">
                  {CUSTOMER_TABLE_COLUMNS.map((column) => {
                    if (!column.sort) {
                      return (
                        <th
                          key={column.label}
                          scope="col"
                          className="py-3 pr-4 text-left font-semibold"
                        >
                          {column.label}
                        </th>
                      );
                    }

                    const sort = column.sort;
                    const active = listParams.sort === sort;
                    const arrow = active ? (listParams.direction === "asc" ? "\u2191" : "\u2193") : "";

                    return (
                      <th
                        key={sort}
                        scope="col"
                        aria-sort={
                          active
                            ? listParams.direction === "asc"
                              ? "ascending"
                              : "descending"
                            : "none"
                        }
                        className="p-0 pr-4 text-left font-semibold"
                      >
                        <button
                          type="button"
                          onClick={() => sortByColumn(sort)}
                          disabled={loadingList}
                          className={[
                            "group flex w-full items-center gap-1 py-3 text-left font-semibold transition",
                            active ? "text-accent" : "text-muted hover:text-ink",
                            loadingList ? "cursor-not-allowed opacity-60" : "",
                          ].join(" ")}
                        >
                          <span>{column.label}</span>
                          <span className="inline-block min-w-3 text-left text-xs" aria-hidden="true">
                            {arrow}
                          </span>
                          <span className="sr-only">
                            {active
                              ? `Sorted ${listParams.direction === "asc" ? "ascending" : "descending"}`
                              : "Not sorted"}
                          </span>
                        </button>
                      </th>
                    );
                  })}
                </tr>
              </thead>
              <tbody>
                {customers.map((customer) => (
                  <tr
                    key={customer.customer_id}
                    onClick={() => setSelectedCustomer(customer)}
                    className={[
                      "cursor-pointer border-b border-line last:border-0 hover:bg-slate-50",
                      selectedCustomer?.customer_id === customer.customer_id ? "bg-blue-50" : "",
                    ].join(" ")}
                  >
                    <td className="py-3 pr-4 font-semibold text-ink">{customer.customer_id}</td>
                    <td className="py-3 pr-4">
                      <span
                        className={[
                          "rounded-full px-2 py-1 text-xs font-semibold",
                          customer.actual_label === 1
                            ? "bg-amber-50 text-warning"
                            : "bg-emerald-50 text-success",
                        ].join(" ")}
                      >
                        {customer.actual_label_name ?? "Unknown"}
                      </span>
                    </td>
                    <td className="py-3 pr-4">
                      {customer.history_months_available ?? customer.age} months
                    </td>
                    <td className="py-3 pr-4">{customer.tenure_months} months</td>
                    <td className="py-3 pr-4">
                      {(customer.txn_count_3m ?? customer.support_tickets).toFixed(0)} txns / $
                      {(customer.spend_3m ?? customer.monthly_charges).toFixed(2)}
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
