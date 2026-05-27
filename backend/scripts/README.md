# Backend Validation Scripts

## Model artifact validation

Use this before integrating real model inference into FastAPI.

Recommended Python runtime:

```bash
py -3.11 -m venv backend\.venv311
backend\.venv311\Scripts\python -m pip install -r backend\requirements-ml-validation.txt
backend\.venv311\Scripts\python backend\scripts\validate_model_artifacts.py
```

The script validates:

- required artifact files
- `customers_sample.parquet` schema
- TabNet live `predict_proba`
- TabNet cached fallback parquet
- TFT dependency/config/calibrator readiness
- TFT cached fallback parquet

TFT live inference requires exact `TimeSeriesDataSet` reconstruction and may remain blocked until the training dataset construction code is available.

## Dynamic explainability smoke checks

These scripts validate whether local per-customer explanation signals can be produced from the existing artifacts. They do not change the FastAPI explanation endpoint and do not generate production explanation JSON.

```bash
backend\.venv\Scripts\python backend\scripts\smoke_tabnet_explainability.py --customer-id 293243
backend\.venv\Scripts\python backend\scripts\smoke_tft_explainability.py --customer-id 293243
```

Both scripts print normalized top features with `direction: "unknown"` because native TabNet masks and TFT interpretation values are importance signals, not signed churn contributions.

## Explainability precompute benchmark

Use this before generating a full per-customer explanation artifact.

```bash
backend\.venv\Scripts\python backend\scripts\benchmark_explainability_generation.py --limit 10 --top-k 5
backend\.venv\Scripts\python backend\scripts\benchmark_explainability_generation.py --limit 50 --top-k 5
```

The benchmark writes compact top-k explanation output to `backend/app/artifacts/models/explainability/benchmark_customer_explanations.json` by default. It does not store raw TFT attention tensors or raw TabNet masks.

## Demo explanation artifact generation

Use this to generate the production/demo artifact consumed by `GET /explanations/{customer_id}`.

```bash
backend\.venv\Scripts\python backend\scripts\generate_customer_explanations.py --top-k 5
```

The script writes compact top-k explanation output to `backend/app/artifacts/models/explainability/customer_explanations.json` by default. Customers that are TFT sequence-ineligible keep their available TabNet explanation and a warning; no global feature importance or fake TFT fallback is written.

For live demo or deployment, `backend/app/artifacts/models/explainability/customer_explanations.json` must be present with the backend files. If the artifact is missing, `GET /explanations/{customer_id}` returns HTTP 503 with regeneration guidance. Regenerate it with `backend\.venv\Scripts\python backend\scripts\generate_customer_explanations.py --top-k 5`.
