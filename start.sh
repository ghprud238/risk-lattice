#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "================================================================="
echo " Starting ContagionGraph: Cross-Asset Macro Contagion Stress-Tester"
echo "================================================================="

# Check DuckDB seed
if [ ! -f "backend/data/contagion.duckdb" ]; then
    echo "Seeding synthetic dataset (50 canonical nodes, 2520 trading days)..."
    .venv/bin/python backend/scripts/seed_data.py --verify
fi

# Trap SIGINT to kill background servers on exit
trap 'kill $(jobs -p) 2>/dev/null || true; exit 0' SIGINT SIGTERM EXIT

echo "Starting FastAPI Backend on http://localhost:8000..."
cd backend
../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend health
sleep 1.5

echo "Starting Next.js Frontend on http://localhost:3000..."
cd frontend
npm run dev -- -p 3000 &
FRONTEND_PID=$!
cd ..

echo "================================================================="
echo " ContagionGraph is RUNNING!"
echo " Frontend UI: http://localhost:3000"
echo " Backend API: http://localhost:8000/docs"
echo " Press Ctrl+C to stop both servers."
echo "================================================================="

wait
