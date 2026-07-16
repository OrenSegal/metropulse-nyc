# Build context is the repo root (see docker-compose.yml) so this can read
# the root requirements.txt without a path-traversal COPY, which Docker
# doesn't allow. Pipeline output (clusters.parquet, personas.json, ...) is
# NOT baked into the image — it's mounted at runtime from backend/data, same
# artifact dev.sh stages locally, so the container always serves current data
# instead of whatever was on disk at image-build time.
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]