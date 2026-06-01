from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


BACKEND_DIR = Path(__file__).resolve().parents[1]
SAMPLE_PATH = BACKEND_DIR / "app" / "artifacts" / "datasets" / "sample" / "customers_sample.parquet"
EXPLANATIONS_PATH = (
    BACKEND_DIR / "app" / "artifacts" / "models" / "explainability" / "customer_explanations.json"
)
TABNET_PREDICTIONS_PATH = (
    BACKEND_DIR
    / "app"
    / "artifacts"
    / "models"
    / "tabnet"
    / "predictions"
    / "tabnet_l3_latest_test_predictions.parquet"
)
TFT_PREDICTIONS_PATH = (
    BACKEND_DIR / "app" / "artifacts" / "models" / "tft" / "predictions" / "latest_test_predictions.parquet"
)


def main() -> int:
    sample = pd.read_parquet(SAMPLE_PATH)
    explanations = json.loads(EXPLANATIONS_PATH.read_text(encoding="utf-8"))
    customers = explanations.get("customers", {})

    latest_rows = sample.sort_values("time_idx").groupby(sample["cust_id"].astype(str), sort=False).tail(1)
    sample_ids = set(latest_rows["cust_id"].astype(str))
    explanation_ids = set(customers.keys())
    overlap_ids = sample_ids & explanation_ids
    missing_ids = sample_ids - explanation_ids
    extra_ids = explanation_ids - sample_ids

    print("Explainability alignment")
    print("========================")
    print(f"sample_rows: {len(sample)}")
    print(f"sample_customers: {len(sample_ids)}")
    print(f"explanation_customers: {len(explanation_ids)}")
    print(f"matching_customers: {len(overlap_ids)}")
    print(f"missing_explanations_for_sample: {len(missing_ids)}")
    print(f"extra_explanations_not_in_sample: {len(extra_ids)}")
    print(f"coverage_percent: {len(overlap_ids) / max(len(sample_ids), 1) * 100:.2f}")
    print(f"missing_first_10: {sorted(missing_ids)[:10]}")
    print(f"extra_first_10: {sorted(extra_ids)[:10]}")

    print()
    print("Model availability in explanation artifact")
    print("==========================================")
    both = 0
    tabnet_only = 0
    tft_only = 0
    neither = 0
    for customer in customers.values():
        model_names = {model.get("model") for model in customer.get("models", [])}
        has_tabnet = "TabNet" in model_names
        has_tft = "TFT" in model_names
        if has_tabnet and has_tft:
            both += 1
        elif has_tabnet:
            tabnet_only += 1
        elif has_tft:
            tft_only += 1
        else:
            neither += 1
    print(f"both_models: {both}")
    print(f"tabnet_only: {tabnet_only}")
    print(f"tft_only: {tft_only}")
    print(f"neither: {neither}")

    print()
    print("Prediction probability spot check")
    print("=================================")
    tabnet_predictions = pd.read_parquet(TABNET_PREDICTIONS_PATH)
    tft_predictions = pd.read_parquet(TFT_PREDICTIONS_PATH)
    for customer_id in sorted(overlap_ids)[:10]:
        row = _probability_row(customer_id, customers, tabnet_predictions, tft_predictions)
        print(row)

    return 0 if not missing_ids and not extra_ids else 1


def _probability_row(
    customer_id: str,
    customers: dict[str, Any],
    tabnet_predictions: pd.DataFrame,
    tft_predictions: pd.DataFrame,
) -> dict[str, Any]:
    models = {model.get("model"): model for model in customers[customer_id].get("models", [])}
    exp_tabnet = models.get("TabNet", {}).get("churn_probability")
    exp_tft = models.get("TFT", {}).get("churn_probability")
    cached_tabnet = _tabnet_probability(customer_id, tabnet_predictions) if exp_tabnet is not None else None
    cached_tft = _tft_probability(customer_id, tft_predictions) if exp_tft is not None else None
    return {
        "customer_id": customer_id,
        "exp_tabnet": exp_tabnet,
        "cached_tabnet": cached_tabnet,
        "tabnet_diff": _diff(exp_tabnet, cached_tabnet),
        "exp_tft": exp_tft,
        "cached_tft": cached_tft,
        "tft_diff": _diff(exp_tft, cached_tft),
    }


def _tabnet_probability(customer_id: str, predictions: pd.DataFrame) -> float | None:
    rows = predictions[predictions["cust_id"].astype(str) == customer_id]
    if rows.empty:
        return None
    return float(rows.iloc[0]["prob_churn"])


def _tft_probability(customer_id: str, predictions: pd.DataFrame) -> float | None:
    rows = predictions[predictions["cust_id"].astype(str) == customer_id]
    if rows.empty:
        return None
    row = rows.sort_values("eval_time_idx").tail(1).iloc[0]
    column = "score_calibrated" if "score_calibrated" in row else "score_raw"
    return float(row[column])


def _diff(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return round(abs(float(left) - float(right)), 10)


if __name__ == "__main__":
    raise SystemExit(main())
