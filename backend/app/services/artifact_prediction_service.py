from __future__ import annotations

import time
from functools import lru_cache
from typing import Any

from app.schemas.prediction import PredictionResult
from app.services.artifact_data_service import (
    TABNET_MODEL_PATH,
    latest_customer_row,
    load_tabnet_fallback_predictions,
    load_tabnet_feature_columns,
    load_tft_fallback_predictions,
)


def predict_tabnet(customer_id: str) -> PredictionResult:
    started = time.perf_counter()
    try:
        probability = _predict_tabnet_live_probability(customer_id)
        return _prediction_result(
            model_name="TabNet",
            probability=probability,
            inference_ms=_elapsed_ms(started),
            source="live_model",
            status="ok",
            message="Live TabNet inference completed from the local model artifact.",
        )
    except Exception as exc:
        probability = _tabnet_fallback_probability(customer_id)
        return _prediction_result(
            model_name="TabNet",
            probability=probability,
            inference_ms=_elapsed_ms(started),
            source="cached_fallback",
            status="fallback",
            message=f"Live TabNet inference was unavailable, so cached validated output was used. {type(exc).__name__}: {exc}",
        )


def predict_tft_cached(customer_id: str) -> PredictionResult:
    started = time.perf_counter()
    probability = _tft_fallback_probability(customer_id)
    return _prediction_result(
        model_name="TFT",
        probability=probability,
        inference_ms=_elapsed_ms(started),
        source="cached_fallback",
        status="ok",
        message="TFT currently uses the validated cached prediction output while live checkpoint loading is resolved.",
    )


def predict_nhits_mock(raw_result: dict[str, Any]) -> PredictionResult:
    return PredictionResult(
        **raw_result,
        source="mock_baseline",
        status="mock",
        message="NHiTS is retained as a mock baseline because it is not part of the live model integration.",
    )


@lru_cache
def _load_tabnet_model() -> Any:
    try:
        from pytorch_tabnet.tab_model import TabNetClassifier
    except ImportError as exc:
        raise RuntimeError("pytorch-tabnet is not installed in the backend environment") from exc

    if not TABNET_MODEL_PATH.exists():
        raise FileNotFoundError(f"TabNet model artifact not found: {TABNET_MODEL_PATH}")

    model = TabNetClassifier()
    model.load_model(str(TABNET_MODEL_PATH))
    return model


def _predict_tabnet_live_probability(customer_id: str) -> float:
    feature_columns = load_tabnet_feature_columns()
    row = latest_customer_row(customer_id)
    model = _load_tabnet_model()
    x = row[feature_columns].astype("float32").to_frame().T.to_numpy().copy()
    probability = float(model.predict_proba(x)[0][1])
    return _valid_probability(probability, "TabNet live")


def _tabnet_fallback_probability(customer_id: str) -> float:
    fallback_df = load_tabnet_fallback_predictions()
    rows = fallback_df[fallback_df["cust_id"].astype(str) == str(customer_id)]
    if rows.empty:
        raise ValueError(f"No TabNet fallback prediction for customer {customer_id}")
    return _valid_probability(float(rows.iloc[0]["prob_churn"]), "TabNet fallback")


def _tft_fallback_probability(customer_id: str) -> float:
    fallback_df = load_tft_fallback_predictions()
    rows = fallback_df[fallback_df["cust_id"].astype(str) == str(customer_id)]
    if rows.empty:
        raise ValueError(f"No TFT fallback prediction for customer {customer_id}")
    row = rows.sort_values("eval_time_idx").tail(1).iloc[0]
    probability = float(row.get("score_calibrated", row.get("score_raw")))
    return _valid_probability(probability, "TFT fallback")


def _prediction_result(
    *,
    model_name: str,
    probability: float,
    inference_ms: float,
    source: str,
    status: str,
    message: str,
) -> PredictionResult:
    return PredictionResult(
        model_name=model_name,
        churn_probability=probability,
        prediction_label="Churn" if probability >= 0.5 else "Not Churn",
        confidence=max(probability, 1 - probability),
        inference_ms=inference_ms,
        source=source,
        status=status,
        message=message,
    )


def _valid_probability(probability: float, context: str) -> float:
    if not 0 <= probability <= 1:
        raise ValueError(f"{context} returned invalid probability: {probability}")
    return probability


def _elapsed_ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 2)
