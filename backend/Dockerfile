FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the API code
COPY app ./app

# COPY THE DATA from the pipeline output
# We create a 'data' folder in the container and put our processed files there
COPY ../dagster_pipeline/data/processed/clusters.parquet ./data/clusters.parquet
COPY ../dagster_pipeline/data/processed/personas.json ./data/personas.json

# Expose port
EXPOSE 8000

# Run the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]