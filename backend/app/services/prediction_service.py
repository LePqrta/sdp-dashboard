from app.schemas.prediction import PredictionResponse, PredictionResult
from app.services.mock_data_service import find_customer, load_mock_predictions
from app.services.model_selection_service import select_best_for_customer


def predict_for_customer(customer_id: str) -> PredictionResponse:
    customer = find_customer(customer_id)
    prediction_map = load_mock_predictions()

    # Later: replace this mock lookup with real TFT, NHiTS, and TabNet model inference.
    raw_results = prediction_map.get(customer_id, prediction_map["default"])
    results = [PredictionResult(**item) for item in raw_results]
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
            f"{best_model.model_name} reports the strongest churn signal. "
            "Prioritize this customer for retention outreach."
        )
    return (
        f"{best_model.model_name} has the highest churn probability, but the customer is still "
        "classified as Not Churn. Monitor normally."
    )
