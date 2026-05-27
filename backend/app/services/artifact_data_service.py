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

_CUSTOMER_FILTER_ALIASES: dict[str, tuple[str, ...]] = {
    "high_churn_risk": ("high churn risk",),
    "growing_activity": ("growing activity",),
    "stable_monitored": ("stable monitored",),
    "month_to_month": ("month-to-month", "month to month"),
    "one_year": ("one year",),
    "two_year": ("two year",),
}


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


def load_artifact_customer_page(
    offset: int,
    limit: int,
    q: str | None = None,
    filter: str | None = None,
    sort: str = "customer_id",
    direction: str = "asc",
) -> tuple[list[Customer], int]:
    latest_rows = load_demo_customer_rows()
    latest_rows = _search_customer_rows(latest_rows, q)
    latest_rows = _filter_customer_rows(latest_rows, filter)
    latest_rows = _sort_customer_rows(latest_rows, sort, direction)
    total = int(len(latest_rows))
    page_rows = latest_rows.iloc[offset : offset + limit]
    return [_row_to_customer(row) for _, row in page_rows.iterrows()], total


def _search_customer_rows(rows: Any, q: str | None) -> Any:
    search_term = (q or "").strip().casefold()
    if not search_term:
        return rows

    mask = [_customer_row_search_text(row).find(search_term) >= 0 for _, row in rows.iterrows()]
    return rows.loc[mask]


def _filter_customer_rows(rows: Any, filter: str | None) -> Any:
    filter_key = (filter or "all").strip().casefold()
    if filter_key == "all":
        return rows

    aliases = _CUSTOMER_FILTER_ALIASES.get(filter_key, (filter_key.replace("_", " "),))
    mask = [_customer_row_matches_filter(row, aliases) for _, row in rows.iterrows()]
    return rows.loc[mask]


def _sort_customer_rows(rows: Any, sort: str, direction: str) -> Any:
    if rows.empty:
        return rows

    descending = direction.strip().casefold() == "desc"
    sort_values = [_customer_row_sort_value(row, sort) for _, row in rows.iterrows()]
    helper_column = "__customer_sort_value"
    sortable_rows = rows.assign(**{helper_column: sort_values})
    present_rows = sortable_rows[sortable_rows[helper_column].map(lambda value: not _is_missing_sort_value(value))]
    missing_rows = sortable_rows[sortable_rows[helper_column].map(_is_missing_sort_value)]
    sorted_rows = present_rows.sort_values(
        helper_column,
        ascending=not descending,
        kind="mergesort",
        key=lambda series: series.map(_normalize_sort_value),
    )
    pd = _import_pandas()
    return pd.concat(
        [
            sorted_rows.drop(columns=[helper_column]),
            missing_rows.drop(columns=[helper_column]),
        ]
    )


def _customer_row_search_text(row: Any) -> str:
    values = (
        row.get("cust_id"),
        _segment_for_row(row),
        row.get("split"),
        row.get("l3_component_category"),
        row.get("history_months_available"),
        row.get("tenure_months"),
        row.get("txn_count_3m"),
        row.get("spend_3m"),
    )
    return " ".join(str(value).casefold() for value in values if not _is_missing_sort_value(value))


def _customer_row_matches_filter(row: Any, aliases: tuple[str, ...]) -> bool:
    candidate_values = (
        _segment_for_row(row),
        row.get("split"),
        row.get("l3_component_category"),
    )
    normalized_candidates = {
        str(value).strip().casefold()
        for value in candidate_values
        if not _is_missing_sort_value(value)
    }
    return any(alias in normalized_candidates for alias in aliases)


def _customer_row_sort_value(row: Any, sort: str) -> Any:
    sort_key = sort.strip().casefold()
    if sort_key == "customer_id":
        return str(row.get("cust_id"))
    if sort_key in {"history", "history_months_available"}:
        return _numeric_row_value(row, "history_months_available", fallback_column="tenure_months")
    if sort_key in {"tenure", "tenure_months"}:
        return _numeric_row_value(row, "tenure_months")
    if sort_key in {"segment", "customer_segment"}:
        return _segment_for_row(row)
    if sort_key in {"activity", "txn_count_3m"}:
        return _numeric_row_value(row, "txn_count_3m")
    if sort_key in {"spend", "spend_3m"}:
        return _numeric_row_value(row, "spend_3m")
    if sort_key == "days_since_last_txn":
        return _numeric_row_value(row, "days_since_last_txn")
    if sort_key == "total_lifetime_spend":
        return _numeric_row_value(row, "total_lifetime_spend")
    return str(row.get("cust_id"))


def _numeric_row_value(row: Any, column: str, fallback_column: str | None = None) -> float | None:
    value = row.get(column)
    if _is_missing_sort_value(value):
        if fallback_column is None:
            return None
        fallback = row.get(fallback_column)
        if _is_missing_sort_value(fallback):
            return None
        return _to_float(fallback)
    return _to_float(value)


def _is_missing_sort_value(value: Any) -> bool:
    try:
        pd = _import_pandas()
        return value is None or bool(pd.isna(value)) or str(value).strip() == ""
    except (TypeError, ValueError):
        return value is None or str(value).strip() == ""


def _normalize_sort_value(value: Any) -> Any:
    if isinstance(value, str):
        return value.casefold()
    return value


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
