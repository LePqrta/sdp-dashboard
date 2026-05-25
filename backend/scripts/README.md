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
