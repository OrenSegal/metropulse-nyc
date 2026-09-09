import sys
import time
from pathlib import Path

import duckdb
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app import db  # noqa: E402

# CI has no hydrated backend/data/*.parquet (see conftest.py), so this test
# builds its own synthetic ridership file with the real schema/shape
# (STATION, dt, entries) rather than depending on pipeline output. It's a
# regression guard against the query becoming pathologically slow, not a
# reproduction of the README's headline number -- that comes from
# scripts/benchmark.py run against real data.
STATIONS = 344
HOURS = 310  # ~ same order of magnitude as one 30-day pipeline pull
LATENCY_CEILING_MS = 50
FULL_PATH_LATENCY_CEILING_MS = 150


@pytest.fixture(scope="module")
def synthetic_traffic_file(tmp_path_factory):
    rows = []
    start = pd.Timestamp("2026-01-01")
    for s in range(STATIONS):
        for h in range(HOURS):
            rows.append(
                {
                    "STATION": f"Station {s}",
                    "dt": start + pd.Timedelta(hours=h),
                    "entries": float((s * 7 + h * 3) % 500),
                }
            )
    df = pd.DataFrame(rows)

    out_dir = tmp_path_factory.mktemp("data")
    out_file = out_dir / "traffic_clean.parquet"
    df.to_parquet(out_file)
    return out_file


def test_group_by_station_query_is_fast(synthetic_traffic_file):
    query = f"""
        SELECT
            STATION,
            CAST(hour(dt) AS INTEGER) as hr,
            AVG(entries) as vol
        FROM '{synthetic_traffic_file}'
        GROUP BY 1, 2
    """

    con = duckdb.connect(database=":memory:")
    con.execute(query).df()  # warmup
    start = time.perf_counter()
    result = con.execute(query).df()
    elapsed_ms = (time.perf_counter() - start) * 1000
    con.close()

    assert len(result) > 0
    assert elapsed_ms < LATENCY_CEILING_MS, (
        f"GROUP BY station query took {elapsed_ms:.2f}ms, "
        f"exceeding the {LATENCY_CEILING_MS}ms regression ceiling"
    )


def test_full_query_path_is_fast(synthetic_traffic_file):
    # Wider ceiling than the DuckDB-only test above: this path also pays for
    # connection setup and a pandas conversion, and CI runners are shared,
    # noisy-neighbor hardware -- this is a regression guard against the path
    # becoming pathologically slow, not a tight perf assertion.
    query = f"""
        SELECT
            STATION,
            CAST(hour(dt) AS INTEGER) as hr,
            AVG(entries) as vol
        FROM '{synthetic_traffic_file}'
        GROUP BY 1, 2
    """

    db.query(query)  # warmup
    start = time.perf_counter()
    result = db.query(query)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert len(result) > 0
    assert elapsed_ms < FULL_PATH_LATENCY_CEILING_MS, (
        f"Full db.query() path took {elapsed_ms:.2f}ms, "
        f"exceeding the {FULL_PATH_LATENCY_CEILING_MS}ms regression ceiling"
    )
