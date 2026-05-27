from pydantic import BaseModel


class ModelMetrics(BaseModel):
    model_name: str
    accuracy: float | None
    precision: float | None
    recall: float | None
    f1_score: float | None
    roc_auc: float | None
    pr_auc: float | None
    model_size_mb: float | None
    threshold: float | None


class BestModelResponse(BaseModel):
    model_name: str
    score: float
    reason: str
