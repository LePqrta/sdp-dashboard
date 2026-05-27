from fastapi import APIRouter, Query

from app.schemas.customer import Customer, CustomerPage
from app.services.mock_data_service import (
    DEFAULT_CUSTOMER_DIRECTION,
    DEFAULT_CUSTOMER_SORT,
    CustomerFilterKey,
    CustomerSortDirection,
    CustomerSortKey,
    find_customer,
    load_customer_page,
    load_customers,
    random_customer,
)

router = APIRouter(tags=["customers"])


@router.get("/customers", response_model=list[Customer])
def get_customers() -> list[Customer]:
    return load_customers()


@router.get("/customers/page", response_model=CustomerPage)
def get_customer_page(
    offset: int = 0,
    limit: int = 25,
    q: str | None = None,
    filter: CustomerFilterKey | None = Query(default=None),
    sort: CustomerSortKey = DEFAULT_CUSTOMER_SORT,
    direction: CustomerSortDirection = DEFAULT_CUSTOMER_DIRECTION,
) -> CustomerPage:
    return load_customer_page(
        offset=offset,
        limit=limit,
        q=q,
        filter=filter,
        sort=sort,
        direction=direction,
    )


@router.get("/customers/random", response_model=Customer)
def get_random_customer() -> Customer:
    return random_customer()


@router.get("/customers/{customer_id}", response_model=Customer)
def get_customer(customer_id: str) -> Customer:
    return find_customer(customer_id)
