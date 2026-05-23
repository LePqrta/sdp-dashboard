from fastapi import APIRouter

from app.schemas.metrics import BestModelResponse, ModelMetrics
from app.services.mock_data_service import load_model_metrics
from app.services.model_selection_service import select_best_global_model

router = APIRouter(tags=["metrics"])


@router.get("/metrics", response_model=list[ModelMetrics])
def get_metrics() -> list[ModelMetrics]:
    return load_model_metrics()


@router.get("/best-model", response_model=BestModelResponse)
def get_best_model() -> BestModelResponse:
    metrics = load_model_metrics()
    return select_best_global_model(metrics)
