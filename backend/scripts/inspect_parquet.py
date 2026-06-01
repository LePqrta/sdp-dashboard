from __future__ import annotations

import argparse
from pathlib import Path

import pyarrow.compute as pc
import pyarrow.parquet as pq


DEFAULT_COLUMNS = [
    "cust_id",
    "split",
    "month_start",
    "time_idx",
    "txn_count",
    "spend",
    "tenure_months",
    "l3_label",
    "l3_component_category",
]


def existing_columns(parquet_file: pq.ParquetFile, requested_columns: list[str]) -> list[str]:
    available = set(parquet_file.schema.names)
    return [column for column in requested_columns if column in available]


def print_metadata(path: Path, parquet_file: pq.ParquetFile) -> None:
    print(f"Path: {path}")
    print(f"Exists: {path.exists()}")
    print(f"Size MB: {path.stat().st_size / (1024 * 1024):.2f}")
    print(f"Rows: {parquet_file.metadata.num_rows:,}")
    print(f"Columns: {parquet_file.metadata.num_columns}")
    print(f"Row groups: {parquet_file.metadata.num_row_groups}")
    print()
    print("Columns:")
    for column in parquet_file.schema.names:
        print(f"  - {column}")


def print_preview(parquet_file: pq.ParquetFile, columns: list[str], rows: int) -> None:
    print()
    print(f"Preview: first {rows} rows")
    preview = parquet_file.read_row_group(0, columns=columns).slice(0, rows)
    print(preview.to_pandas().to_string(index=False))


def print_split_counts(path: Path) -> None:
    dataset = pq.read_table(path, columns=["split"])
    counts = pc.value_counts(dataset["split"]).to_pylist()
    print()
    print("Split counts:")
    for item in counts:
        print(f"  {item['values']}: {item['counts']:,}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect a parquet file without loading every column into memory.")
    parser.add_argument("path", help="Path to the parquet file.")
    parser.add_argument("--rows", type=int, default=5, help="Number of preview rows to print.")
    parser.add_argument(
        "--columns",
        nargs="*",
        default=DEFAULT_COLUMNS,
        help="Columns to preview. Missing columns are skipped.",
    )
    parser.add_argument("--split-counts", action="store_true", help="Print counts for the split column.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    path = Path(args.path)

    if not path.exists():
        print(f"File not found: {path}")
        return 1

    parquet_file = pq.ParquetFile(path)
    preview_columns = existing_columns(parquet_file, args.columns)
    if not preview_columns:
        print("None of the requested preview columns exist in the parquet file.")
        return 1

    print_metadata(path, parquet_file)
    print_preview(parquet_file, preview_columns, max(1, args.rows))

    if args.split_counts:
        if "split" not in parquet_file.schema.names:
            print()
            print("No split column found.")
        else:
            print_split_counts(path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
