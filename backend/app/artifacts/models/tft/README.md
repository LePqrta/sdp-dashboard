# TFT Artifacts

Place TFT live-inference files here.

## Required

```text
checkpoints/
  tft-l3-gold-v1-epoch=04-val_loss=0.6388.ckpt

configs/
  tft_l3_feature_config.json
  tft_interpretation_keys.json

calibration/
  isotonic_calibrator.pkl

metrics/
  tft_l3_final_summary.json
  tft_l3_result_card.json
```

## Optional

```text
predictions/
  latest_test_predictions.parquet
  latest_val_predictions.parquet
  anchor_test_predictions.parquet
  anchor_val_predictions.parquet
```

Large checkpoint, pickle, and parquet files are ignored by Git.
