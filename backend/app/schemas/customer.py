from pydantic import BaseModel


class Customer(BaseModel):
    customer_id: str
    age: int
    tenure_months: int
    contract_type: str
    monthly_charges: float
    total_charges: float
    internet_service: str
    payment_method: str
    support_tickets: int
    late_payments: int
