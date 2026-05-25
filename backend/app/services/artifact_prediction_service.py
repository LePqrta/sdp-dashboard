from __future__ import annotations

import logging
import time
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.schemas.prediction import PredictionResult
from app.services.artifact_data_service import (
    TFT_CALIBRATOR_PATH,
    TFT_CHECKPOINT_PATH,
    TABNET_MODEL_PATH,
    customer_panel_rows,
    latest_customer_row,
    load_tabnet_fallback_predictions,
    load_tabnet_feature_columns,
    load_tft_fallback_predictions,
)

for logger_name in ("lightning", "lightning.pytorch", "pytorch_lightning"):
    logging.getLogger(logger_name).setLevel(logging.ERROR)


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


def predict_tft(customer_id: str) -> PredictionResult:
    started = time.perf_counter()
    try:
        probability = _predict_tft_live_probability(customer_id)
        return _prediction_result(
            model_name="TFT",
            probability=probability,
            inference_ms=_elapsed_ms(started),
            source="live_model",
            status="ok",
            message="Live TFT inference completed from the local checkpoint and isotonic calibrator.",
        )
    except Exception as exc:
        probability = _tft_fallback_probability(customer_id)
        return _prediction_result(
            model_name="TFT",
            probability=probability,
            inference_ms=_elapsed_ms(started),
            source="cached_fallback",
            status="fallback",
            message=f"Live TFT inference was unavailable, so cached validated output was used. {type(exc).__name__}: {exc}",
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


@lru_cache
def _load_tft_model_and_parameters() -> tuple[Any, dict[str, Any]]:
    try:
        import torch
        from pytorch_forecasting import TemporalFusionTransformer
        from pytorch_forecasting.metrics import CrossEntropy
    except ImportError as exc:
        raise RuntimeError("TFT live inference requires torch and pytorch-forecasting") from exc

    if not TFT_CHECKPOINT_PATH.exists():
        raise FileNotFoundError(f"TFT checkpoint artifact not found: {TFT_CHECKPOINT_PATH}")

    checkpoint = torch.load(TFT_CHECKPOINT_PATH, map_location="cpu", weights_only=False)
    dataset_parameters = checkpoint.get("dataset_parameters")
    if not isinstance(dataset_parameters, dict):
        raise ValueError("TFT checkpoint does not contain dataset_parameters")

    # The training checkpoint stores torchmetrics objects on CUDA. For CPU demo
    # inference we keep weights/config intact and remove only non-inference metrics.
    hyperparameters = checkpoint.get("hyper_parameters", {})
    hyperparameters.pop("logging_metrics", None)
    hyperparameters["loss"] = CrossEntropy()
    checkpoint["hyper_parameters"] = hyperparameters

    special_save = checkpoint.get("__special_save__", {})
    special_save.pop("logging_metrics", None)
    special_save["loss"] = CrossEntropy()
    checkpoint["__special_save__"] = special_save

    sanitized_path = Path(tempfile.gettempdir()) / "churn_dashboard_tft_cpu.ckpt"
    torch.save(checkpoint, sanitized_path)

    model = TemporalFusionTransformer.load_from_checkpoint(str(sanitized_path), map_location="cpu")
    model.eval()
    return model, dataset_parameters


@lru_cache
def _load_tft_calibrator() -> Any:
    import pickle

    if not TFT_CALIBRATOR_PATH.exists():
        raise FileNotFoundError(f"TFT calibrator artifact not found: {TFT_CALIBRATOR_PATH}")
    with TFT_CALIBRATOR_PATH.open("rb") as file:
        return pickle.load(file)


def _predict_tabnet_live_probability(customer_id: str) -> float:
    feature_columns = load_tabnet_feature_columns()
    row = latest_customer_row(customer_id)
    model = _load_tabnet_model()
    x = row[feature_columns].astype("float32").to_frame().T.to_numpy().copy()
    probability = float(model.predict_proba(x)[0][1])
    return _valid_probability(probability, "TabNet live")


def _predict_tft_live_probability(customer_id: str) -> float:
    import torch
    from pytorch_forecasting import TimeSeriesDataSet

    model, dataset_parameters = _load_tft_model_and_parameters()
    panel = customer_panel_rows(customer_id).copy()
    panel["cust_id"] = panel["cust_id"].astype(str)
    dataset = TimeSeriesDataSet.from_parameters(
        dataset_parameters,
        panel,
        predict=True,
        stop_randomization=True,
    )
    dataloader = dataset.to_dataloader(train=False, batch_size=1, num_workers=0)
    with torch.no_grad():
        raw_prediction = model.predict(
            dataloader,
            mode="raw",
            trainer_kwargs={"logger": False, "enable_progress_bar": False},
        ).prediction
    raw_probability = float(torch.softmax(raw_prediction.squeeze(0).squeeze(0), dim=-1)[1])
    calibrator = _load_tft_calibrator()
    calibrated_probability = float(calibrator.predict([[raw_probability]])[0])
    return _valid_probability(calibrated_probability, "TFT live")


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
