from pydantic import BaseModel
from typing import List, Optional

class Persona(BaseModel):
    name: str
    description: str
    tags: List[str]

class ClusterSummary(BaseModel):
    cluster_id: int
    persona: Persona
    station_count: int
    avg_bars: float
    example_station: str
    chart_data: List[float]  # 24 hourly values

class StationDetail(BaseModel):
    STATION: str
    cluster_id: int
    GTFS_Latitude: float
    GTFS_Longitude: float
    n_bars: Optional[int] = 0
    n_offices: Optional[int] = 0
    n_universities: Optional[int] = 0
    persona_name: Optional[str] = "Unknown"