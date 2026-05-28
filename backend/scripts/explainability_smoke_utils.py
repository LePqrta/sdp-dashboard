from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, default=_json_default))


def normalize_top_features(
    *,
    feature_names: list[str],
    importance_values: Any,
    display_values: dict[str, Any],
    top_k: int,
) -> list[dict[str, Any]]:
    values = _as_float_list(importance_values)
    if len(values) != len(feature_names):
        raise ValueError(
            f"Expected {len(feature_names)} importance values, got {len(values)}"
        )

    ranked = sorted(
        zip(feature_names, values, strict=True),
        key=lambda item: abs(item[1]),
        reverse=True,
    )
    return [
        {
            "name": name,
            "importance": round(float(value), 6),
            "display_value": _format_display_value(display_values.get(name)),
        }
        for name, value in ranked[:top_k]
    ]


def first_customer_id(explicit_customer_id: str | None = None) -> str:
    if explicit_customer_id:
        return explicit_customer_id

    from app.services.artifact_data_service import load_latest_customer_rows

    rows = load_latest_customer_rows().sort_values("cust_id")
    if rows.empty:
        raise ValueError("No sample customer IDs are available")
    return str(rows.iloc[0]["cust_id"])


def row_display_values(row: Any, feature_names: list[str]) -> dict[str, Any]:
    return {name: row.get(name) for name in feature_names}


def _as_float_list(values: Any) -> list[float]:
    import numpy as np

    array = np.asarray(values, dtype="float64")
    if array.ndim == 0:
        return [float(array)]
    if array.ndim > 1:
        array = array.reshape(-1)
    return [float(value) for value in array.tolist()]


def _format_display_value(value: Any) -> str | None:
    if value is None:
        return None

    try:
        import pandas as pd

        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)


def _json_default(value: Any) -> Any:
    try:
        return value.item()
    except AttributeError:
        return str(value)
