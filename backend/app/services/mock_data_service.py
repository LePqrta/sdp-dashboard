import json
import random
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from fastapi import HTTPException

from app.schemas.customer import Customer, CustomerPage
from app.schemas.metrics import ModelMetrics

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

CustomerFilterKey = Literal[
    "all",
    "churn",
    "not_churn",
    "train",
    "validation",
    "test",
    "sample",
]
CustomerSortKey = Literal[
    "customer_id",
    "history",
    "history_months_available",
    "tenure",
    "tenure_months",
    "actual_label",
    "activity",
    "txn_count_3m",
    "spend",
    "spend_3m",
    "days_since_last_txn",
    "total_lifetime_spend",
]
CustomerSortDirection = Literal["asc", "desc"]

DEFAULT_CUSTOMER_SORT: CustomerSortKey = "customer_id"
DEFAULT_CUSTOMER_DIRECTION: CustomerSortDirection = "asc"

_CUSTOMER_FILTER_ALIASES: dict[str, tuple[str, ...]] = {
    "churn": ("1", "churn"),
    "not_churn": ("0", "not churn"),
}


def _read_json(filename: str) -> Any:
    with (DATA_DIR / filename).open("r", encoding="utf-8") as file:
        return json.load(file)


@lru_cache
def load_model_metrics() -> list[ModelMetrics]:
    return [
        _load_tft_final_metrics(),
        _load_tabnet_final_metrics(),
    ]


def _load_tft_final_metrics() -> ModelMetrics:
    summary = _read_json("tft_l3_final_summary.json")
    result = summary.get("calibrated_results", {}).get("latest_test", {})
    threshold_metrics = result.get("metrics_f1", {})
    model_size_mb = _model_artifact_size_mb("TFT")

    return ModelMetrics(
        model_name="TFT",
        accuracy=_safe_accuracy(threshold_metrics),
        precision=_safe_float(threshold_metrics.get("precision")),
        recall=_safe_float(threshold_metrics.get("recall")),
        f1_score=_safe_float(threshold_metrics.get("f1")),
        roc_auc=_safe_float(result.get("auc")),
        pr_auc=_safe_float(result.get("ap")),
        model_size_mb=model_size_mb,
        threshold=_safe_float(threshold_metrics.get("threshold")),
    )


def _load_tabnet_final_metrics() -> ModelMetrics:
    summary = _read_json("tabnet_l3_final_summary.json")
    result = summary.get("best_result", {})
    model_size_mb = _model_artifact_size_mb("TabNet")

    return ModelMetrics(
        model_name="TabNet",
        accuracy=_safe_float(result.get("test_chosen_accuracy")),
        precision=_safe_float(result.get("test_chosen_precision")),
        recall=_safe_float(result.get("test_chosen_recall")),
        f1_score=_safe_float(result.get("test_chosen_f1")),
        roc_auc=_safe_float(result.get("test_auc")),
        pr_auc=_safe_float(result.get("test_ap")),
        model_size_mb=model_size_mb,
        threshold=_safe_float(result.get("test_chosen_threshold")),
    )


def _model_artifact_size_mb(model_name: str) -> float | None:
    try:
        from app.services.artifact_data_service import TABNET_MODEL_PATH, TFT_CHECKPOINT_PATH
    except Exception:
        return None

    artifact_paths = {
        "TFT": TFT_CHECKPOINT_PATH,
        "TabNet": TABNET_MODEL_PATH,
    }
    path = artifact_paths.get(model_name)
    if path is None:
        return None

    size_bytes = _path_size_bytes(path)
    if size_bytes is None:
        return None
    return round(size_bytes / (1024 * 1024), 2)


def _path_size_bytes(path: Path) -> int | None:
    if path.is_file():
        return path.stat().st_size
    if path.is_dir():
        return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())
    return None


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_accuracy(metrics: dict[str, Any]) -> float | None:
    tn = _safe_float(metrics.get("tn"))
    fp = _safe_float(metrics.get("fp"))
    fn = _safe_float(metrics.get("fn"))
    tp = _safe_float(metrics.get("tp"))
    if None in {tn, fp, fn, tp}:
        return None

    total = tn + fp + fn + tp
    if total <= 0:
        return None
    return (tp + tn) / total


@lru_cache
def load_customers() -> list[Customer]:
    try:
        from app.services.artifact_data_service import load_artifact_customers

        return load_artifact_customers()
    except Exception:
        # Fallback keeps the MVP usable when local model artifacts or parquet dependencies
        # are not installed yet.
        pass
    return [Customer(**item) for item in _read_json("sample_customers.json")]


def load_customer_page(
    offset: int = 0,
    limit: int = 25,
    q: str | None = None,
    filter: CustomerFilterKey | None = None,
    sort: CustomerSortKey = DEFAULT_CUSTOMER_SORT,
    direction: CustomerSortDirection = DEFAULT_CUSTOMER_DIRECTION,
) -> CustomerPage:
    safe_offset = max(0, offset)
    safe_limit = min(max(1, limit), 100)

    try:
        from app.services.artifact_data_service import load_artifact_customer_page

        items, total = load_artifact_customer_page(
            safe_offset,
            safe_limit,
            q=q,
            filter=filter,
            sort=sort,
            direction=direction,
        )
        return CustomerPage(items=items, total=total, limit=safe_limit, offset=safe_offset)
    except Exception:
        # Fallback keeps the MVP usable when local model artifacts or parquet dependencies
        # are not installed yet.
        pass

    customers = _search_customers(load_customers(), q)
    customers = _filter_customers(customers, filter)
    customers = _sort_customers(customers, sort, direction)
    return CustomerPage(
        items=customers[safe_offset : safe_offset + safe_limit],
        total=len(customers),
        limit=safe_limit,
        offset=safe_offset,
    )


def _search_customers(customers: list[Customer], q: str | None) -> list[Customer]:
    search_term = (q or "").strip().casefold()
    if not search_term:
        return customers

    return [customer for customer in customers if search_term in _customer_search_text(customer)]


def _filter_customers(customers: list[Customer], filter: CustomerFilterKey | None) -> list[Customer]:
    filter_key = (filter or "all").strip().casefold()
    if filter_key == "all":
        return customers

    aliases = _CUSTOMER_FILTER_ALIASES.get(filter_key, (filter_key.replace("_", " "),))
    return [customer for customer in customers if _customer_matches_filter(customer, aliases)]


def _sort_customers(
    customers: list[Customer],
    sort: CustomerSortKey,
    direction: CustomerSortDirection,
) -> list[Customer]:
    reverse = direction == "desc"
    present: list[tuple[int, Customer, Any]] = []
    missing: list[Customer] = []

    for index, customer in enumerate(customers):
        value = _customer_sort_value(customer, sort)
        if _is_missing_sort_value(value):
            missing.append(customer)
        else:
            present.append((index, customer, value))

    sorted_present = sorted(
        present,
        key=lambda item: _normalize_sort_value(item[2]),
        reverse=reverse,
    )
    return [customer for _, customer, _ in sorted_present] + missing


def _customer_search_text(customer: Customer) -> str:
    values = (
        customer.customer_id,
        customer.actual_label,
        customer.actual_label_name,
        customer.split,
        customer.internet_service,
        customer.payment_method,
        customer.history_months_available,
        customer.tenure_months,
        customer.txn_count_3m,
        customer.spend_3m,
    )
    return " ".join(str(value).casefold() for value in values if value is not None)


def _customer_matches_filter(customer: Customer, aliases: tuple[str, ...]) -> bool:
    candidate_values = (
        customer.actual_label,
        customer.actual_label_name,
        customer.split,
        customer.internet_service,
        customer.payment_method,
    )
    normalized_candidates = {
        str(value).strip().casefold()
        for value in candidate_values
        if value is not None and str(value).strip()
    }
    return any(alias in normalized_candidates for alias in aliases)


def _customer_sort_value(customer: Customer, sort: CustomerSortKey) -> Any:
    if sort in {"history", "history_months_available"}:
        return customer.history_months_available if customer.history_months_available is not None else customer.age
    if sort in {"tenure", "tenure_months"}:
        return customer.tenure_months
    if sort == "actual_label":
        return customer.actual_label
    if sort in {"activity", "txn_count_3m"}:
        return customer.txn_count_3m if customer.txn_count_3m is not None else customer.support_tickets
    if sort in {"spend", "spend_3m"}:
        return customer.spend_3m if customer.spend_3m is not None else customer.monthly_charges
    if sort == "days_since_last_txn":
        return customer.days_since_last_txn
    if sort == "total_lifetime_spend":
        return customer.total_lifetime_spend if customer.total_lifetime_spend is not None else customer.total_charges
    return customer.customer_id


def _is_missing_sort_value(value: Any) -> bool:
    return value is None or str(value).strip() == ""


def _normalize_sort_value(value: Any) -> Any:
    if isinstance(value, str):
        return value.casefold()
    return value


@lru_cache
def load_mock_predictions() -> dict[str, list[dict[str, Any]]]:
    return _read_json("mock_predictions.json")


@lru_cache
def load_mock_explanations() -> dict[str, dict[str, Any]]:
    return _read_json("mock_explanations.json")


def random_customer() -> Customer:
    try:
        from app.services.artifact_data_service import load_demo_customer_rows
        from app.services.explainability_service import explanation_ready_customer_ids

        sample_ids = set(load_demo_customer_rows()["cust_id"].astype(str))
        eligible_ids = [
            customer_id
            for customer_id in explanation_ready_customer_ids(require_both_models=True)
            if customer_id in sample_ids
        ]
        if eligible_ids:
            return find_customer(random.choice(eligible_ids))
    except Exception:
        pass

    try:
        from app.services.artifact_data_service import random_artifact_customer

        return random_artifact_customer()
    except Exception:
        customers = load_customers()
        if not customers:
            raise HTTPException(status_code=404, detail="No customers available")
        return random.choice(customers)


def find_customer(customer_id: str) -> Customer:
    try:
        from app.services.artifact_data_service import find_artifact_customer

        return find_artifact_customer(customer_id)
    except HTTPException:
        pass
    except Exception:
        pass

    for customer in load_customers():
        if customer.customer_id == customer_id:
            return customer
    raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")


def load_explanation_for_customer(customer_id: str) -> dict[str, Any]:
    find_customer(customer_id)
    explanations = load_mock_explanations()
    return explanations.get(customer_id, explanations["default"]) | {"customer_id": customer_id}
