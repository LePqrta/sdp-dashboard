from app.schemas.prediction import PredictionResponse, PredictionResult
from app.services.artifact_prediction_service import predict_nhits_mock, predict_tabnet, predict_tft
from app.services.mock_data_service import find_customer, load_mock_predictions
from app.services.model_selection_service import select_best_for_customer


def predict_for_customer(customer_id: str) -> PredictionResponse:
    customer = find_customer(customer_id)
    prediction_map = load_mock_predictions()

    raw_results = prediction_map.get(customer_id, prediction_map["default"])
    mock_by_model = {item["model_name"]: item for item in raw_results}
    results = [
        _safe_model_result("TabNet", lambda: predict_tabnet(customer.customer_id)),
        _safe_model_result("TFT", lambda: predict_tft(customer.customer_id)),
        predict_nhits_mock(mock_by_model.get("NHiTS", prediction_map["default"][1])),
    ]
    best_model = select_best_for_customer(results)

    return PredictionResponse(
        customer_id=customer.customer_id,
        predictions=results,
        highest_probability_model=best_model.model_name,
        recommendation=_build_recommendation(best_model),
    )


def _build_recommendation(best_model: PredictionResult) -> str:
    if best_model.prediction_label == "Churn":
        return (
            f"{best_model.model_name} reports the strongest validated churn signal. "
            "Prioritize this customer for retention outreach."
        )
    return (
        f"{best_model.model_name} has the highest validated churn probability, but the customer is still "
        "classified as Not Churn. Monitor normally."
    )


def _safe_model_result(model_name: str, callback) -> PredictionResult:
    try:
        return callback()
    except Exception as exc:
        return PredictionResult(
            model_name=model_name,
            churn_probability=0.0,
            prediction_label="Not Churn",
            confidence=0.0,
            inference_ms=0.0,
            source="unavailable",
            status="failed",
            message=f"{model_name} prediction is unavailable: {type(exc).__name__}: {exc}",
        )
