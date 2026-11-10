.PHONY: all seed test test-math test-llm test-api backend frontend dev build

all: dev

seed:
	cd backend && ../.venv/bin/python scripts/seed_data.py --verify

test:
	cd backend && ../.venv/bin/pytest tests/ -v

test-math:
	cd backend && ../.venv/bin/pytest tests/test_math.py -v

test-llm:
	cd backend && ../.venv/bin/pytest tests/test_llm.py -v

test-api:
	cd backend && ../.venv/bin/pytest tests/test_api.py -v

test-perf:
	cd backend && ../.venv/bin/pytest tests/test_performance_gate.py -s -v

backend:
	cd backend && ../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

frontend:
	cd frontend && npm run dev -- -p 3000

build:
	cd frontend && npm run build

dev:
	./start.sh
