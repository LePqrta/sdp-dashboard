from fastapi import APIRouter

from app.schemas.customer import Customer
from app.services.mock_data_service import load_customers, random_customer

router = APIRouter(tags=["customers"])


@router.get("/customers", response_model=list[Customer])
def get_customers() -> list[Customer]:
    return load_customers()


@router.get("/customers/random", response_model=Customer)
def get_random_customer() -> Customer:
    return random_customer()
