# Backend

FastAPI backend for the churn prediction model comparison dashboard.

## Run Locally

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Endpoints

- `GET /metrics` - static metrics for TFT and TabNet
- `GET /customers` - sample demo customers
- `GET /customers/random` - one random sample customer
- `POST /predict` - live TFT and TabNet predictions for a customer
- `GET /explanations/{customer_id}` - mock SHAP-style feature contributions
- `GET /best-model` - best global model using weighted scoring

## Real Model Integration

Add model loading and inference in `app/services/prediction_service.py`. Keep large datasets out of the API runtime path; use a curated sample dataset for demos and lightweight customer lookup.

Place real TabNet and TFT artifacts under `app/artifacts/`. See `app/artifacts/README.md` for the folder map.
