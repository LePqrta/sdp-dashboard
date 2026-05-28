from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from explainability_smoke_utils import BACKEND_DIR
from smoke_tabnet_explainability import run as run_tabnet_explainability
from smoke_tft_explainability import run as run_tft_explainability


warnings.filterwarnings("ignore", message="Device used : cpu")
warnings.filterwarnings("ignore", message="Min encoder length.*")
warnings.filterwarnings("ignore", message="Trying to unpickle estimator.*")
warnings.filterwarnings("ignore", message="Attribute 'loss'.*")
warnings.filterwarnings("ignore", message="Attribute 'logging_metrics'.*")
warnings.filterwarnings("ignore", message="`isinstance\\(treespec, LeafSpec\\)` is deprecated.*")
warnings.filterwarnings("ignore", message="The 'predict_dataloader' does not have many workers.*")

DEFAULT_OUTPUT_PATH = (
    BACKEND_DIR
    / "app"
    / "artifacts"
    / "models"
    / "explainability"
    / "customer_explanations.json"
)

ModelChoice = Literal["both", "tabnet", "tft"]


def _customer_ids(limit: int | None, customer_id: str | None) -> tuple[list[str], int]:
    from app.services.artifact_data_service import load_demo_customer_rows

    rows = load_demo_customer_rows().sort_values("cust_id")
    ids = rows["cust_id"].astype(str).drop_duplicates().tolist()
    if customer_id:
        return [str(customer_id)], len(ids)
    if limit is not None:
        return ids[:limit], len(ids)
    return ids, len(ids)


def _models_for_choice(choice: ModelChoice) -> list[str]:
    if choice == "both":
        return ["tabnet", "tft"]
    return [choice]


def _run_model(model: str, customer_id: str, top_k: int) -> dict[str, Any]:
    if model == "tabnet":
        return run_tabnet_explainability(customer_id, top_k)
    if model == "tft":
        return run_tft_explainability(customer_id, top_k)
    raise ValueError(f"Unsupported model: {model}")


def _compact_result(result: dict[str, Any]) -> dict[str, Any]:
    probability = result.get("churn_probability")
    if probability is None:
        probability = result.get("churn_probability_raw")

    return {
        "model": result.get("model"),
        "prediction_label": _prediction_label(probability),
        "churn_probability": _round_float(probability),
        "top_features": result.get("top_features", []),
        "explanation_type": result.get("explanation_type", "unknown"),
        "notes": [str(item) for item in result.get("notes", [])],
        "warnings": _warnings_for_result(result),
    }


def _failure_record(customer_id: str, model: str, exc_or_error: Any) -> dict[str, str]:
    return {
        "customer_id": str(customer_id),
        "model": "TabNet" if model == "tabnet" else "TFT",
        "error": str(exc_or_error),
    }


def _warnings_for_result(result: dict[str, Any]) -> list[str]:
    result_warnings = [str(item) for item in result.get("warnings", [])]
    if result.get("status") not in {"passed", "partial"}:
        result_warnings.append(str(result.get("error", "Explanation generation failed.")))
    return result_warnings


def _prediction_label(probability: Any) -> str | None:
    if probability is None:
        return None
    return "Churn" if float(probability) >= 0.5 else "Not Churn"


def _round_float(value: Any) -> float | None:
    if value is None:
        return None
    return round(float(value), 8)


def _artifact_version() -> dict[str, str]:
    from app.services.artifact_data_service import TABNET_MODEL_PATH, TFT_CHECKPOINT_PATH

    return {
        "tabnet": TABNET_MODEL_PATH.name,
        "tft": TFT_CHECKPOINT_PATH.name,
    }


def _write_output(path: Path, payload: dict[str, Any]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path.stat().st_size


def generate(
    *,
    limit: int | None,
    customer_id: str | None,
    top_k: int,
    model: ModelChoice,
    output: Path,
) -> dict[str, Any]:
    if limit is not None and limit <= 0:
        raise ValueError("--limit must be greater than 0")
    if top_k <= 0:
        raise ValueError("--top-k must be greater than 0")

    selected_ids, total_customers = _customer_ids(limit, customer_id)
    model_names = _models_for_choice(model)
    started = time.perf_counter()

    customers: dict[str, dict[str, Any]] = {}
    failures: list[dict[str, str]] = []

    for index, selected_customer_id in enumerate(selected_ids, start=1):
        print(f"[{index}/{len(selected_ids)}] Explaining customer {selected_customer_id} ({', '.join(model_names)})")
        customer_entry = {
            "customer_id": selected_customer_id,
            "models": [],
            "warnings": [],
        }
        for model_name in model_names:
            try:
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    result = _run_model(model_name, selected_customer_id, top_k)
                if result.get("status") not in {"passed", "partial"}:
                    error = result.get("error", "Unknown explanation failure.")
                    failures.append(_failure_record(selected_customer_id, model_name, error))
                    customer_entry["warnings"].append(
                        f"{_display_model_name(model_name)} explanation unavailable: {error}"
                    )
                    continue
                customer_entry["models"].append(_compact_result(result))
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                failures.append(_failure_record(selected_customer_id, model_name, error))
                customer_entry["warnings"].append(
                    f"{_display_model_name(model_name)} explanation unavailable: {error}"
                )

        customers[selected_customer_id] = customer_entry

    elapsed = time.perf_counter() - started
    counts = _eligibility_counts(customers)
    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    payload = {
        "manifest": {
            "generated_at": generated_at,
            "total_customers": total_customers,
            "processed_customers": len(selected_ids),
            "customers_with_both_models": counts["both"],
            "customers_with_tabnet_only": counts["tabnet_only"],
            "customers_with_tft_only": counts["tft_only"],
            "failed_customers": counts["failed"],
            "top_k": top_k,
            "model": model,
            "source": "native TabNet explain(X) and native TFT interpret_output over representative sample parquet",
            "artifact_version": _artifact_version(),
            "notes": [
                "Only compact normalized top-k explanations are stored.",
                "Raw TFT attention tensors and raw TabNet masks are not stored.",
                "TFT sequence-ineligible customers keep available model explanations without fake fallback.",
            ],
        },
        "customers": customers,
        "failures": failures,
    }
    output_size = _write_output(output, payload)

    return {
        "output": str(output),
        "output_size_bytes": output_size,
        "total_runtime_seconds": round(elapsed, 3),
        "average_seconds_per_customer": round(elapsed / max(len(selected_ids), 1), 3),
        "total_sample_customers": total_customers,
        "processed_customers": len(selected_ids),
        "customers_with_both_models": counts["both"],
        "customers_with_tabnet_only": counts["tabnet_only"],
        "customers_with_tft_only": counts["tft_only"],
        "failed_customers": counts["failed"],
        "model_failures": len(failures),
        "failure_reasons": failures[:10],
    }


def _display_model_name(model: str) -> str:
    return "TabNet" if model == "tabnet" else "TFT"


def _eligibility_counts(customers: dict[str, dict[str, Any]]) -> dict[str, int]:
    counts = {"both": 0, "tabnet_only": 0, "tft_only": 0, "failed": 0}
    for customer in customers.values():
        model_names = {model.get("model") for model in customer.get("models", [])}
        has_tabnet = "TabNet" in model_names
        has_tft = "TFT" in model_names
        if has_tabnet and has_tft:
            counts["both"] += 1
        elif has_tabnet:
            counts["tabnet_only"] += 1
        elif has_tft:
            counts["tft_only"] += 1
        else:
            counts["failed"] += 1
    return counts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate compact real per-customer explanations for the demo dashboard."
    )
    parser.add_argument("--limit", type=int, help="Optional number of sample customers to generate.")
    parser.add_argument("--customer-id", help="Optional single customer ID to generate.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of top features to store per model.")
    parser.add_argument(
        "--model",
        choices=("both", "tabnet", "tft"),
        default="both",
        help="Which model explanations to generate.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Path for compact explanation JSON output.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = generate(
        limit=args.limit,
        customer_id=args.customer_id,
        top_k=args.top_k,
        model=args.model,
        output=args.output,
    )
    print("\nGeneration report")
    print("=================")
    print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
