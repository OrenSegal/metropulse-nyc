import polars as pl
import requests
from datetime import datetime, timedelta
from dagster import asset, Output
from .constants import RIDERSHIP_API_URL, STATIONS_API_URL, TRAFFIC_FILE

@asset(group_name="ingestion")
def fetch_mta_data():
    """
    Fetches Official MTA Hourly Ridership from NY Open Data API.
    - Uses Dynamic Date Detection (finds latest available data) to prevent empty results.
    """
    
    # 1. Fetch Geocoding Reference (Station Locations)
    print("--- FETCHING STATION LOCATIONS ---")
    try:
        st_resp = requests.get(f"{STATIONS_API_URL}?$limit=1000")
        st_resp.raise_for_status()
        
        st_data = st_resp.json()
        stations_df = pl.DataFrame(st_data).select([
            pl.col("complex_id").cast(pl.Utf8),
            pl.col("gtfs_latitude").cast(pl.Float64).alias("lat"),
            pl.col("gtfs_longitude").cast(pl.Float64).alias("lon"),
            pl.col("stop_name").alias("STATION")
        ]).unique(subset=["complex_id"])
        
        print(f"Loaded {len(stations_df)} stations.")
        
    except Exception as e:
        raise ValueError(f"Failed to fetch station metadata: {e}")

    # 2. Dynamic Date Detection (The Robust Fix)
    print("--- DETECTING LATEST DATA AVAILABILITY ---")
    try:
        # Ask Socrata for the maximum timestamp in the dataset
        max_date_query = {
            "$select": "max(transit_timestamp)",
        }
        max_resp = requests.get(RIDERSHIP_API_URL, params=max_date_query)
        max_resp.raise_for_status()
        
        latest_str = max_resp.json()[0]['max_transit_timestamp']
        latest_dt = datetime.fromisoformat(latest_str)
        
        # Calculate start date (30 days before the LATEST data, not today)
        start_dt = latest_dt - timedelta(days=30)
        start_str = start_dt.strftime("%Y-%m-%dT00:00:00")
        
        print(f"Latest Data Available: {latest_str}")
        print(f"Fetching Range: {start_str} to {latest_str}")
        
    except Exception as e:
        print(f"Date detection failed ({e}). Fallback to hardcoded 30 days ago.")
        start_str = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%dT00:00:00")

    # 3. Fetch Ridership Data
    print(f"--- FETCHING RIDERSHIP ---")
    params = {
        "$where": f"transit_timestamp >= '{start_str}'",
        "$limit": 600000, # Cap high enough to capture 30 days (~450k rows)
        "$order": "transit_timestamp"
    }
    
    try:
        r_resp = requests.get(RIDERSHIP_API_URL, params=params)
        r_resp.raise_for_status()
        r_data = r_resp.json()
        
        if not r_data:
            # If still empty, the dataset ID might be wrong or server is down
            raise ValueError(f"API returned 0 rows. Dataset ID: {RIDERSHIP_API_URL}")
            
        print(f"Downloaded {len(r_data)} hourly records.")
        
    except Exception as e:
        raise ValueError(f"Failed to fetch ridership data: {e}")

    # 4. Process with Polars
    print("--- PROCESSING DATA ---")
    traffic_df = pl.DataFrame(r_data)
    
    # Cast types
    traffic_df = traffic_df.select([
        pl.col("transit_timestamp").str.to_datetime().alias("dt"),
        pl.col("station_complex_id").cast(pl.Utf8).alias("complex_id"),
        pl.col("ridership").cast(pl.Float64).fill_null(0)
    ])
    
    # 5. Join with Geodata
    joined_df = traffic_df.join(stations_df, on="complex_id", how="inner")
    
    # 6. Aggregate to Hourly Station Totals
    final_df = joined_df.group_by(["STATION", "complex_id", "dt", "lat", "lon"]).agg([
        pl.col("ridership").sum().alias("entries")
    ]).sort(["STATION", "dt"])
    
    # Rename for compatibility
    final_df = final_df.rename({
        "lat": "GTFS Latitude", 
        "lon": "GTFS Longitude"
    })
    
    # Add dummy exits (API doesn't track exits, but ML model expects the col)
    final_df = final_df.with_columns(pl.lit(0).alias("exits"))

    print(f"--- SAVING TO {TRAFFIC_FILE} ---")
    final_df.write_parquet(TRAFFIC_FILE)
    
    return Output(final_df, metadata={"rows": len(final_df)})