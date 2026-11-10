.PHONY: all seed test test-all test-math test-llm test-api test-perf unit integration doctor smoke privacy backup dev backend frontend build

all: dev

doctor:
	cd backend && ../.venv/bin/python scripts/doctor.py

smoke:
	cd backend && ../.venv/bin/python scripts/smoke_test.py

privacy:
	cd backend && ../.venv/bin/python scripts/verify_privacy.py

seed:
	cd backend && ../.venv/bin/python scripts/seed_data.py --verify

backup:
	cd backend && ../.venv/bin/python scripts/backup.py

test:
	cd backend && ../.venv/bin/pytest tests/unit/ tests/integration/ tests/test_math.py tests/test_llm.py tests/test_api.py -v

unit:
	cd backend && ../.venv/bin/pytest tests/unit/ -v

integration:
	cd backend && ../.venv/bin/pytest tests/integration/ -v

test-math:
	cd backend && ../.venv/bin/pytest tests/test_math.py -v

test-llm:
	cd backend && ../.venv/bin/pytest tests/test_llm.py -v

test-api:
	cd backend && ../.venv/bin/pytest tests/test_api.py tests/integration/test_section12_api.py -v

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
