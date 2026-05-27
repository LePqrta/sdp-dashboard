from app.schemas.metrics import BestModelResponse, ModelMetrics
from app.schemas.prediction import PredictionResult


def select_best_global_model(metrics: list[ModelMetrics]) -> BestModelResponse:
    scored = [(item, _global_score(item)) for item in metrics]
    best_metric, best_score = max(scored, key=lambda pair: pair[1])
    return BestModelResponse(
        model_name=best_metric.model_name,
        score=round(best_score, 4),
        reason=(
            "Weighted score favors recall, F1-score, and ROC-AUC "
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
    return (
        0.34 * (metric.recall or 0.0)
        + 0.33 * (metric.f1_score or 0.0)
        + 0.33 * (metric.roc_auc or 0.0)
    )
