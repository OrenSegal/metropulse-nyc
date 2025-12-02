import polars as pl
import numpy as np
import json
from dagster import asset, Output
from tslearn.clustering import TimeSeriesKMeans
from tslearn.preprocessing import TimeSeriesScalerMeanVariance
from .features import fetch_poi_features
from .ingestion import fetch_mta_data
from .constants import CLUSTERS_FILE, PROFILES_FILE

@asset(group_name="ml")
def train_cluster_model(fetch_mta_data: pl.DataFrame, fetch_poi_features: pl.DataFrame):
    """
    Trains a Time-Series K-Means model to segment stations.
    
    Outputs:
    1. clusters.parquet: The main DB table (Station -> Cluster ID -> Stats)
    2. cluster_profiles.json: The chart data for the frontend (Average Ridership Curve)
    """
    
    print("--- PREPARING TIME SERIES DATA ---")
    
    # 1. Feature Engineering: Create "Hour of Week" (0 to 167)
    # This aligns Monday 1AM, Tuesday 1AM etc. across all weeks.
    df = fetch_mta_data.with_columns(
        (pl.col("dt").dt.weekday() * 24 + pl.col("dt").dt.hour()).alias("hour_of_week"),
        # New API has 'entries', 'exits' (0). We sum them to be safe.
        (pl.col("entries") + pl.col("exits")).alias("total_traffic")
    )
    
    # 2. Filter Low Volume Stations
    # Stations with practically zero traffic mess up the scaling/clustering
    station_vols = df.group_by("STATION").agg(pl.col("total_traffic").sum())
    valid_stations = station_vols.filter(pl.col("total_traffic") > 500).select("STATION")
    df = df.join(valid_stations, on="STATION", how="inner")
    
    # 3. Aggregate to "Average Week" Profile
    # Group by Station + HourOfWeek -> Mean Traffic
    profile_df = df.group_by(["STATION", "hour_of_week"]).agg(
        pl.col("total_traffic").mean()
    ).sort(["STATION", "hour_of_week"])

    # 4. Pivot to Matrix (Rows=Stations, Cols=0..167)
    pivot_df = profile_df.pivot(
        values="total_traffic",
        index="STATION",
        columns="hour_of_week",
        aggregate_function="mean"
    ).fill_null(0) # Zero fill missing hours
    
    # 5. Convert to Numpy for Machine Learning
    station_names = pivot_df["STATION"].to_list()
    # Drop the name column to get pure numbers
    X = pivot_df.drop("STATION").to_numpy()
    
    # Robustness: Ensure strictly 168 columns (7 days * 24 hours)
    # If data is missing (e.g. API only returned 165 hours), pad it.
    expected_hours = 168
    if X.shape[1] < expected_hours:
        padding = np.zeros((X.shape[0], expected_hours - X.shape[1]))
        X = np.hstack([X, padding])
    elif X.shape[1] > expected_hours:
        # Truncate if somehow larger
        X = X[:, :expected_hours]
    
    # Reshape for TSLEARN: (n_samples, n_timestamps, n_features)
    X = X.reshape((X.shape[0], expected_hours, 1))
    
    # 6. Scaling (Z-Score)
    # Crucial: We want to cluster by SHAPE (Pattern), not Volume.
    # This makes "Small Station Commute" look like "Grand Central Commute".
    print("Scaling Time Series...")
    scaler = TimeSeriesScalerMeanVariance()
    X_scaled = scaler.fit_transform(X)
    
    # 7. Train Model
    # We use Euclidean distance for speed/stability in this demo.
    # (Soft-DTW is better but takes 10x longer).
    print("--- TRAINING K-MEANS MODEL (k=5) ---")
    n_clusters = 5
    km = TimeSeriesKMeans(n_clusters=n_clusters, metric="euclidean", max_iter=10, random_state=42)
    labels = km.fit_predict(X_scaled)
    
    # 8. Extract Centroids for Charts
    # These represent the "Archetypal" week for each cluster.
    print(f"--- SAVING CHART PROFILES TO {PROFILES_FILE} ---")
    cluster_centers = km.cluster_centers_.squeeze() # Shape (5, 168)
    
    profiles_json = []
    for i in range(n_clusters):
        # We take the full week (168 points) for the chart
        profiles_json.append({
            "cluster_id": int(i),
            "hourly_profile": cluster_centers[i].tolist()
        })
        
    with open(PROFILES_FILE, "w") as f:
        json.dump(profiles_json, f)

    # 9. Create Final DataFrame
    # Join Clusters + Amenities + Lat/Lon
    results_df = pl.DataFrame({
        "STATION": station_names, 
        "cluster_id": labels
    })
    
    # Get coordinates from original data (unique mapping)
    coords_df = fetch_mta_data.select(["STATION", "GTFS Latitude", "GTFS Longitude"]).unique()
    
    # Join everything: Clusters -> POI Features -> Coordinates
    final_df = results_df.join(fetch_poi_features, on="STATION", how="left") \
                         .join(coords_df, on="STATION", how="left")
    
    print(f"--- SAVING CLUSTERS TO {CLUSTERS_FILE} ---")
    final_df.write_parquet(CLUSTERS_FILE)
    
    return Output(
        final_df, 
        metadata={
            "n_clusters": n_clusters, 
            "file": CLUSTERS_FILE
        }
    )