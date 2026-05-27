from __future__ import annotations

import argparse
import sys
import time
from typing import Any

from explainability_smoke_utils import (
    first_customer_id,
    normalize_top_features,
    print_json,
    row_display_values,
)


def _extract_local_importance(explanation: Any, feature_count: int) -> Any:
    import numpy as np

    if isinstance(explanation, tuple):
        candidates = list(explanation)
    else:
        candidates = [explanation]

    for candidate in candidates:
        if isinstance(candidate, dict):
            if not candidate:
                continue
            arrays = [np.asarray(value, dtype="float64") for value in candidate.values()]
            reduced = sum(_first_row(array) for array in arrays)
            if reduced.size == feature_count:
                return reduced
            continue

        array = np.asarray(candidate, dtype="float64")
        reduced = _first_row(array)
        if reduced.size == feature_count:
            return reduced

    shapes = [_shape_of(candidate) for candidate in candidates]
    raise ValueError(
        "Could not map TabNet explanation output to feature columns. "
        f"Expected {feature_count} values; observed shapes: {shapes}"
    )


def _first_row(array: Any) -> Any:
    import numpy as np

    normalized = np.asarray(array, dtype="float64")
    if normalized.ndim == 1:
        return normalized
    return normalized.reshape(normalized.shape[0], -1)[0]


def _shape_of(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _shape_of(item) for key, item in value.items()}
    return getattr(value, "shape", type(value).__name__)


def run(customer_id: str | None, top_k: int) -> dict[str, Any]:
    from app.services.artifact_data_service import (
        TABNET_MODEL_PATH,
        latest_customer_row,
        load_tabnet_feature_columns,
    )
    from app.services.artifact_prediction_service import _load_tabnet_model

    selected_customer_id = first_customer_id(customer_id)
    feature_columns = load_tabnet_feature_columns()
    row = latest_customer_row(selected_customer_id)
    x = row[feature_columns].astype("float32").to_frame().T.to_numpy().copy()

    started = time.perf_counter()
    model = _load_tabnet_model()
    probability = float(model.predict_proba(x)[0][1])
    explanation = model.explain(x)
    importance = _extract_local_importance(explanation, len(feature_columns))
    top_features = normalize_top_features(
        feature_names=feature_columns,
        importance_values=importance,
        display_values=row_display_values(row, feature_columns),
        top_k=top_k,
    )

    return {
        "status": "passed",
        "model": "TabNet",
        "customer_id": selected_customer_id,
        "artifact": str(TABNET_MODEL_PATH),
        "churn_probability": probability,
        "explanation_type": "native_tabnet_mask",
        "direction_policy": "unknown",
        "notes": [
            "TabNet native mask values are local feature importance, not signed churn contribution.",
            "Direction is intentionally unknown.",
        ],
        "top_features": top_features,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test native TabNet local explainability.")
    parser.add_argument("--customer-id", help="Customer ID from the sample parquet.")
    parser.add_argument("--top-k", type=int, default=10, help="Number of top features to print.")
    args = parser.parse_args()

    try:
        payload = run(args.customer_id, args.top_k)
    except Exception as exc:
        payload = {
            "status": "failed",
            "model": "TabNet",
            "error": f"{type(exc).__name__}: {exc}",
            "notes": [
                "No fallback or fake explanation was generated.",
                "Validate model artifact, feature order, and pytorch-tabnet explain output shape.",
            ],
        }
        print_json(payload)
        return 1

    print_json(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
