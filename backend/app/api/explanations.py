from fastapi import APIRouter

from app.services.mock_data_service import load_explanation_for_customer

router = APIRouter(tags=["explanations"])


@router.get("/explanations/{customer_id}")
def get_explanations(customer_id: str) -> dict:
    return load_explanation_for_customer(customer_id)
