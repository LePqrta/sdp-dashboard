from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "http://localhost:8000"
PAGE_PATH = "/customers/page"


@dataclass
class ApiResponse:
    status: int
    data: Any
    raw: str
    url: str


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


class SmokeFailure(Exception):
    pass


def build_url(base_url: str, params: dict[str, Any]) -> str:
    clean_base = base_url.rstrip("/") + "/"
    clean_path = PAGE_PATH.lstrip("/")
    return urljoin(clean_base, clean_path) + "?" + urlencode(params)


def request_json(base_url: str, params: dict[str, Any], timeout: float) -> ApiResponse:
    url = build_url(base_url, params)
    request = Request(url, headers={"Accept": "application/json"})

    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            status = response.status
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        status = exc.code
    except (TimeoutError, URLError) as exc:
        raise SmokeFailure(f"Request failed for {url}: {exc}") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SmokeFailure(f"Response was not JSON for {url}: status={status}, body={raw[:200]!r}") from exc

    return ApiResponse(status=status, data=data, raw=raw, url=url)


def require_page_shape(response: ApiResponse, expected_limit: int, expected_offset: int) -> None:
    if response.status != 200:
        raise SmokeFailure(f"Expected HTTP 200, got {response.status} from {response.url}: {response.raw[:200]}")
    if not isinstance(response.data, dict):
        raise SmokeFailure(f"Expected response object, got {type(response.data).__name__}")

    for key in ("items", "total", "limit", "offset"):
        if key not in response.data:
            raise SmokeFailure(f"Missing page key: {key}")

    if not isinstance(response.data["items"], list):
        raise SmokeFailure("Expected items to be a list")
    if not isinstance(response.data["total"], int):
        raise SmokeFailure("Expected total to be an integer")
    if response.data["limit"] != expected_limit:
        raise SmokeFailure(f"Expected limit={expected_limit}, got {response.data['limit']}")
    if response.data["offset"] != expected_offset:
        raise SmokeFailure(f"Expected offset={expected_offset}, got {response.data['offset']}")

    for index, item in enumerate(response.data["items"]):
        if not isinstance(item, dict):
            raise SmokeFailure(f"Expected items[{index}] to be an object")
        if not isinstance(item.get("customer_id"), str) or not item["customer_id"].strip():
            raise SmokeFailure(f"Expected non-empty string customer_id in items[{index}]")


def customer_ids(response: ApiResponse) -> list[str]:
    return [item["customer_id"] for item in response.data["items"]]


def fetch_page(
    base_url: str,
    timeout: float,
    *,
    offset: int,
    limit: int,
    sort: str | None = None,
    direction: str | None = None,
    q: str | None = None,
    filter: str | None = None,
) -> ApiResponse:
    params: dict[str, Any] = {"offset": offset, "limit": limit}
    if sort is not None:
        params["sort"] = sort
    if direction is not None:
        params["direction"] = direction
    if q is not None:
        params["q"] = q
    if filter is not None:
        params["filter"] = filter
    return request_json(base_url, params, timeout)


def check_base_page(base_url: str, timeout: float) -> ApiResponse:
    response = fetch_page(base_url, timeout, offset=0, limit=5)
    require_page_shape(response, expected_limit=5, expected_offset=0)
    return response


def check_sort_direction(base_url: str, timeout: float, sort: str) -> None:
    asc = fetch_page(base_url, timeout, offset=0, limit=5, sort=sort, direction="asc")
    desc = fetch_page(base_url, timeout, offset=0, limit=5, sort=sort, direction="desc")
    require_page_shape(asc, expected_limit=5, expected_offset=0)
    require_page_shape(desc, expected_limit=5, expected_offset=0)

    asc_ids = customer_ids(asc)
    desc_ids = customer_ids(desc)
    if asc_ids == desc_ids:
        raise SmokeFailure(f"asc and desc returned identical first page: {asc_ids}")


def check_sort_before_pagination(base_url: str, timeout: float, sort: str, direction: str) -> None:
    first_ten = fetch_page(base_url, timeout, offset=0, limit=10, sort=sort, direction=direction)
    second_slice = fetch_page(base_url, timeout, offset=5, limit=5, sort=sort, direction=direction)
    require_page_shape(first_ten, expected_limit=10, expected_offset=0)
    require_page_shape(second_slice, expected_limit=5, expected_offset=5)

    expected_ids = customer_ids(first_ten)[5:10]
    actual_ids = customer_ids(second_slice)
    if actual_ids != expected_ids:
        raise SmokeFailure(
            f"offset=5 page {actual_ids} did not match first page slice {expected_ids}"
        )


def check_search_shape(base_url: str, timeout: float, sample_customer_id: str) -> None:
    response = fetch_page(base_url, timeout, offset=0, limit=5, q=sample_customer_id)
    require_page_shape(response, expected_limit=5, expected_offset=0)


def check_filter_shape(base_url: str, timeout: float) -> None:
    response = fetch_page(base_url, timeout, offset=0, limit=5, filter="high_churn_risk")
    require_page_shape(response, expected_limit=5, expected_offset=0)


def check_invalid_sort_does_not_crash(base_url: str, timeout: float) -> None:
    response = fetch_page(
        base_url,
        timeout,
        offset=0,
        limit=5,
        sort="not_a_customer_sort_key",
        direction="asc",
    )
    if response.status >= 500:
        raise SmokeFailure(f"Invalid sort key returned HTTP {response.status}: {response.raw[:200]}")
    if not isinstance(response.data, dict):
        raise SmokeFailure(f"Invalid sort key returned non-object JSON with status {response.status}")


def run_check(name: str, fn: Any) -> CheckResult:
    try:
        fn()
    except SmokeFailure as exc:
        return CheckResult(name=name, passed=False, detail=str(exc))
    except Exception as exc:
        return CheckResult(name=name, passed=False, detail=f"Unexpected error: {type(exc).__name__}: {exc}")
    return CheckResult(name=name, passed=True, detail="ok")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke test /customers/page sorting, search, and filter behavior.")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("CUSTOMER_API_BASE_URL", DEFAULT_BASE_URL),
        help=f"API base URL. Defaults to CUSTOMER_API_BASE_URL or {DEFAULT_BASE_URL}.",
    )
    parser.add_argument("--timeout", type=float, default=10.0, help="Per-request timeout in seconds.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base_url = args.base_url.rstrip("/")
    timeout = args.timeout

    print(f"Smoke testing {PAGE_PATH} at {base_url}")

    base_page: ApiResponse | None = None

    def load_base_page() -> None:
        nonlocal base_page
        base_page = check_base_page(base_url, timeout)

    results = [
        run_check("GET /customers/page?offset=0&limit=5 returns valid JSON", load_base_page),
        run_check("sort=customer_id asc and desc return different orders", lambda: check_sort_direction(base_url, timeout, "customer_id")),
        run_check("sort=days_since_last_txn asc and desc return different orders", lambda: check_sort_direction(base_url, timeout, "days_since_last_txn")),
        run_check("sort=customer_id happens before pagination", lambda: check_sort_before_pagination(base_url, timeout, "customer_id", "asc")),
        run_check("sort=days_since_last_txn happens before pagination", lambda: check_sort_before_pagination(base_url, timeout, "days_since_last_txn", "asc")),
        run_check("filter=high_churn_risk returns valid response shape", lambda: check_filter_shape(base_url, timeout)),
        run_check("invalid sort key does not crash", lambda: check_invalid_sort_does_not_crash(base_url, timeout)),
    ]

    if base_page is None or not base_page.data.get("items"):
        results.append(CheckResult("q search returns valid response shape", False, "Skipped because base page failed or returned no items"))
    else:
        sample_customer_id = base_page.data["items"][0]["customer_id"]
        results.append(
            run_check(
                "q search returns valid response shape",
                lambda: check_search_shape(base_url, timeout, sample_customer_id),
            )
        )

    passed = 0
    failed = 0
    for result in results:
        if result.passed:
            passed += 1
            print(f"PASS {result.name}: {result.detail}")
        else:
            failed += 1
            print(f"FAIL {result.name}: {result.detail}")

    print(f"Summary: {passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
