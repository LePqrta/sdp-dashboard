import json
import random
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from app.schemas.customer import Customer, CustomerPage
from app.schemas.metrics import ModelMetrics

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def _read_json(filename: str) -> Any:
    with (DATA_DIR / filename).open("r", encoding="utf-8") as file:
        return json.load(file)


@lru_cache
def load_model_metrics() -> list[ModelMetrics]:
    return [ModelMetrics(**item) for item in _read_json("model_metrics.json")]


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


def load_customer_page(offset: int = 0, limit: int = 25) -> CustomerPage:
    safe_offset = max(0, offset)
    safe_limit = min(max(1, limit), 100)
    try:
        from app.services.artifact_data_service import load_artifact_customer_page

        items, total = load_artifact_customer_page(safe_offset, safe_limit)
        return CustomerPage(items=items, total=total, limit=safe_limit, offset=safe_offset)
    except Exception:
        customers = load_customers()
        return CustomerPage(
            items=customers[safe_offset : safe_offset + safe_limit],
            total=len(customers),
            limit=safe_limit,
            offset=safe_offset,
        )


@lru_cache
def load_mock_predictions() -> dict[str, list[dict[str, Any]]]:
    return _read_json("mock_predictions.json")


@lru_cache
def load_mock_explanations() -> dict[str, dict[str, Any]]:
    return _read_json("mock_explanations.json")


def random_customer() -> Customer:
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
