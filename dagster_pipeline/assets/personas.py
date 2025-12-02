import polars as pl
import os
import json
from dagster import asset, Output
from google import genai
from google.genai import types
from .modeling import train_cluster_model
from .constants import PERSONAS_FILE

@asset(group_name="ai")
def generate_personas(train_cluster_model: pl.DataFrame):
    """
    Generates semantic personas using Google Gemini 2.0 Flash.
    Uses 'response_mime_type' to guarantee valid JSON output.
    """
    
    # 1. Calculate Cluster Statistics
    df = train_cluster_model
    stats = df.group_by("cluster_id").agg([
        pl.col("n_bars").mean().alias("avg_bars"),
        pl.col("n_offices").mean().alias("avg_offices"),
        pl.col("n_universities").mean().alias("avg_unis"),
        pl.col("STATION").first().alias("example_station")
    ])
    
    personas = {}
    
    # 2. Initialize Gemini Client
    api_key = os.getenv("GEMINI_API_KEY")
    
    if api_key:
        print("--- CALLING GOOGLE GEMINI 2.0 FLASH ---")
        client = genai.Client(api_key=api_key)
        
        for row in stats.iter_rows(named=True):
            cid = row['cluster_id']
            
            # Contextual Prompt
            prompt = f"""
            You are an urban mobility analyst. Analyze this NYC Subway Cluster based on its amenities:
            
            DATA:
            - Avg Nightlife Spots (Bars/Pubs) within 300m: {row['avg_bars']:.1f}
            - Avg Corporate Offices within 300m: {row['avg_offices']:.1f}
            - Avg Universities: {row['avg_unis']:.1f}
            - Representative Station: {row['example_station']}
            
            TASK:
            Create a persona for the typical rider here.
            - High Bars = "Nightlife/Social"
            - High Offices = "Corporate/Commuter"
            - High Unis = "Student/Academic"
            
            OUTPUT SCHEMA (JSON):
            {{
                "name": "Short Catchy Title",
                "description": "2 sentence backstory.",
                "tags": ["Tag1", "Tag2"]
            }}
            """
            
            try:
                # Native JSON Mode Request
                response = client.models.generate_content(
                    model='gemini-flash-latest', 
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type='application/json'
                    )
                )
                
                # Parse JSON
                personas[str(cid)] = json.loads(response.text)
                print(f"Generated Persona for Cluster {cid}: {personas[str(cid)]['name']}")
                
            except Exception as e:
                print(f"Gemini Error for cluster {cid}: {e}")
                personas[str(cid)] = {
                    "name": f"Cluster {cid}", 
                    "description": "AI Generation Failed", 
                    "tags": ["Error"]
                }
    else:
        print("!!! NO GEMINI_API_KEY FOUND - USING FALLBACK !!!")
        personas = {
            "0": {"name": "The Night Owls", "description": "Late night activity.", "tags": ["Nightlife"]},
            "1": {"name": "The Commuters", "description": "9-5 Warriors.", "tags": ["Corporate"]},
            "2": {"name": "The Students", "description": "Near universities.", "tags": ["Academic"]},
            "3": {"name": "The Tourists", "description": "Midtown hubs.", "tags": ["Tourism"]},
            "4": {"name": "The Locals", "description": "Residential areas.", "tags": ["Home"]}
        }
        
    # 3. Save to Disk
    print(f"--- SAVING PERSONAS TO {PERSONAS_FILE} ---")
    with open(PERSONAS_FILE, "w") as f:
        json.dump(personas, f, indent=2)
        
    return Output(personas, metadata={"file": PERSONAS_FILE})