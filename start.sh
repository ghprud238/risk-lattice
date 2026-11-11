#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "================================================================="
echo " Starting RiskLattice: Cross-Asset Macro Contagion Stress-Tester"
echo "================================================================="

# Check DuckDB seed
if [ ! -f "backend/data/contagion.duckdb" ]; then
    echo "Seeding synthetic dataset (50 canonical nodes, 2520 trading days)..."
    .venv/bin/python backend/scripts/seed_data.py --verify
fi

# Detect available ports (defaults to 5051 for backend, 5050 for frontend)
BACKEND_PORT=${PORT:-5051}
if lsof -i :$BACKEND_PORT >/dev/null 2>&1; then
    echo "⚠️  Port $BACKEND_PORT is occupied. Switching backend to port 8051..."
    BACKEND_PORT=8051
fi

FRONTEND_PORT=${FRONTEND_PORT:-5050}
if lsof -i :$FRONTEND_PORT >/dev/null 2>&1; then
    echo "⚠️  Port $FRONTEND_PORT is occupied. Switching frontend to port 8050..."
    FRONTEND_PORT=8050
fi

# Trap SIGINT to kill background servers on exit
trap 'kill $(jobs -p) 2>/dev/null || true; exit 0' SIGINT SIGTERM EXIT

echo "Starting FastAPI Backend on http://localhost:$BACKEND_PORT..."
cd backend
../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT &
BACKEND_PID=$!
cd ..

# Wait for backend health
sleep 1.5

echo "Starting Next.js Frontend on http://localhost:$FRONTEND_PORT..."
cd frontend
NEXT_PUBLIC_API_URL="http://localhost:$BACKEND_PORT" npm run dev -- -p $FRONTEND_PORT &
FRONTEND_PID=$!
cd ..

echo "================================================================="
echo " RiskLattice is RUNNING!"
echo " Frontend UI: http://localhost:$FRONTEND_PORT"
echo " Backend API: http://localhost:$BACKEND_PORT/docs"
echo " Press Ctrl+C to stop both servers."
echo "================================================================="

wait
