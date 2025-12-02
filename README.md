# Metropulse NYC: Urban Mobility Intelligence Platform

## System Overview

Metropulse is a high-performance **Lakehouse-Lite** architecture designed to segment NYC subway stations into behavioral archetypes. By synthesizing temporal ridership signals (MTA) with geospatial amenity vectors (OpenStreetMap), the system constructs a "Station DNA" used to drive unsupervised learning models and hybrid narrative generation.

The platform decouples compute (Dagster/Polars) from serving (FastAPI/DuckDB), allowing for high-throughput analytics on static file artifacts without persistent database overhead.

## Architecture

### 1. Data Engineering Pipeline (ELT)

The pipeline is orchestrated via **Dagster** (`dagster_pipeline/`) and follows a functional data flow pattern:

- **Ingestion (Resilient Fetch):**
  - _Source:_ NY Open Data (Socrata API).
  - _Logic:_ Implements dynamic date-window detection to query the `max(transit_timestamp)` and fetch a rolling 30-day window. This handles upstream reporting lags gracefully.
- **Enrichment (Geospatial Vectorization):**
  - _Source:_ OpenStreetMap (Overpass API via OSMnx).
  - _Logic:_ Generates 300m isochrones around every station centroid to calculate feature vectors: `nightlife` (amenity=bar), `corporate` (office=\*), and `academic` (amenity=university).
- **Transformation (Time-Series Engineering):**
  - _Signal Processing:_ Ridership is pivoted from scalar rows to **168-dimensional vectors** (Hour-of-Week).
  - _Scaling:_ `TimeSeriesScalerMeanVariance` (Z-Score) is applied to normalize volume, ensuring clustering is based on _temporal shape_ (commuter patterns) rather than magnitude.

### 2. Logic Engines (Backend)

The FastAPI backend (`backend/app/main.py`) implements sophisticated deterministic logic to ensure reliability before calling AI.

- **GeoEngine (Linear Boundary Classification):**
  - Instead of simple bounding boxes, we utilize a **Slope-Intercept** model to define the diagonal boundary of the East River.
  - This mathematically distinguishes Manhattan from Brooklyn/Queens with high precision, handling edge cases like DUMBO and Long Island City correctly.
- **NarrativeEngine (Hybrid Deterministic/Generative):**
  - _Layer 1 (Deterministic):_ A rule-based engine generates a "Base Narrative" using strict thresholds (e.g., `Social Pulse > 80` + `Night Traffic > 40` = "Nightlife District"). This ensures factual accuracy regarding borough and archetype.
  - _Layer 2 (Generative):_ Google Gemini 2.0 Flash is used solely for stylistic polishing, injected with the strict constraints of Layer 1 to prevent hallucinations.

### 3. Serving Layer (OLAP)

- **Storage:** Columnar Parquet files (`backend/data/*.parquet`) serve as the System of Record.
- **Query Engine:** **DuckDB** runs in-process within the API, executing SQL directly over Parquet with zero-copy reads.
- **Context-Aware UI:** The frontend adapts its visualization strategy based on the analytical mode (General, Lifestyle, or Retail Scout).

## Metric Definitions

### Social Pulse ($S_p$)

_Previously "Vitality Score"._
A percentile rank quantifying the **"Off-Work" energy** of a neighborhood. It combines the density of social amenities (bars, restaurants, culture) with late-night ridership patterns.
$$ S*p = \text{Percentile}(Density*{amenities} \times Ridership\_{night}) $$

- **> 80:** High Energy / Nightlife Hub.
- **< 20:** Quiet / Residential Zone.

### Retail Gap ($R_g$)

Quantifies the imbalance between workforce density and local services.
$$ R_g = \text{Norm}(O_s) - \text{Norm}(S_p) $$

- **High Gap (> 0.6):** High concentration of office workers but low Social Pulse (amenities). Indicates a prime investment opportunity for retail or lunch spots.

### Time DNA

A vectorized representation of the station's "Pulse".

- **Morning Peak (6-10 AM):** Commuter Outflow (Residential) or Inflow (Commercial).
- **Night Peak (10 PM - 4 AM):** Indicator of specific nightlife destinations vs. 24h hubs.

## Setup & Deployment

### Prerequisites

- Python 3.10+
- Node.js 18+
- Google Gemini API Key (Optional, for narrative polish)

### Local Development

1.  **Hydrate Data Lake:**

    ```bash
    # Runs the ETL pipeline to generate Parquet files
    # Note: Requires ~2GB RAM for OSMnx graph processing
    dagster asset materialize --select \* -m dagster_pipeline
    ```

2.  **Start Platform:**
    ```bash
    ./dev.sh
    ```
    - Backend: `http://localhost:8000`
    - Frontend: `http://localhost:5173`
    - Dagster UI: `http://localhost:3000`
