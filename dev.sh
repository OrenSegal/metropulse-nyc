#!/bin/bash

# 1. CLEANUP PREVIOUS RUNS
echo "🧹 Cleaning up old processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null

# Function to kill processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down MetroPulse..."
    kill $(jobs -p) 2>/dev/null
    exit
}

trap cleanup SIGINT

echo "🚀 Starting MetroPulse NYC..."

# 2. Check for Data
if [ ! -f "backend/data/clusters.parquet" ]; then
    echo "⚠️  Data missing in backend! Copying from pipeline..."
    mkdir -p backend/data
    cp dagster_pipeline/data/processed/* backend/data/
fi

# 3. Start Backend (Background)
echo "🐍 Starting Backend (Port 8000)..."
source venv/bin/activate

# FIX: Ensure dependencies are installed ---
echo "📦 Checking dependencies..."
pip install -r backend/requirements.txt > /dev/null 2>&1
# -------------------------------------------

cd backend
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo "⏳ Waiting for Backend to initialize..."
sleep 5

# 4. Start Frontend
echo "⚛️  Starting Frontend (Port 5173)..."
cd frontend
npm run dev

wait