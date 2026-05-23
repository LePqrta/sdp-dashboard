const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type ModelMetrics = {
  model_name: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  roc_auc: number;
  pr_auc: number;
  model_size_mb: number;
  average_inference_ms: number;
  threshold: number;
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
};

export type PredictionResult = {
  model_name: string;
  churn_probability: number;
  prediction_label: "Churn" | "Not Churn";
  confidence: number;
  inference_ms: number;
};

export type PredictionResponse = {
  customer_id: string;
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
  feature: string;
  contribution: number;
};

export type ExplanationResponse = {
  customer_id: string;
  features: ExplanationFeature[];
  summary: string[];
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
