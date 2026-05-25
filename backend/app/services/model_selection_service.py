from app.schemas.metrics import BestModelResponse, ModelMetrics
from app.schemas.prediction import PredictionResult


def select_best_global_model(metrics: list[ModelMetrics]) -> BestModelResponse:
    scored = [(item, _global_score(item)) for item in metrics]
    best_metric, best_score = max(scored, key=lambda pair: pair[1])
    return BestModelResponse(
        model_name=best_metric.model_name,
        score=round(best_score, 4),
        reason=(
            "Weighted score favors recall, F1-score, ROC-AUC, and lower inference time "
            "for a balanced demo recommendation."
        ),
    )


def select_best_for_customer(results: list[PredictionResult]) -> PredictionResult:
    validated_results = [
        result
        for result in results
        if result.source not in {"mock_baseline", "unavailable"} and result.status != "failed"
    ]
    return max(validated_results or results, key=lambda result: result.churn_probability)


def _global_score(metric: ModelMetrics) -> float:
    normalized_speed = max(0.0, 1 - (metric.average_inference_ms / 100))
    return (
        0.30 * metric.recall
        + 0.30 * metric.f1_score
        + 0.30 * metric.roc_auc
        + 0.10 * normalized_speed
    )
