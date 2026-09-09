# Run from repo root: python scripts/benchmark.py
#
# Benchmarks the "GROUP BY station" query that backend/app/main.py's
# preload_data() runs against backend/data/traffic_clean.parquet on every
# cold start. Requires that file to exist -- it's a pipeline output, not
# checked into git (see .gitignore) -- so hydrate it first:
#
#   python -c "
#   import importlib.util, sys
#   spec = importlib.util.spec_from_file_location(
#       'ingestion', 'dagster_pipeline/assets/ingestion.py')
#   m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
#   m.fetch_mta_data()"
#   mkdir -p backend/data
#   cp dagster_pipeline/data/processed/traffic_clean.parquet backend/data/
#
# Two numbers are reported because they answer different questions:
#   - "DuckDB execute" is the raw SQL engine time (what the README's ~6ms
#     figure describes): conn.execute(query).df().
#   - "Full db.query() path" additionally does the inf/NaN cleanup and
#     df.to_dict(orient="records") conversion that backend/app/db.py does
#     on every real request, plus a fresh :memory: connection per call
#     (matching db.get_data()'s "fresh connection per request" design) --
#     this is what a client actually waits on.
import statistics
import sys
import time
from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app import db  # noqa: E402

DATA_FILE = REPO_ROOT / "backend" / "data" / "traffic_clean.parquet"
WARMUP_ITERS = 10
BENCH_ITERS = 100

QUERY = f"""
    SELECT
        STATION,
        CAST(hour(dt) AS INTEGER) as hr,
        AVG(entries) as vol
    FROM '{DATA_FILE}'
    GROUP BY 1, 2
"""


def percentile(samples_ms, pct):
    ordered = sorted(samples_ms)
    idx = min(len(ordered) - 1, int(round(pct / 100 * (len(ordered) - 1))))
    return ordered[idx]


def bench_duckdb_execute():
    con = duckdb.connect(database=":memory:")
    for _ in range(WARMUP_ITERS):
        con.execute(QUERY).df()
    samples = []
    for _ in range(BENCH_ITERS):
        start = time.perf_counter()
        con.execute(QUERY).df()
        samples.append((time.perf_counter() - start) * 1000)
    con.close()
    return samples


def bench_full_db_query_path():
    for _ in range(WARMUP_ITERS):
        db.query(QUERY)
    samples = []
    for _ in range(BENCH_ITERS):
        start = time.perf_counter()
        db.query(QUERY)
        samples.append((time.perf_counter() - start) * 1000)
    return samples


def report(name, samples):
    p50 = percentile(samples, 50)
    p95 = percentile(samples, 95)
    print(f"{name}: p50={p50:.2f}ms  p95={p95:.2f}ms  (n={len(samples)})")
    return p50, p95


def main():
    if not DATA_FILE.exists():
        print(f"Missing {DATA_FILE} -- hydrate it first (see script docstring).")
        sys.exit(1)

    con = duckdb.connect(database=":memory:")
    row_count, station_count = con.execute(
        f"SELECT COUNT(*), COUNT(DISTINCT STATION) FROM '{DATA_FILE}'"
    ).fetchone()
    con.close()
    print(f"Data: {row_count} rows across {station_count} stations\n")

    report("DuckDB execute only", bench_duckdb_execute())
    print()
    report("Full db.query() path (incl. pandas cleanup + fresh connection)",
           bench_full_db_query_path())


if __name__ == "__main__":
    main()
