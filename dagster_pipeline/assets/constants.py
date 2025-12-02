import os

# Base Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) 
DATA_DIR = os.path.join(BASE_DIR, "data", "processed")

os.makedirs(DATA_DIR, exist_ok=True)

# File Paths
TRAFFIC_FILE = os.path.join(DATA_DIR, "traffic_clean.parquet")
FEATURES_FILE = os.path.join(DATA_DIR, "features.parquet")
CLUSTERS_FILE = os.path.join(DATA_DIR, "clusters.parquet")
PROFILES_FILE = os.path.join(DATA_DIR, "cluster_profiles.json")
PERSONAS_FILE = os.path.join(DATA_DIR, "personas.json")

# Dataset: MTA Subway Hourly Ridership: Beginning 2025
RIDERSHIP_API_URL = "https://data.ny.gov/resource/5wq4-mkjj.json"

# Dataset: MTA Subway Stations (Geocoding)
STATIONS_API_URL = "https://data.ny.gov/resource/39hk-dx4f.json"