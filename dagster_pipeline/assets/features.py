import polars as pl
import osmnx as ox
import pandas as pd
import warnings
from dagster import asset, Output
from .ingestion import fetch_mta_data
from .constants import FEATURES_FILE

# Suppress harmless UserWarnings
warnings.filterwarnings("ignore")

@asset(group_name="enrichment")
def fetch_poi_features(fetch_mta_data: pl.DataFrame):
    """
    Fetches real Point-of-Interest (POI) data from OpenStreetMap for every station.
    
    Logic:
    1. Extract unique Lat/Lon from the traffic data.
    2. Query OSM for specific amenities within 300m (Bars, Offices, Unis).
    3. Save results to Parquet.
    """
    
    # 1. Get unique stations from ingestion output
    # The ingestion pipeline guarantees these columns exist
    stations = fetch_mta_data.select([
        "STATION", 
        "GTFS Latitude", 
        "GTFS Longitude"
    ]).unique()
    
    # Convert to Pandas for looping (OSMnx doesn't support Polars natively yet)
    stations_pd = stations.to_pandas()
    
    total_stations = len(stations_pd)
    print(f"--- STARTING POI ENRICHMENT FOR {total_stations} STATIONS ---")
    print("Note: This performs real geospatial queries. It may take 2-5 minutes.")

    # Define what we are looking for in OpenStreetMap
    tags = {
        'amenity': ['bar', 'pub', 'restaurant', 'university', 'college', 'school', 'cafe'],
        'office': True,  # True means "any tag with key=office"
        'leisure': ['park', 'stadium']
    }
    
    results = []
    
    for idx, row in stations_pd.iterrows():
        station_name = row['STATION']
        lat = row['GTFS Latitude']
        lon = row['GTFS Longitude']
        
        try:
            # Query OSM: 300m radius (approx 4-5 min walk)
            # This returns a GeoDataFrame of features
            pois = ox.features_from_point((lat, lon), tags=tags, dist=300)
            
            # Count Bars/Nightlife
            n_bars = 0
            if 'amenity' in pois.columns:
                n_bars = len(pois[pois['amenity'].isin(['bar', 'pub', 'nightclub'])])
                
            # Count Offices (Corporate)
            n_offices = 0
            if 'office' in pois.columns:
                n_offices = len(pois[pois['office'].notna()])
                
            # Count Universities (Students)
            n_unis = 0
            if 'amenity' in pois.columns:
                n_unis = len(pois[pois['amenity'].isin(['university', 'college'])])
            
            results.append({
                "STATION": station_name,
                "n_bars": n_bars,
                "n_offices": n_offices,
                "n_universities": n_unis
            })
            
        except Exception:
            # If OSMnx fails (empty area, timeout, or weird geometry), fallback to 0
            # This ensures the pipeline doesn't crash on one bad coordinate
            results.append({
                "STATION": station_name,
                "n_bars": 0,
                "n_offices": 0,
                "n_universities": 0
            })
        
        # Progress Log
        if idx % 20 == 0:
            print(f"Processed {idx}/{total_stations} stations...")

    # Convert back to Polars for high-performance join later
    poi_df = pl.DataFrame(results)
    
    # Force Save
    print(f"--- SAVING FEATURE VECTORS TO {FEATURES_FILE} ---")
    poi_df.write_parquet(FEATURES_FILE)
    
    return Output(
        poi_df, 
        metadata={
            "count": len(poi_df),
            "description": "Station Amenity Vectors (Bars, Offices, Unis)"
        }
    )