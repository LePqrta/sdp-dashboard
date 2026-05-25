# TabNet Artifacts

Place TabNet live-inference files here.

## Required

```text
model/
  best_tabnet_l3_gold_v1_20260523_233256.zip

configs/
  tabnet_l3_used_feature_columns.json

metrics/
  tabnet_l3_latest_test_metrics.json
  tabnet_l3_result_card.json
  tabnet_l3_final_summary.json

explainability/
  tabnet_l3_feature_importance.csv
  tabnet_l3_feature_importance_top25.png
```

## Optional

```text
predictions/
  tabnet_l3_test_predictions.parquet
  tabnet_l3_val_predictions.parquet
  tabnet_l3_latest_test_predictions.parquet

metrics/
  tabnet_l3_target_summary.json
  tabnet_l3_trial_results.json
```

Large model files and parquet files are ignored by Git.
