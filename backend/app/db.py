import duckdb
import logging
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_data(sql_query: str, params: tuple = ()):
    """
    Executes a query using a fresh connection per request.
    This guarantees thread safety and prevents DuckDB locks.
    """
    conn = None
    try:
        # Lightweight in-memory connection
        conn = duckdb.connect(database=':memory:')
        
        # Attempt 1: Fast dataframe Conversion
        try:
            df = conn.execute(sql_query, params).df()
            df = df.replace([np.inf, -np.inf], 0)
            df = df.where(pd.notnull(df), None)
            
            return df.to_dict(orient="records")
            
        except Exception as pd_error:
            logger.warning(f"Pandas optimization failed: {pd_error}. Switching to fallback.")
            
            # Attempt 2: Slow Python Object Conversion (Robust Fallback)
            cursor = conn.execute(sql_query, params)
            rows = cursor.fetchall()
            
            if not rows:
                return []
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in rows]

    except Exception as e:
        logger.error(f"DB Query Failed: {e}")
        return []
        
    finally:
        if conn:
            conn.close()

# Export alias for compatibility
query = get_data