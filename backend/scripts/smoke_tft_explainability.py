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


def _prediction_output(raw_result: Any) -> Any:
    return getattr(raw_result, "output", raw_result)


def _prediction_tensor(raw_output: Any) -> Any:
    prediction = getattr(raw_output, "prediction", None)
    if prediction is None and isinstance(raw_output, dict):
        prediction = raw_output.get("prediction")
    if prediction is None:
        raise ValueError(f"Raw TFT output has no prediction field. Type={type(raw_output).__name__}")
    return prediction


def _interpretation_keys(interpretation: Any) -> list[str]:
    if isinstance(interpretation, dict):
        return sorted(str(key) for key in interpretation.keys())
    if hasattr(interpretation, "_asdict"):
        return sorted(str(key) for key in interpretation._asdict().keys())
    return sorted(name for name in dir(interpretation) if not name.startswith("_"))


def _interpretation_value(interpretation: Any, key: str) -> Any:
    if isinstance(interpretation, dict):
        return interpretation.get(key)
    if hasattr(interpretation, "_asdict"):
        return interpretation._asdict().get(key)
    return getattr(interpretation, key, None)


def _feature_names(dataset_parameters: dict[str, Any], key: str, count: int) -> list[str]:
    candidates = [
        dataset_parameters.get(key),
        dataset_parameters.get("time_varying_reals_encoder"),
        dataset_parameters.get("time_varying_known_reals"),
        dataset_parameters.get("x_reals"),
    ]
    for candidate in candidates:
        if isinstance(candidate, list) and len(candidate) == count:
            return [str(item) for item in candidate]
    return [f"{key}_{index}" for index in range(count)]


def _top_from_interpretation(
    *,
    interpretation: Any,
    dataset_parameters: dict[str, Any],
    latest_row: Any,
    top_k: int,
) -> list[dict[str, Any]]:
    for key in ("encoder_variables", "decoder_variables", "static_variables"):
        values = _interpretation_value(interpretation, key)
        if values is None:
            continue

        feature_values = _flatten_importance(values)
        if not feature_values:
            continue

        feature_names = _feature_names(dataset_parameters, key, len(feature_values))
        return normalize_top_features(
            feature_names=feature_names,
            importance_values=feature_values,
            display_values=row_display_values(latest_row, feature_names),
            top_k=top_k,
        )

    return []


def _flatten_importance(values: Any) -> list[float]:
    import numpy as np

    try:
        import torch

        if isinstance(values, torch.Tensor):
            values = values.detach().cpu().numpy()
    except ImportError:
        pass

    array = np.asarray(values, dtype="float64")
    if array.size == 0:
        return []
    while array.ndim > 1:
        array = array.mean(axis=0)
    return [float(value) for value in array.tolist()]


def run(customer_id: str | None, top_k: int) -> dict[str, Any]:
    import torch
    from pytorch_forecasting import TimeSeriesDataSet

    from app.services.artifact_data_service import TFT_CHECKPOINT_PATH, customer_panel_rows
    from app.services.artifact_prediction_service import _load_tft_model_and_parameters

    selected_customer_id = first_customer_id(customer_id)
    started = time.perf_counter()
    model, dataset_parameters = _load_tft_model_and_parameters()

    panel = customer_panel_rows(selected_customer_id).copy()
    panel["cust_id"] = panel["cust_id"].astype(str)
    latest_row = panel.sort_values("time_idx").tail(1).iloc[0]
    dataset = TimeSeriesDataSet.from_parameters(
        dataset_parameters,
        panel,
        predict=True,
        stop_randomization=True,
    )
    dataloader = dataset.to_dataloader(train=False, batch_size=1, num_workers=0)

    with torch.no_grad():
        raw_result = model.predict(
            dataloader,
            mode="raw",
            return_x=True,
            trainer_kwargs={"logger": False, "enable_progress_bar": False},
        )

    raw_output = _prediction_output(raw_result)
    prediction = _prediction_tensor(raw_output)
    raw_probability = float(torch.softmax(prediction.squeeze(0).squeeze(0), dim=-1)[1])

    try:
        interpretation = model.interpret_output(raw_output, reduction="none")
    except Exception as exc:
        return {
            "status": "failed",
            "model": "TFT",
            "customer_id": selected_customer_id,
            "artifact": str(TFT_CHECKPOINT_PATH),
            "churn_probability_raw": raw_probability,
            "error": f"{type(exc).__name__}: {exc}",
            "notes": [
                "Native TFT interpretation failed; no fake explanation was generated.",
                "Verify PyTorch Forecasting raw output compatibility with interpret_output.",
            ],
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
        }

    keys = _interpretation_keys(interpretation)
    top_features = _top_from_interpretation(
        interpretation=interpretation,
        dataset_parameters=dataset_parameters,
        latest_row=latest_row,
        top_k=top_k,
    )

    return {
        "status": "passed" if top_features else "partial",
        "model": "TFT",
        "customer_id": selected_customer_id,
        "artifact": str(TFT_CHECKPOINT_PATH),
        "churn_probability_raw": raw_probability,
        "explanation_type": "native_tft_interpret_output",
        "raw_interpretation_keys": keys,
        "direction_policy": "unknown",
        "notes": [
            "TFT interpretation values are variable/attention importance, not signed churn contribution.",
            "Direction is intentionally unknown.",
        ],
        "top_features": top_features,
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test native TFT local interpretation.")
    parser.add_argument("--customer-id", help="Customer ID from the sample parquet.")
    parser.add_argument("--top-k", type=int, default=10, help="Number of top features to print.")
    args = parser.parse_args()

    try:
        payload = run(args.customer_id, args.top_k)
    except Exception as exc:
        payload = {
            "status": "failed",
            "model": "TFT",
            "error": f"{type(exc).__name__}: {exc}",
            "notes": [
                "No fallback or fake explanation was generated.",
                "Validate checkpoint, dataset reconstruction, and PyTorch Forecasting compatibility.",
            ],
        }
        print_json(payload)
        return 1

    print_json(payload)
    return 0 if payload["status"] in {"passed", "partial"} else 1


if __name__ == "__main__":
    sys.exit(main())
