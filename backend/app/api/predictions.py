from fastapi import APIRouter

from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.prediction_service import predict_for_customer

router = APIRouter(tags=["predictions"])


@router.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest) -> PredictionResponse:
    return predict_for_customer(request.customer_id)
