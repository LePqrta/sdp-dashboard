from pydantic import BaseModel


class ModelMetrics(BaseModel):
    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float
    pr_auc: float
    model_size_mb: float
    average_inference_ms: float
    threshold: float


class BestModelResponse(BaseModel):
    model_name: str
    score: float
    reason: str
