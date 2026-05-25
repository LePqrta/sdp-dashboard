from pydantic import BaseModel


class PredictionRequest(BaseModel):
    customer_id: str


class PredictionResult(BaseModel):
    model_name: str
    churn_probability: float
    prediction_label: str
    confidence: float
    inference_ms: float
    source: str | None = None
    status: str | None = None
    message: str | None = None


class PredictionResponse(BaseModel):
    customer_id: str
    predictions: list[PredictionResult]
    highest_probability_model: str
    recommendation: str
