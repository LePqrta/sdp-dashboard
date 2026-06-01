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
    split: str | None = None
    latest_time_idx: int | None = None
    actual_label: int | None = None
    actual_label_name: str | None = None
    history_months_available: int | None = None
    txn_count_3m: float | None = None
    spend_3m: float | None = None
    avg_txn_amt_3m: float | None = None
    total_transaction_count: float | None = None
    total_lifetime_spend: float | None = None
    days_since_last_txn: float | None = None


class CustomerPage(BaseModel):
    items: list[Customer]
    total: int
    limit: int
    offset: int
