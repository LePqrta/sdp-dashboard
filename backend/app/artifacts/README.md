# Backend Artifacts

This folder is for local model and inference artifacts. Large files are intentionally ignored by Git.

## Structure

```text
artifacts/
  models/
    tabnet/
      README.md
      model/
      configs/
      metrics/
      explainability/
      predictions/
    tft/
      README.md
      checkpoints/
      configs/
      metrics/
      explainability/
      predictions/
      calibration/
  datasets/
    sample/
      README.md
```

Use `backend/app/data/` only for small mock JSON used by the current MVP. Put real model files, checkpoints, calibrators, and parquet prediction outputs here.
