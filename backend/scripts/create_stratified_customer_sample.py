from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


DEFAULT_SOURCE = Path(
    r"C:\Users\lepqr\Downloads\Bitirme Projesi\Bitirme Projesi\L3\labels\l3_hybrid_gold_v3\l3_hybrid_all_enriched.parquet"
)
DEFAULT_OUTPUT = Path("app/artifacts/datasets/sample/customers_sample.parquet")


def latest_labeled_rows(df: pd.DataFrame) -> pd.DataFrame:
    labeled = df[df["l3_label"].notna()].copy()
    if labeled.empty:
        raise ValueError("No labeled rows found in l3_label.")
    labeled["cust_id"] = labeled["cust_id"].astype(str)
    return labeled.sort_values(["cust_id", "time_idx"]).groupby("cust_id", as_index=False).tail(1)


def stratified_customer_ids(latest_rows: pd.DataFrame, customer_count: int, seed: int) -> list[str]:
    label_counts = latest_rows["l3_label"].astype(int).value_counts().sort_index()
    total_customers = int(label_counts.sum())
    target_counts = (label_counts / total_customers * customer_count).round().astype(int)

    while int(target_counts.sum()) < customer_count:
        label = int(((label_counts / total_customers * customer_count) - target_counts).idxmax())
        target_counts.loc[label] += 1
    while int(target_counts.sum()) > customer_count:
        label = int(target_counts.idxmax())
        target_counts.loc[label] -= 1

    sampled_ids: list[str] = []
    for label, target_count in target_counts.items():
        candidates = latest_rows[latest_rows["l3_label"].astype(int) == int(label)]
        n = min(int(target_count), len(candidates))
        sampled = candidates.sample(n=n, random_state=seed + int(label))
        sampled_ids.extend(sampled["cust_id"].astype(str).tolist())

    return sorted(sampled_ids)


def trim_to_sampled_labeled_windows(df: pd.DataFrame, source_latest: pd.DataFrame, sample_ids: list[str]) -> pd.DataFrame:
    eval_time_idx = (
        source_latest[source_latest["cust_id"].isin(sample_ids)]
        .set_index("cust_id")["time_idx"]
        .to_dict()
    )
    sampled = df[df["cust_id"].isin(sample_ids)].copy()
    sampled["__eval_time_idx"] = sampled["cust_id"].map(eval_time_idx)
    sampled = sampled[sampled["time_idx"] <= sampled["__eval_time_idx"]].copy()
    sampled = sampled[sampled["l3_label"].notna()].copy()
    return sampled.drop(columns=["__eval_time_idx"])


def print_rate_report(name: str, latest_rows: pd.DataFrame) -> None:
    labels = latest_rows["l3_label"].astype(int)
    churn_rate = float(labels.mean())
    counts = labels.value_counts().sort_index().to_dict()
    print(f"{name} customers: {len(latest_rows):,}")
    print(f"{name} label counts: {counts}")
    print(f"{name} churn rate: {churn_rate:.4%}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a stratified customer sample from the enriched L3 parquet.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="Source enriched parquet path.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output sample parquet path.")
    parser.add_argument("--customers", type=int, default=5000, help="Number of customers to sample.")
    parser.add_argument("--split", default="test", help="Split to sample from. Use 'all' to ignore split.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.source.exists():
        raise FileNotFoundError(f"Source parquet not found: {args.source}")

    df = pd.read_parquet(args.source)
    df["cust_id"] = df["cust_id"].astype(str)
    if args.split.casefold() != "all":
        df = df[df["split"].astype(str).str.casefold() == args.split.casefold()].copy()
    if df.empty:
        raise ValueError(f"No rows available for split={args.split!r}")

    source_latest = latest_labeled_rows(df)
    sample_ids = stratified_customer_ids(source_latest, args.customers, args.seed)
    sampled = trim_to_sampled_labeled_windows(df, source_latest, sample_ids)
    sampled_latest = latest_labeled_rows(sampled)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    sampled.to_parquet(args.output, index=False)

    print(f"Output: {args.output}")
    print(f"Rows written: {len(sampled):,}")
    print(f"Unique customers written: {sampled['cust_id'].nunique():,}")
    print(f"Split: {args.split}")
    print()
    print_rate_report("Source", source_latest)
    print()
    print_rate_report("Sample", sampled_latest)
    print()
    print(f"Absolute churn-rate difference: {abs(source_latest['l3_label'].astype(int).mean() - sampled_latest['l3_label'].astype(int).mean()):.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
