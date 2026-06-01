from pydantic import BaseModel


class PredictionRequest(BaseModel):
    customer_id: str


class PredictionResult(BaseModel):
    model_name: str
    churn_probability: float
    prediction_label: str
    confidence: float
    actual_label: int | None = None
    actual_label_name: str | None = None
    is_correct: bool | None = None
    source: str | None = None
    status: str | None = None
    message: str | None = None


class PredictionResponse(BaseModel):
    customer_id: str
    actual_label: int | None = None
    actual_label_name: str | None = None
    predictions: list[PredictionResult]
    highest_probability_model: str
    recommendation: str
