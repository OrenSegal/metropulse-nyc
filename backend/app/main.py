from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from . import db
from .schemas import ClusterSummary
import json
import numpy as np
import os
import logging
from dotenv import load_dotenv
from pathlib import Path
import math
import re

# Load API Key
load_dotenv()

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- AI Setup ---
try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

app = FastAPI(title="MetroPulse NYC")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Path Resolution ---
BASE_DIR = Path(__file__).resolve().parent.parent 
DATA_DIR = BASE_DIR / "data"

# --- Helper: Normalization ---
def normalize_key(name):
    """Standardizes station names for lookup."""
    if not name: return ""
    return re.sub(r'[^a-zA-Z0-9]', '', str(name)).lower()

# --- Caching & State ---
NARRATIVES_FILE = DATA_DIR / "narratives.json"
NARRATIVES_CACHE = {}

# Global Distributions for Percentile Calcs
DISTRIBUTIONS = {
    "bars": [],
    "offices": [],
    "unis": []
}

def load_cache():
    global NARRATIVES_CACHE
    if NARRATIVES_FILE.exists():
        try:
            with open(NARRATIVES_FILE, "r") as f:
                NARRATIVES_CACHE = json.load(f)
        except Exception:
            NARRATIVES_CACHE = {}

def save_cache():
    try:
        with open(NARRATIVES_FILE, "w") as f:
            json.dump(NARRATIVES_CACHE, f, indent=2)
    except Exception:
        pass

# --- Data Loading ---
PERSONAS = {}
CLUSTER_PROFILES = {}
STATION_PULSE_CACHE = {}

load_cache()

try:
    p_file = DATA_DIR / "personas.json"
    if p_file.exists():
        with open(p_file, "r") as f:
            PERSONAS = json.load(f)
    
    cp_file = DATA_DIR / "cluster_profiles.json"
    if cp_file.exists():
        with open(cp_file, "r") as f:
            profiles = json.load(f)
            for p in profiles:
                # Store generic profiles scaled 0-100 for fallbacks
                raw_profile = np.array(p.get("hourly_profile", [0]*168))
                if raw_profile.max() > raw_profile.min():
                    scaled = (raw_profile - raw_profile.min()) / (raw_profile.max() - raw_profile.min()) * 100
                else:
                    scaled = raw_profile * 0 + 20 
                CLUSTER_PROFILES[str(p["cluster_id"])] = scaled.tolist()
except Exception as e:
    logger.error(f"Static data load failed: {e}")

# --- AI Client ---
api_key = os.getenv("GEMINI_API_KEY")
client = None
if HAS_GENAI and api_key:
    try:
        client = genai.Client(api_key=api_key)
    except Exception:
        pass

# --- 1. Robust Data Preloader ---
def preload_data():
    global STATION_PULSE_CACHE, DISTRIBUTIONS
    traffic_file = DATA_DIR / "traffic_clean.parquet"
    clusters_file = DATA_DIR / "clusters.parquet"
    
    # 1. Load Pulses
    if traffic_file.exists():
        try:
            query_str = f"""
                SELECT 
                    STATION, 
                    CAST(hour(dt) AS INTEGER) as hr, 
                    AVG(entries) as vol
                FROM '{traffic_file}'
                GROUP BY 1, 2
            """
            raw_data = db.query(query_str)
            temp_cache = {}
            for row in raw_data:
                key = normalize_key(row['STATION'])
                h = row['hr']
                v = row['vol']
                if v is None or math.isnan(v): v = 0.0
                if key not in temp_cache: temp_cache[key] = [0.0] * 24
                if 0 <= h < 24: temp_cache[key][h] = v
            
            for s, values in temp_cache.items():
                arr = np.array(values)
                range_val = arr.max() - arr.min()
                if range_val > 0:
                    arr = (arr - arr.min()) / range_val * 100
                elif arr.max() > 0:
                    arr[:] = 50.0
                else:
                    arr[:] = 5.0 
                STATION_PULSE_CACHE[s] = arr.tolist()
            logger.info(f"Loaded pulses for {len(STATION_PULSE_CACHE)} stations.")
        except Exception as e:
            logger.error(f"Pulse generation failed: {e}")

    # 2. Load Metric Distributions for Vitality Calc
    if clusters_file.exists():
        try:
            q = f"SELECT n_bars, n_offices, n_universities FROM '{clusters_file}'"
            rows = db.query(q)
            DISTRIBUTIONS["bars"] = [r['n_bars'] or 0 for r in rows]
            DISTRIBUTIONS["offices"] = [r['n_offices'] or 0 for r in rows]
            DISTRIBUTIONS["unis"] = [r['n_universities'] or 0 for r in rows]
            logger.info("Loaded global amenity distributions.")
        except Exception as e:
            logger.error(f"Distribution load failed: {e}")

# Run preloader
preload_data()

# --- 2. Logic Engines ---

class GeoEngine:
    @staticmethod
    def get_borough(lat, lon):
        """
        Robust Borough Detection using Linear Boundary Separation.
        This handles the diagonal nature of the East River.
        """
        if lat is None or lon is None: return "NYC"
        
        # 1. The Bronx (North of Harlem River)
        if lat > 40.835: return "Bronx"
        
        # 2. Staten Island (Isolated West)
        if lon < -74.05: return "Staten Island"
        
        # 3. Deep Queens (East of everything)
        # Any point East of Flushing Bay/Prospect Park is safely Queens/BK
        if lon > -73.85: return "Queens" 

        # 4. MANHATTAN VS OUTER BOROUGHS (The East River Diagonal)
        # Manhattan creates a diagonal line. We define 3 points along the East River.
        # If a point is WEST (lon < border) of these lines, it's Manhattan.
        
        is_manhattan = False
        
        # Zone A: Upper East Side vs Astoria (North of 59th St / 40.76)
        if lat > 40.76:
            # Border is roughly -73.94
            if lon < -73.935: is_manhattan = True
            
        # Zone B: Midtown vs LIC (40.74 to 40.76)
        # The river cuts in here. Border is approx -73.96
        elif lat > 40.74:
            if lon < -73.96: is_manhattan = True
            
        # Zone C: Lower Manhattan vs Brooklyn (South of 40.74)
        # The river bulges West towards FiDi.
        # We use a slope approximation.
        # At 40.70 (Dumbo), border is -73.99
        # At 40.73 (Greenpoint), border is -73.96
        else:
            # Simple linear boundary for Lower Manhattan
            # Slope formula check roughly:
            east_river_border = -74.01 + (lat - 40.68) * 0.8
            if lon < east_river_border: is_manhattan = True

        if is_manhattan:
            # Final Sanity Check for Marble Hill/Inwood extremes
            if lat > 40.88: return "Bronx"
            return "Manhattan"

        # 5. BROOKLYN VS QUEENS (The Newtown Creek Divide)
        # Now we know it's NOT Manhattan, Bronx, or SI.
        # Divide Brooklyn and Queens.
        
        # Rockaways (Far South, usually Queens)
        if lat < 40.60:
            if lon > -73.90: return "Queens" # Rockaway
            return "Brooklyn" # Coney Island / Brighton

        # Newtown Creek is roughly Latitude 40.73
        # North of 40.73 is generally Queens (LIC/Sunnyside)
        # South of 40.73 is generally Brooklyn (Greenpoint/Williamsburg)
        
        # However, Ridgewood (Queens) dips south.
        if lat > 40.70:
            # East of -73.91 is usually Ridgewood/Maspeth (Queens)
            if lon > -73.91: return "Queens"
            # West of -73.91 and North of 40.72 is LIC/Sunnyside (Queens)
            if lat > 40.735: return "Queens"
            
            return "Brooklyn"
            
        # Deep South (Lat < 40.70)
        # East New York / Cypress Hills border
        if lat < 40.70 and lon > -73.86: return "Queens" # Ozone Park
        
        return "Brooklyn"

class RuleBasedNarrative:
    @staticmethod
    def generate(borough, vitality, office, uni, time_dna):
        """
        Deterministic Description Generator.
        Uses specific ranges to determine archetype without LLM hallucination.
        """
        # A. Determine Primary Character
        character_type = "Standard"
        if uni > 2: character_type = "Academic"
        elif vitality > 75 and time_dna['night'] > 40: character_type = "Nightlife"
        elif office > 70: character_type = "Corporate"
        elif office > 50 and vitality > 50: character_type = "Mixed-Use"
        elif time_dna['morning'] > 60: character_type = "Commuter"
        elif vitality < 20 and office < 20: character_type = "Residential"
        
        # B. Generate Persona Title
        persona_map = {
            "Academic": f"{borough} Student Hub",
            "Nightlife": f"{borough} Nightlife District",
            "Corporate": f"{borough} Business Center",
            "Mixed-Use": f"Dynamic {borough} Hub",
            "Commuter": "Major Transit Anchor",
            "Residential": "Local Neighborhood Stop",
            "Standard": f"{borough} Local Stop"
        }
        persona = persona_map.get(character_type, "Local Station")

        # C. Generate Vibe Description (Sentence 1)
        vibe_desc = ""
        if character_type == "Academic":
            vibe_desc = "Defined by student foot traffic and nearby educational institutions."
        elif character_type == "Nightlife":
            vibe_desc = f"A high-energy area (Vitality: {int(vitality)}%) bustling with evening social activity."
        elif character_type == "Corporate":
            vibe_desc = f"A dense commercial district dominated by office buildings and professional services."
        elif character_type == "Mixed-Use":
            vibe_desc = "A balanced 'Live-Work-Play' neighborhood combining commercial density with social amenities."
        elif character_type == "Residential":
            vibe_desc = "A quieter, community-focused area serving local residents."
        else:
            vibe_desc = f"A key {borough} transit point serving the surrounding community."

        # D. Generate Time Context (Sentence 2)
        # Explicit definitions of time ranges for explainability
        peak_time = max(time_dna, key=time_dna.get)
        time_desc = ""
        
        if peak_time == "morning":
            time_desc = "Passenger volume peaks in the Morning (6-10am), indicating a heavy outbound commuter flow."
        elif peak_time == "lunch":
            time_desc = "Activity is highest midday (11am-2pm), driven by local lunch crowds."
        elif peak_time == "evening":
            time_desc = "Passenger volume swells in the Evening (4-8pm) as the workday ends and retail activity picks up."
        elif peak_time == "night":
            time_desc = "Unusually high Late Night (10pm-4am) ridership signals a destination for after-hours entertainment."
        else:
            time_desc = "Ridership remains consistent throughout the day."

        return {
            "persona": persona,
            "description": f"{vibe_desc} {time_desc}"
        }

def get_clean_time_dna(station_name, cluster_id):
    key = normalize_key(station_name)
    if key in STATION_PULSE_CACHE:
        day = np.array(STATION_PULSE_CACHE[key])
    else:
        cluster_profile = CLUSTER_PROFILES.get(str(cluster_id), [])
        day = np.array(cluster_profile[:24] if len(cluster_profile) >= 24 else [20.0]*24)

    day = np.nan_to_num(day, nan=0.0)
    return {
        "morning": int(np.mean(day[6:10])),   
        "lunch": int(np.mean(day[11:14])),    
        "evening": int(np.mean(day[16:20])),  
        "night": int((np.mean(day[22:24]) + np.mean(day[0:4])) / 2)
    }

def calculate_percentile(dist_key, value):
    data = DISTRIBUTIONS.get(dist_key, [])
    if not data: return 0.0
    if value is None: value = 0
    # Simple rank calculation
    count_less = sum(1 for x in data if x < value)
    return (count_less / len(data)) * 100

# --- 3. Endpoints ---

@app.get("/intelligence/stations")
def get_intelligent_stations():
    db_file = DATA_DIR / "clusters.parquet"
    if not db_file.exists(): return []

    query = f"""
        SELECT 
            STATION, cluster_id, 
            "GTFS Latitude" as lat, "GTFS Longitude" as lon,
            CAST(n_bars AS INTEGER) as n_bars,
            CAST(n_offices AS INTEGER) as n_offices,
            CAST(n_universities AS INTEGER) as n_universities
        FROM '{db_file}'
    """
    results = db.query(query)
    
    enriched = []
    for row in results:
        cid = str(row['cluster_id'])
        dna = get_clean_time_dna(row['STATION'], cid)
        borough = GeoEngine.get_borough(row['lat'], row['lon'])
        
        # Calculate scores
        vitality = calculate_percentile("bars", row['n_bars'])
        office_score = calculate_percentile("offices", row['n_offices'])
        
        # Retail Scout Logic
        # Gap = High potential if High Office (Workers) but Low Vitality (Food/Bev)
        retail_gap = 0.0
        if office_score > 60 and vitality < 40:
            retail_gap = 0.9  # Prime Opportunity
        elif office_score > 40 and vitality < 50:
            retail_gap = 0.6  # Moderate Opportunity
        elif vitality > 80:
            retail_gap = 0.1  # Saturated
        
        enriched.append({
            **row,
            "persona_name": PERSONAS.get(cid, {}).get("name", "Unknown"),
            "time_dna": dna,
            "metrics": {
                "weekend_vitality": vitality / 100.0, 
                "borough": borough,
                "office_density": office_score,
                "retail_gap": retail_gap
            }
        })
    return enriched

@app.get("/intelligence/narrative/{station}")
def get_station_analysis(station: str):
    # Check Cache
    if station in NARRATIVES_CACHE and isinstance(NARRATIVES_CACHE[station], dict):
        return NARRATIVES_CACHE[station]

    db_file = DATA_DIR / "clusters.parquet"
    rows = db.query(f"SELECT * FROM '{db_file}' WHERE STATION = ?", (station,))
    
    if not rows:
        return {"persona": "Unknown Station", "description": "Data unavailable."}
    
    data = rows[0]
    cid = str(data['cluster_id'])
    
    # Critical Geodata Fix
    lat, lon = data['GTFS Latitude'], data['GTFS Longitude']
    borough = GeoEngine.get_borough(lat, lon)
    
    time_dna = get_clean_time_dna(station, cid)
    
    # Calculate Real Metrics
    vitality_score = calculate_percentile("bars", data['n_bars'])
    office_score = calculate_percentile("offices", data['n_offices'])
    uni_count = data['n_universities'] or 0
    
    # 1. GENERATE DETERMINISTIC NARRATIVE (Primary Source)
    base_analysis = RuleBasedNarrative.generate(
        borough, vitality_score, office_score, uni_count, time_dna
    )
    
    result = {
        **base_analysis,
        "vitality_score": vitality_score,
        "office_score": office_score,
        "is_ai_generated": False
    }

    # 2. OPTIONAL LLM POLISH
    if client:
        try:
            prompt = f"""
            Refine this analysis for {station} in {borough}.
            
            Context:
            - {base_analysis['description']}
            - Vitality Score: {int(vitality_score)}/100 (Nightlife percentile)
            - Peak Time: {max(time_dna, key=time_dna.get)}
            
            Task:
            Write a polished 2-sentence description. 
            1. Keep the borough correct ({borough}). 
            2. Explain WHY the vitality score matters (e.g. "Low vitality suggests a quiet residential area").
            3. Do not hallucinate amenities not present.
            
            Return JSON: {{ "persona": "{base_analysis['persona']}", "description": "..." }}
            """
            
            resp = client.models.generate_content(model='gemini-flash-latest', contents=prompt)
            text = resp.text.strip()
            if text.startswith("```json"): text = text[7:-3]
            elif text.startswith("```"): text = text[3:-3]
            
            parsed = json.loads(text)
            if "description" in parsed:
                result["description"] = parsed["description"]
                result["is_ai_generated"] = True
                logger.info(f"AI Polished: {station}")
                
        except Exception as e:
            logger.error(f"LLM Gen failed: {e}")

    # Save to Cache
    NARRATIVES_CACHE[station] = result
    save_cache()
    return result

@app.get("/clusters", response_model=list[ClusterSummary])
def get_clusters():
    db_file = DATA_DIR / "clusters.parquet"
    if not db_file.exists(): return []
    
    query = f"""
        SELECT 
            cluster_id,
            COUNT(*) as station_count,
            AVG(n_bars) as avg_bars,
            FIRST(STATION) as example_station
        FROM '{db_file}'
        GROUP BY cluster_id
        ORDER BY cluster_id
    """
    results = db.query(query)
    
    response = []
    for row in results:
        cid = str(row['cluster_id'])
        persona = PERSONAS.get(cid, {"name": f"Cluster {cid}", "description": "", "tags": []})
        chart_data = CLUSTER_PROFILES.get(cid, [0.0]*24)[:24]
        
        response.append({
            **row,
            "persona": persona,
            "chart_data": chart_data
        })
    return response