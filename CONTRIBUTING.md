# Contributing

## Setup

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

## Running the backend test suite

The unit tests (`backend/tests/`) exercise `GeoEngine`, `RuleBasedNarrative`,
and a performance regression guard for the `GROUP BY station` query. None of
them need hydrated data — the geo/narrative classes are pure functions, and
`test_performance.py` builds its own synthetic Parquet fixture.

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest tests/ -v
```

This is exactly what CI runs on every push (`.github/workflows/ci.yml`).

## Running backend lint

```bash
pip install ruff
ruff check backend/
```

## Running the frontend test suite

```bash
cd frontend
npm run test    # vitest, jsdom
npm run lint    # eslint
npm run build   # tsc -b && vite build
```

`src/api.test.ts` covers the three API calls in `src/api.ts` (station list,
cluster info, station narrative), and `src/App.test.tsx` covers the
loading/loaded states and the search-filter logic in `App.tsx`, with
`Map.tsx` mocked out (it renders live MapLibre/WebGL and isn't
unit-testable in jsdom).

**Known gap:** `Map.tsx`, `Sidebar.tsx`, `StationDrawer.tsx`, and `Legend.tsx`
have no component tests of their own yet — only their effect on `App.tsx`'s
render output is covered indirectly. Next step: add
`@testing-library/react` render tests for `Sidebar`'s mode switcher and
`StationDrawer`'s mode-specific content (retail/lifestyle/general), since
those are the components with the most conditional rendering logic.

## Running the benchmark against real data

`scripts/benchmark.py` measures the same query against a real, hydrated
`backend/data/traffic_clean.parquet` and reports p50/p95 latency — this is
what backs the latency figures in the README. Unlike the pytest suite, it
requires real data:

```bash
# Materialize just the ridership asset (no OSMnx/geospatial deps needed):
python -c "
import importlib.util, sys
spec = importlib.util.spec_from_file_location(
    'ingestion', 'dagster_pipeline/assets/ingestion.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.fetch_mta_data()"

mkdir -p backend/data
cp dagster_pipeline/data/processed/traffic_clean.parquet backend/data/

python scripts/benchmark.py
```

For the full data lake (adds POI features, clustering, personas — needs
~2GB RAM for OSMnx graph processing and a `GEMINI_API_KEY` for persona
generation), run the whole pipeline instead:

```bash
dagster asset materialize --select \* -m dagster_pipeline
```

## Running the app locally

```bash
./dev.sh
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`
- Dagster UI: `http://localhost:3000`

## Conventions

- Backend: FastAPI + DuckDB, no ORM, no persistent DB process — Parquet is
  read directly at query time.
- Pipeline: Dagster software-defined assets in `dagster_pipeline/assets/`,
  each asset's function parameters declare its dependencies.
- Keep deterministic logic (borough detection, archetype classification)
  free of LLM calls — `RuleBasedNarrative` and `GeoEngine` are pure
  functions on purpose so they stay unit-testable without mocking.
