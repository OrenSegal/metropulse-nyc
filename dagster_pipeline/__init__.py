from dagster import Definitions
from .assets import ingestion, features, modeling, personas

defs = Definitions(
    assets=[
        # Fetch Data
        ingestion.fetch_mta_data,
        
        # Feature Enrichment
        features.fetch_poi_features,
        
        # Train & Generate
        modeling.train_cluster_model,
        personas.generate_personas
    ]
)