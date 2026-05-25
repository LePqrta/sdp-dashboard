from __future__ import annotations

import argparse
import json
import sys
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

ARTIFACTS_DIR = BACKEND_DIR / "app" / "artifacts"
SAMPLE_PATH = ARTIFACTS_DIR / "datasets" / "sample" / "customers_sample.parquet"

TABNET_MODEL_PATH = (
    ARTIFACTS_DIR
    / "models"
    / "tabnet"
    / "model"
    / "best_tabnet_l3_gold_v1_20260523_233256.zip"
)
TABNET_FEATURES_PATH = (
    ARTIFACTS_DIR / "models" / "tabnet" / "configs" / "tabnet_l3_used_feature_columns.json"
)
TABNET_FALLBACK_PATH = (
    ARTIFACTS_DIR / "models" / "tabnet" / "predictions" / "tabnet_l3_latest_test_predictions.parquet"
)

TFT_CHECKPOINT_PATH = (
    ARTIFACTS_DIR
    / "models"
    / "tft"
    / "checkpoints"
    / "tft-l3-gold-v1-epoch=04-val_loss=0.6388.ckpt"
)
TFT_CONFIG_PATH = ARTIFACTS_DIR / "models" / "tft" / "configs" / "tft_l3_feature_config.json"
TFT_SUMMARY_PATH = ARTIFACTS_DIR / "models" / "tft" / "metrics" / "tft_l3_final_summary.json"
TFT_CALIBRATOR_PATH = ARTIFACTS_DIR / "models" / "tft" / "calibration" / "isotonic_calibrator.pkl"
TFT_FALLBACK_PATH = ARTIFACTS_DIR / "models" / "tft" / "predictions" / "latest_test_predictions.parquet"


@dataclass
class CheckResult:
    name: str
    status: str
    details: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _import(name: str) -> Any:
    __import__(name)
    return sys.modules[name]


def _result(name: str, status: str, **details: Any) -> CheckResult:
    return CheckResult(name=name, status=status, details=details)


def _failed(name: str, exc: BaseException, **details: Any) -> CheckResult:
    return CheckResult(name=name, status="failed", details=details, error=f"{type(exc).__name__}: {exc}")


def validate_artifacts() -> CheckResult:
    required_paths = [
        SAMPLE_PATH,
        TABNET_MODEL_PATH,
        TABNET_FEATURES_PATH,
        TABNET_FALLBACK_PATH,
        TFT_CHECKPOINT_PATH,
        TFT_CONFIG_PATH,
        TFT_SUMMARY_PATH,
        TFT_CALIBRATOR_PATH,
        TFT_FALLBACK_PATH,
    ]
    missing = [str(path.relative_to(BACKEND_DIR)) for path in required_paths if not path.exists()]
    if missing:
        return _result("artifact_presence", "failed", missing=missing)

    with zipfile.ZipFile(TABNET_MODEL_PATH) as zip_file:
        tabnet_zip_members = sorted(zip_file.namelist())

    return _result(
        "artifact_presence",
        "passed",
        tabnet_zip_members=tabnet_zip_members,
        sample_mb=round(SAMPLE_PATH.stat().st_size / (1024 * 1024), 2),
        tabnet_zip_kb=round(TABNET_MODEL_PATH.stat().st_size / 1024, 2),
        tft_checkpoint_mb=round(TFT_CHECKPOINT_PATH.stat().st_size / (1024 * 1024), 2),
    )


def load_sample_and_configs() -> tuple[Any, dict[str, Any], dict[str, Any]]:
    pd = _import("pandas")
    sample_df = pd.read_parquet(SAMPLE_PATH)
    tabnet_config = _load_json(TABNET_FEATURES_PATH)
    tft_config = _load_json(TFT_CONFIG_PATH)
    return sample_df, tabnet_config, tft_config


def pick_customer_ids(sample_df: Any, explicit_customer_ids: list[str] | None) -> list[str]:
    if explicit_customer_ids:
        return explicit_customer_ids[:3]
    unique_ids = sample_df["cust_id"].drop_duplicates().astype(str).head(3).tolist()
    return unique_ids


def validate_sample_data(customer_ids: list[str] | None = None) -> tuple[CheckResult, Any, list[str]]:
    try:
        sample_df, tabnet_config, tft_config = load_sample_and_configs()
        selected_ids = pick_customer_ids(sample_df, customer_ids)

        sample_cols = set(sample_df.columns)
        tabnet_missing = [col for col in tabnet_config["feature_cols"] if col not in sample_cols]
        tft_missing = [col for col in tft_config["time_varying_known_reals"] if col not in sample_cols]

        per_customer = {}
        for customer_id in selected_ids:
            customer_df = sample_df[sample_df["cust_id"].astype(str) == str(customer_id)]
            per_customer[customer_id] = {
                "rows": int(len(customer_df)),
                "latest_time_idx": None if customer_df.empty else int(customer_df["time_idx"].max()),
                "has_latest_row": not customer_df.empty,
            }

        status = "passed" if not tabnet_missing and not tft_missing and all(v["rows"] > 0 for v in per_customer.values()) else "failed"
        return (
            _result(
                "sample_data",
                status,
                rows=int(len(sample_df)),
                unique_customers=int(sample_df["cust_id"].nunique()),
                columns=len(sample_df.columns),
                selected_customer_ids=selected_ids,
                tabnet_missing_features=tabnet_missing,
                tft_missing_features=tft_missing,
                per_customer=per_customer,
            ),
            sample_df,
            selected_ids,
        )
    except BaseException as exc:
        return _failed("sample_data", exc), None, []


def validate_tabnet_live(sample_df: Any, customer_ids: list[str]) -> CheckResult:
    started = time.perf_counter()
    try:
        np = _import("numpy")
        tab_model = _import("pytorch_tabnet.tab_model")
        TabNetClassifier = tab_model.TabNetClassifier
        feature_cols = _load_json(TABNET_FEATURES_PATH)["feature_cols"]

        model = TabNetClassifier()
        model.load_model(str(TABNET_MODEL_PATH))

        predictions = {}
        for customer_id in customer_ids:
            customer_df = sample_df[sample_df["cust_id"].astype(str) == str(customer_id)]
            latest_row = customer_df.sort_values("time_idx").tail(1)
            x = latest_row[feature_cols].astype("float32").to_numpy()
            proba = model.predict_proba(x)
            churn_probability = float(proba[0][1])
            if not np.isfinite(churn_probability) or not 0 <= churn_probability <= 1:
                raise ValueError(f"Invalid probability for {customer_id}: {churn_probability}")
            predictions[customer_id] = churn_probability

        return _result(
            "tabnet_live_inference",
            "passed",
            elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
            predictions=predictions,
        )
    except BaseException as exc:
        return _failed("tabnet_live_inference", exc, elapsed_ms=round((time.perf_counter() - started) * 1000, 2))


def validate_tabnet_fallback(customer_ids: list[str]) -> CheckResult:
    try:
        pd = _import("pandas")
        fallback_df = pd.read_parquet(TABNET_FALLBACK_PATH)
        predictions = {}
        for customer_id in customer_ids:
            rows = fallback_df[fallback_df["cust_id"].astype(str) == str(customer_id)]
            if rows.empty:
                raise ValueError(f"No TabNet fallback row for {customer_id}")
            probability = float(rows.iloc[0]["prob_churn"])
            if not 0 <= probability <= 1:
                raise ValueError(f"Invalid TabNet fallback probability for {customer_id}: {probability}")
            predictions[customer_id] = probability
        return _result("tabnet_cached_fallback", "passed", predictions=predictions)
    except BaseException as exc:
        return _failed("tabnet_cached_fallback", exc)


def validate_tft_live(sample_df: Any, customer_ids: list[str]) -> CheckResult:
    started = time.perf_counter()
    try:
        summary = _load_json(TFT_SUMMARY_PATH)
        model_config = summary.get("model_config", {})
        required_dataset_fields = [
            "max_encoder_length",
            "max_prediction_length",
            "output_size",
            "loss",
        ]
        missing_model_config = [field for field in required_dataset_fields if field not in model_config]
        if missing_model_config:
            raise ValueError(f"TFT summary missing model_config fields: {missing_model_config}")

        customer_panel_lengths = {}
        for customer_id in customer_ids:
            customer_df = sample_df[sample_df["cust_id"].astype(str) == str(customer_id)]
            if customer_df.empty:
                raise ValueError(f"No TFT panel rows for {customer_id}")
            customer_panel_lengths[customer_id] = int(len(customer_df))

        from app.services.artifact_prediction_service import predict_tft

        predictions = {}
        sources = {}
        for customer_id in customer_ids:
            result = predict_tft(customer_id)
            if result.source != "live_model":
                raise ValueError(f"TFT live inference fell back for {customer_id}: {result.message}")
            predictions[customer_id] = result.churn_probability
            sources[customer_id] = result.source

        return _result(
            "tft_live_inference",
            "passed",
            elapsed_ms=round((time.perf_counter() - started) * 1000, 2),
            predictions=predictions,
            sources=sources,
            model_config={key: model_config.get(key) for key in required_dataset_fields},
            customer_panel_lengths=customer_panel_lengths,
        )
    except BaseException as exc:
        return _failed("tft_live_inference", exc, elapsed_ms=round((time.perf_counter() - started) * 1000, 2))


def validate_tft_fallback(customer_ids: list[str]) -> CheckResult:
    try:
        pd = _import("pandas")
        fallback_df = pd.read_parquet(TFT_FALLBACK_PATH)
        predictions = {}
        for customer_id in customer_ids:
            rows = fallback_df[fallback_df["cust_id"].astype(str) == str(customer_id)]
            if rows.empty:
                raise ValueError(f"No TFT fallback row for {customer_id}")
            row = rows.sort_values("eval_time_idx").tail(1).iloc[0]
            probability = float(row.get("score_calibrated", row.get("score_raw")))
            if not 0 <= probability <= 1:
                raise ValueError(f"Invalid TFT fallback probability for {customer_id}: {probability}")
            predictions[customer_id] = probability
        return _result("tft_cached_fallback", "passed", predictions=predictions)
    except BaseException as exc:
        return _failed("tft_cached_fallback", exc)


def compare_live_to_fallback(live: CheckResult, fallback: CheckResult, name: str) -> CheckResult:
    if live.status != "passed" or fallback.status != "passed":
        return _result(
            f"{name}_live_vs_fallback",
            "skipped",
            reason="Requires both live inference and cached fallback to pass.",
            live_status=live.status,
            fallback_status=fallback.status,
        )

    live_predictions = live.details["predictions"]
    fallback_predictions = fallback.details["predictions"]
    diffs = {
        customer_id: round(abs(live_predictions[customer_id] - fallback_predictions[customer_id]), 6)
        for customer_id in live_predictions
    }
    return _result(f"{name}_live_vs_fallback", "passed", absolute_differences=diffs)


def run_validation(customer_ids: list[str] | None) -> list[CheckResult]:
    results: list[CheckResult] = []
    results.append(validate_artifacts())

    sample_result, sample_df, selected_ids = validate_sample_data(customer_ids)
    results.append(sample_result)

    if sample_df is None or not selected_ids:
        return results

    tabnet_live = validate_tabnet_live(sample_df, selected_ids)
    tabnet_fallback = validate_tabnet_fallback(selected_ids)
    tft_live = validate_tft_live(sample_df, selected_ids)
    tft_fallback = validate_tft_fallback(selected_ids)

    results.extend(
        [
            tabnet_live,
            tabnet_fallback,
            compare_live_to_fallback(tabnet_live, tabnet_fallback, "tabnet"),
            tft_live,
            tft_fallback,
            compare_live_to_fallback(tft_live, tft_fallback, "tft"),
        ]
    )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate TabNet/TFT artifacts before API integration.")
    parser.add_argument("--customer-id", action="append", dest="customer_ids", help="Customer ID to validate. Provide up to 3.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    results = run_validation(args.customer_ids)
    payload = {
        "python": sys.version,
        "backend_dir": str(BACKEND_DIR),
        "results": [result.__dict__ for result in results],
    }

    if args.json:
        print(json.dumps(payload, indent=2, default=str))
    else:
        print(f"Python: {sys.version.split()[0]}")
        for result in results:
            icon = {"passed": "PASS", "failed": "FAIL", "blocked": "BLOCKED", "skipped": "SKIP"}.get(result.status, result.status.upper())
            print(f"\n[{icon}] {result.name}")
            if result.error:
                print(f"  error: {result.error}")
            for key, value in result.details.items():
                print(f"  {key}: {value}")

    failing_statuses = {"failed"}
    return 1 if any(result.status in failing_statuses for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
