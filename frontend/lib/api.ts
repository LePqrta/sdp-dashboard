const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type ModelMetrics = {
  model_name: string;
  accuracy: number | null;
  precision: number | null;
  recall: number | null;
  f1_score: number | null;
  roc_auc: number | null;
  pr_auc: number | null;
  model_size_mb: number | null;
  threshold: number | null;
};

export type Customer = {
  customer_id: string;
  age: number;
  tenure_months: number;
  contract_type: string;
  monthly_charges: number;
  total_charges: number;
  internet_service: string;
  payment_method: string;
  support_tickets: number;
  late_payments: number;
  split?: string | null;
  latest_time_idx?: number | null;
  actual_label?: number | null;
  actual_label_name?: "Churn" | "Not Churn" | string | null;
  history_months_available?: number | null;
  txn_count_3m?: number | null;
  spend_3m?: number | null;
  avg_txn_amt_3m?: number | null;
  total_transaction_count?: number | null;
  total_lifetime_spend?: number | null;
  days_since_last_txn?: number | null;
};

export type PredictionResult = {
  model_name: string;
  churn_probability: number;
  prediction_label: "Churn" | "Not Churn";
  confidence: number;
  actual_label?: number | null;
  actual_label_name?: "Churn" | "Not Churn" | string | null;
  is_correct?: boolean | null;
  source?: "live_model" | "cached_fallback" | "mock_baseline" | "unavailable" | string | null;
  status?: "ok" | "fallback" | "mock" | "failed" | string | null;
  message?: string | null;
};

export type CustomerPage = {
  items: Customer[];
  total: number;
  limit: number;
  offset: number;
};

export type CustomerFilterKey =
  | "all"
  | "churn"
  | "not_churn"
  | "train"
  | "validation"
  | "test"
  | "sample";

export type CustomerSortKey =
  | "customer_id"
  | "history"
  | "tenure"
  | "actual_label"
  | "activity"
  | "spend"
  | "days_since_last_txn"
  | "total_lifetime_spend";

export type CustomerSortDirection = "asc" | "desc";

export type CustomerPageParams = {
  page: number;
  limit: number;
  q?: string;
  filter?: CustomerFilterKey;
  sort?: CustomerSortKey;
  direction?: CustomerSortDirection;
};

export type PredictionResponse = {
  customer_id: string;
  actual_label?: number | null;
  actual_label_name?: "Churn" | "Not Churn" | string | null;
  predictions: PredictionResult[];
  highest_probability_model: string;
  recommendation: string;
};

export type BestModel = {
  model_name: string;
  score: number;
  reason: string;
};

export type ExplanationFeature = {
  name: string;
  importance: number;
  display_value?: string | null;
};

export type ModelExplanation = {
  model: "TFT" | "TabNet" | string;
  prediction_label?: string | null;
  churn_probability?: number | null;
  top_features: ExplanationFeature[];
  explanation_type: string;
  notes: string[];
  warnings: string[];
};

export type ExplanationResponse = {
  customer_id: string;
  models: ModelExplanation[];
  warnings: string[];
  source: string;
  artifact_version?: Record<string, string> | null;
};

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export const api = {
  getMetrics: () => request<ModelMetrics[]>("/metrics"),
  getCustomers: () => request<Customer[]>("/customers"),
  getCustomerPage: ({ page, limit, q, filter, sort, direction }: CustomerPageParams) => {
    const query = new URLSearchParams({
      offset: String((page - 1) * limit),
      limit: String(limit),
    });

    if (q?.trim()) {
      query.set("q", q.trim());
    }
    if (filter) {
      query.set("filter", filter);
    }
    if (sort) {
      query.set("sort", sort);
    }
    if (direction) {
      query.set("direction", direction);
    }

    return request<CustomerPage>(`/customers/page?${query.toString()}`);
  },
  getCustomer: (customerId: string) => request<Customer>(`/customers/${customerId}`),
  getRandomCustomer: () => request<Customer>("/customers/random"),
  getBestModel: () => request<BestModel>("/best-model"),
  getExplanations: (customerId: string) =>
    request<ExplanationResponse>(`/explanations/${customerId}`),
  predict: (customerId: string) =>
    request<PredictionResponse>("/predict", {
      method: "POST",
      body: JSON.stringify({ customer_id: customerId }),
    }),
};
