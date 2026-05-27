from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
import time
import warnings
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
    / "benchmark_customer_explanations.json"
)

ModelChoice = Literal["both", "tabnet", "tft"]


def _customer_ids(limit: int) -> tuple[list[str], int]:
    from app.services.artifact_data_service import load_demo_customer_rows

    rows = load_demo_customer_rows().sort_values("cust_id")
    ids = rows["cust_id"].astype(str).drop_duplicates().tolist()
    return ids[:limit], len(ids)


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

    compact = {
        "customer_id": result.get("customer_id"),
        "model": result.get("model"),
        "prediction_label": _prediction_label(probability),
        "churn_probability": _round_float(probability),
        "top_features": result.get("top_features", []),
        "explanation_type": result.get("explanation_type"),
        "warnings": _warnings_for_result(result),
    }
    return compact


def _failure_result(customer_id: str, model: str, exc: Exception) -> dict[str, Any]:
    return {
        "customer_id": customer_id,
        "model": "TabNet" if model == "tabnet" else "TFT",
        "prediction_label": None,
        "churn_probability": None,
        "top_features": [],
        "explanation_type": "failed",
        "warnings": [f"{type(exc).__name__}: {exc}"],
    }


def _warnings_for_result(result: dict[str, Any]) -> list[str]:
    warnings = []
    if result.get("status") not in {"passed", "partial"}:
        warnings.append(str(result.get("error", "Explanation generation failed.")))
    warnings.extend(str(item) for item in result.get("notes", []))
    return warnings


def _prediction_label(probability: Any) -> str | None:
    if probability is None:
        return None
    return "Churn" if float(probability) >= 0.5 else "Not Churn"


def _round_float(value: Any) -> float | None:
    if value is None:
        return None
    return round(float(value), 8)


def _write_output(path: Path, payload: dict[str, Any]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path.stat().st_size


def _format_seconds(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.2f}s"
    return f"{seconds / 60:.2f}m"


def benchmark(*, limit: int, top_k: int, model: ModelChoice, output: Path) -> dict[str, Any]:
    if limit <= 0:
        raise ValueError("--limit must be greater than 0")
    if top_k <= 0:
        raise ValueError("--top-k must be greater than 0")

    selected_ids, total_customers = _customer_ids(limit)
    model_names = _models_for_choice(model)
    started = time.perf_counter()
    results: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []

    for index, customer_id in enumerate(selected_ids, start=1):
        print(f"[{index}/{len(selected_ids)}] Explaining customer {customer_id} ({', '.join(model_names)})")
        for model_name in model_names:
            try:
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    result = _run_model(model_name, customer_id, top_k)
                if result.get("status") not in {"passed", "partial"}:
                    failures.append(
                        {
                            "customer_id": customer_id,
                            "model": model_name,
                            "error": result.get("error", "Unknown explanation failure."),
                        }
                    )
                results.append(_compact_result(result))
            except Exception as exc:
                failures.append(
                    {
                        "customer_id": customer_id,
                        "model": model_name,
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )
                results.append(_failure_result(customer_id, model_name, exc))

    elapsed = time.perf_counter() - started
    requested_pairs = len(selected_ids) * len(model_names)
    successful_pairs = requested_pairs - len(failures)
    average_seconds_per_customer = elapsed / max(len(selected_ids), 1)
    average_seconds_per_pair = elapsed / max(requested_pairs, 1)
    estimated_full_seconds = average_seconds_per_customer * total_customers

    payload = {
        "metadata": {
            "limit": limit,
            "top_k": top_k,
            "model": model,
            "selected_customers": len(selected_ids),
            "total_sample_customers": total_customers,
            "direction_policy": "unknown",
            "notes": [
                "Only compact normalized top-k explanations are stored.",
                "Raw TFT attention tensors and raw TabNet masks are not stored.",
            ],
        },
        "results": results,
        "failures": failures,
    }
    output_size_bytes = _write_output(output, payload)
    estimated_full_size_bytes = int(output_size_bytes * (total_customers / max(len(selected_ids), 1)))

    report = {
        "output": str(output),
        "output_size_bytes": output_size_bytes,
        "estimated_full_output_size_bytes": estimated_full_size_bytes,
        "total_runtime_seconds": round(elapsed, 3),
        "average_seconds_per_customer": round(average_seconds_per_customer, 3),
        "average_seconds_per_model_explanation": round(average_seconds_per_pair, 3),
        "estimated_full_generation_seconds": round(estimated_full_seconds, 3),
        "estimated_full_generation_human": _format_seconds(estimated_full_seconds),
        "selected_customers": len(selected_ids),
        "total_sample_customers": total_customers,
        "requested_model_explanations": requested_pairs,
        "successful_model_explanations": successful_pairs,
        "failed_model_explanations": len(failures),
        "failure_reasons": failures[:10],
    }
    payload["benchmark_report"] = report
    output_size_bytes = _write_output(output, payload)
    report["output_size_bytes"] = output_size_bytes
    report["estimated_full_output_size_bytes"] = int(
        output_size_bytes * (total_customers / max(len(selected_ids), 1))
    )
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark compact per-customer explanation generation for TabNet and TFT."
    )
    parser.add_argument("--limit", type=int, default=10, help="Number of sample customers to benchmark.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of top features to store per model.")
    parser.add_argument(
        "--model",
        choices=("both", "tabnet", "tft"),
        default="both",
        help="Which model explanations to benchmark.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Path for compact benchmark JSON output.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = benchmark(
        limit=args.limit,
        top_k=args.top_k,
        model=args.model,
        output=args.output,
    )

    print("\nBenchmark report")
    print("================")
    print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
