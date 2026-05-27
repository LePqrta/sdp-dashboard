from __future__ import annotations

import json
import random
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from app.schemas.explainability import CustomerExplanationResponse
from app.services.artifact_data_service import ARTIFACTS_DIR

EXPLANATIONS_PATH = ARTIFACTS_DIR / "models" / "explainability" / "customer_explanations.json"
SUPPORTED_MODELS = {"TFT", "TabNet"}


@lru_cache
def load_explanation_artifact(path: str | None = None) -> dict[str, Any]:
    artifact_path = Path(path) if path else EXPLANATIONS_PATH
    if not artifact_path.exists():
        raise FileNotFoundError(
            f"Customer explanations artifact not found: {artifact_path}. "
            "Run backend/scripts/generate_customer_explanations.py before requesting explanations."
        )
    return json.loads(artifact_path.read_text(encoding="utf-8"))


def get_customer_explanation(customer_id: str) -> CustomerExplanationResponse:
    try:
        artifact = load_explanation_artifact()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    customers = artifact.get("customers", {})
    customer = customers.get(str(customer_id))
    if customer is None:
        raise HTTPException(
            status_code=404,
            detail=f"Explanation for customer {customer_id} is not available in the generated artifact.",
        )

    models = [
        model
        for model in customer.get("models", [])
        if model.get("model") in SUPPORTED_MODELS
    ]
    warnings = [str(item) for item in customer.get("warnings", [])]
    model_names = {model.get("model") for model in models}
    if "TabNet" in model_names and "TFT" not in model_names:
        warnings.append(
            "TFT explanation is unavailable for this customer; the customer sequence was likely ineligible for the TFT dataset window."
        )

    manifest = artifact.get("manifest", {})
    return CustomerExplanationResponse(
        customer_id=str(customer.get("customer_id", customer_id)),
        models=models,
        warnings=_dedupe(warnings),
        source=str(manifest.get("source", "precomputed_model_explanations")),
        artifact_version=manifest.get("artifact_version"),
    )


def explanation_ready_customer_ids(require_both_models: bool = True) -> list[str]:
    try:
        artifact = load_explanation_artifact()
    except FileNotFoundError:
        return []

    ids: list[str] = []
    for customer_id, customer in artifact.get("customers", {}).items():
        model_names = {
            model.get("model")
            for model in customer.get("models", [])
            if model.get("model") in SUPPORTED_MODELS
        }
        if require_both_models:
            if {"TFT", "TabNet"}.issubset(model_names):
                ids.append(str(customer_id))
        elif model_names:
            ids.append(str(customer_id))
    return ids


def random_explainability_ready_customer_id() -> str | None:
    ids = explanation_ready_customer_ids(require_both_models=True)
    if not ids:
        return None
    return random.choice(ids)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result
