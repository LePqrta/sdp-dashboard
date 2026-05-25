from __future__ import annotations

import json
import random
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from app.schemas.customer import Customer

BACKEND_APP_DIR = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = BACKEND_APP_DIR / "artifacts"
SAMPLE_PATH = ARTIFACTS_DIR / "datasets" / "sample" / "customers_sample.parquet"

TABNET_MODEL_PATH = (
    ARTIFACTS_DIR
    / "models"
    / "tabnet"
    / "model"
    / "best_tabnet_l3_gold_v1_20260523_233256.zip"
)
TABNET_FEATURES_PATH = (
    ARTIFACTS_DIR / "models" / "tabnet" / "configs" / "tabnet_l3_used_feature_columns.json"
)
TABNET_FALLBACK_PATH = (
    ARTIFACTS_DIR / "models" / "tabnet" / "predictions" / "tabnet_l3_latest_test_predictions.parquet"
)
TFT_FALLBACK_PATH = ARTIFACTS_DIR / "models" / "tft" / "predictions" / "latest_test_predictions.parquet"
TFT_CHECKPOINT_PATH = (
    ARTIFACTS_DIR
    / "models"
    / "tft"
    / "checkpoints"
    / "tft-l3-gold-v1-epoch=04-val_loss=0.6388.ckpt"
)
TFT_CALIBRATOR_PATH = ARTIFACTS_DIR / "models" / "tft" / "calibration" / "isotonic_calibrator.pkl"
DEMO_CUSTOMER_LIMIT = 5000


def _import_pandas() -> Any:
    try:
        import pandas as pd
    except ImportError as exc:
        raise RuntimeError(
            "Artifact-backed customers require pandas and pyarrow. Install backend ML dependencies first."
        ) from exc
    return pd


def _to_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        pd = _import_pandas()
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int = 0) -> int:
    return int(round(_to_float(value, float(default))))


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache
def load_customer_sample() -> Any:
    if not SAMPLE_PATH.exists():
        raise FileNotFoundError(f"Customer sample not found: {SAMPLE_PATH}")
    pd = _import_pandas()
    return pd.read_parquet(SAMPLE_PATH)


@lru_cache
def load_latest_customer_rows() -> Any:
    df = load_customer_sample().copy()
    df["cust_id"] = df["cust_id"].astype(str)
    return df.sort_values(["cust_id", "time_idx"]).groupby("cust_id", as_index=False).tail(1)


@lru_cache
def load_demo_customer_rows() -> Any:
    return load_latest_customer_rows().sort_values("cust_id").head(DEMO_CUSTOMER_LIMIT)


@lru_cache
def load_tabnet_feature_columns() -> list[str]:
    return list(_read_json(TABNET_FEATURES_PATH)["feature_cols"])


@lru_cache
def load_tabnet_fallback_predictions() -> Any:
    pd = _import_pandas()
    return pd.read_parquet(TABNET_FALLBACK_PATH)


@lru_cache
def load_tft_fallback_predictions() -> Any:
    pd = _import_pandas()
    return pd.read_parquet(TFT_FALLBACK_PATH)


def load_artifact_customers() -> list[Customer]:
    latest_rows = load_demo_customer_rows()
    return [_row_to_customer(row) for _, row in latest_rows.iterrows()]


def load_artifact_customer_page(offset: int, limit: int) -> tuple[list[Customer], int]:
    latest_rows = load_demo_customer_rows()
    total = int(len(latest_rows))
    page_rows = latest_rows.iloc[offset : offset + limit]
    return [_row_to_customer(row) for _, row in page_rows.iterrows()], total


def random_artifact_customer() -> Customer:
    latest_rows = load_demo_customer_rows()
    if latest_rows.empty:
        raise HTTPException(status_code=404, detail="No artifact customers available")
    row = latest_rows.sample(n=1).iloc[0]
    return _row_to_customer(row)


def find_artifact_customer(customer_id: str) -> Customer:
    row = latest_customer_row(customer_id)
    return _row_to_customer(row)


def latest_customer_row(customer_id: str) -> Any:
    latest_rows = load_latest_customer_rows()
    matches = latest_rows[latest_rows["cust_id"].astype(str) == str(customer_id)]
    if matches.empty:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found in sample parquet")
    return matches.iloc[0]


def customer_panel_rows(customer_id: str) -> Any:
    df = load_customer_sample()
    matches = df[df["cust_id"].astype(str) == str(customer_id)].sort_values("time_idx")
    if matches.empty:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found in sample parquet")
    return matches


def _row_to_customer(row: Any) -> Customer:
    segment = _segment_for_row(row)
    history_months = _to_int(row.get("history_months_available"), _to_int(row.get("tenure_months")))
    spend_3m = _to_float(row.get("spend_3m"))
    total_spend = _to_float(row.get("total_lifetime_spend"))
    txn_count_3m = _to_float(row.get("txn_count_3m"))
    days_since_last_txn = _to_float(row.get("days_since_last_txn"))

    return Customer(
        customer_id=str(row.get("cust_id")),
        # Compatibility fields for the original UI. The richer fields below are preferred by new views.
        age=history_months,
        tenure_months=_to_int(row.get("tenure_months")),
        contract_type=segment,
        monthly_charges=spend_3m,
        total_charges=total_spend,
        internet_service=str(row.get("split", "sample")),
        payment_method=str(row.get("l3_component_category", "unknown")),
        support_tickets=_to_int(txn_count_3m),
        late_payments=_to_int(days_since_last_txn),
        split=str(row.get("split", "")),
        latest_time_idx=_to_int(row.get("time_idx")),
        customer_segment=segment,
        history_months_available=history_months,
        txn_count_3m=txn_count_3m,
        spend_3m=spend_3m,
        avg_txn_amt_3m=_to_float(row.get("avg_txn_amt_3m")),
        total_transaction_count=_to_float(row.get("total_transaction_count")),
        total_lifetime_spend=total_spend,
        days_since_last_txn=days_since_last_txn,
    )


def _segment_for_row(row: Any) -> str:
    days_since_last_txn = _to_float(row.get("days_since_last_txn"))
    spend_ratio = _to_float(row.get("spend_ratio"), 1.0)
    txn_ratio = _to_float(row.get("txn_ratio"), 1.0)
    component = str(row.get("l3_component_category", "")).lower()

    if component in {"hard", "soft"} or days_since_last_txn >= 90 or spend_ratio < 0.5:
        return "High churn risk"
    if spend_ratio >= 1.1 or txn_ratio >= 1.1:
        return "Growing activity"
    return "Stable monitored"


def sample_customer_ids(limit: int = 3) -> list[str]:
    ids = load_latest_customer_rows()["cust_id"].astype(str).drop_duplicates().tolist()
    if len(ids) <= limit:
        return ids
    return random.sample(ids, limit)
