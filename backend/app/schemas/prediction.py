from pydantic import BaseModel


class PredictionRequest(BaseModel):
    customer_id: str


class PredictionResult(BaseModel):
    model_name: str
    churn_probability: float
    prediction_label: str
    confidence: float
    inference_ms: float


class PredictionResponse(BaseModel):
    customer_id: str
    predictions: list[PredictionResult]
    highest_probability_model: str
    recommendation: str
