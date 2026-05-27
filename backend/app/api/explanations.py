from fastapi import APIRouter

from app.schemas.explainability import CustomerExplanationResponse
from app.services.explainability_service import get_customer_explanation

router = APIRouter(tags=["explanations"])


@router.get("/explanations/{customer_id}", response_model=CustomerExplanationResponse)
def get_explanations(customer_id: str) -> CustomerExplanationResponse:
    return get_customer_explanation(customer_id)
