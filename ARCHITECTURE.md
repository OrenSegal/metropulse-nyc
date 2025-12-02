# Data Architecture & Engineering Decisions

This document outlines the architectural reasoning behind the Metropulse pipeline. It follows a strict **Problem -> Constraint -> Architectural Decision -> Impact** framework to justify the transformation of raw transit logs into vector-based behavioral archetypes.

## 1. Ingestion Layer: Resilience Patterns

- **Problem:** Public sector APIs (Socrata) often experience unpredictable reporting lags (e.g., data is 3 days stale).
- **Constraint:** Hardcoding query windows (e.g., `date = today - 1`) causes pipeline failures during upstream delays.
- **Decision:** Implemented **Dynamic Watermarking**. The ingestion asset first queries the API's metadata for `max(transit_timestamp)`, then defines the extraction window relative to the _data's_ latest watermark, not the _system's_ clock.
- **Impact:** The pipeline is self-healing, ensuring a complete 30-day statistical window is always processed regardless of upstream latency.

## 2. Standardization Layer: Entity Resolution

- **Problem:** The MTA dataset suffers from schema drift and inconsistencies. Station names vary ("14 St" vs "14th Street"), and `complex_id` mappings drift over time.
- **Constraint:** We need a canonical "Golden Record" to reliably join ridership data with OpenStreetMap geospatial tags.
- **Decision:** Implemented a **Reference Entity Map** during the Bronze-to-Silver transition.
  - _Normalization:_ Regex-based string cleaning removes non-alphanumeric noise (`re.sub(r'[^a-zA-Z0-9]', ...)`).
  - _Geospatial Centroids:_ Multiple entrances for a single complex are aggregated into a single Lat/Lon centroid.
- **Impact:** Zero cardinality mismatches during the enrichment phase; guarantees stable keys for the caching layer.

## 3. Transformation: Signal Processing & Vectorization

- **Problem:** Clustering based on raw volume is flawed. Grand Central Terminal and a small local stop might share the exact same commuter pattern, but Euclidean distance would treat them as distinct due to magnitude differences.
- **Decision:** Adopted **Z-Score Normalization & Dimensional Pivoting**.
  - _Vectorization:_ Time-series data is pivoted into **168-dimensional vectors** (Hour-of-Week: 0–167).
  - _Scaling:_ Applied `TimeSeriesScalerMeanVariance` to flatten Y-axis magnitude.
- **Impact:** The model clusters based on the _shape_ of the curve (behavior), allowing us to group stations by "Personality" (e.g., "Commuter vs. Nightlife") rather than "Size".

## 4. Enrichment: Mathematical Geofencing

- **Problem:** Standard rectangular bounding boxes fail in NYC due to the diagonal nature of the East River (e.g., Long Island City is geographically west of parts of Manhattan).
- **Constraint:** Relying on external GIS APIs for every request introduces unacceptable latency and cost.
- **Decision:** Implemented a **Linear Boundary Engine** (`GeoEngine`). This defines the borough borders as linear functions ($y = mx + b$) rather than static polygons.
- **Impact:** Achieves $O(1)$ classification precision for edge cases (DUMBO, LIC) without the overhead of PostGIS.

## 5. Serving Layer: The "Lakehouse-Lite"

**Problem:** Traditional Data Warehouses incur high fixed costs and latency for read-heavy, write-once workloads.
- **Decision:** Decoupled Compute and Storage.
  - _Storage:_ Processed artifacts are materialized as **Parquet** files.
  - _Compute:_ The API utilizes **DuckDB** in-process to execute SQL directly over Parquet.
- **Impact:** Sub-millisecond analytical query performance on a serverless footprint, eliminating database maintenance overhead.

## 6. Intelligence Layer: Hybrid Deterministic/Generative

- **Problem:** Generative AI is prone to hallucination when analyzing abstract data tables.
- **Decision:** Utilized a **RAG-Lite Context Injection** pattern.
  - _Deterministic Foundation:_ We calculate hard metrics first—`Social Pulse` (Percentile Rank of Nightlife Density) and `Retail Gap`.
  - _Injection:_ These calculated integers are injected into the LLM system prompt as constraints.
- **Impact:** The LLM does not _guess_ the vibe; it _translates_ engineered metrics into narrative, ensuring output is grounded in statistical reality.
