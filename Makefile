# RiskLattice Master Makefile
# Institutional-grade management targets for developers, quant researchers, and DevOps

SHELL := /bin/bash
.DEFAULT_GOAL := help
PYTHON := .venv/bin/python
PYTEST := .venv/bin/pytest
KUBECTL := export PATH="/opt/homebrew/bin:/usr/local/bin:$$PATH" && kubectl
KIND := export PATH="/opt/homebrew/bin:/usr/local/bin:$$PATH" && kind

.PHONY: help setup doctor smoke privacy seed backup test unit integration chaos \
        synthetic test-ast test-perf test-all generate-fixtures dev backend frontend \
        mobile build docker-build docker-up docker-down docker-logs k8s-up k8s-down \
        k8s-test k8s-status k8s-logs-backend k8s-logs-frontend k8s-port-forward clean

# =============================================================================
# 1. HELP & DISCOVERY
# =============================================================================

help: ## Show this interactive help menu
	@echo ""
	@echo "  ============================================================================"
	@echo "    RiskLattice • Cross-Asset Macro Contagion Stress-Testing Platform"
	@echo "  ============================================================================"
	@echo ""
	@echo "  Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "    \033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@echo ""

# =============================================================================
# 2. SETUP & ENVIRONMENT
# =============================================================================

setup: ## Install backend and frontend dependencies
	@echo "==> Setting up Python virtual environment..."
	@uv pip install -e backend/
	@uv pip install pyjwt bcrypt
	@echo "==> Installing frontend dependencies..."
	@cd frontend && npm install
	@echo "==> Setup complete!"

doctor: ## Run system diagnostic & environment doctor
	cd backend && ../$(PYTHON) scripts/doctor.py

smoke: ## Run ultra-fast offline math & copula smoke test (0.12s)
	cd backend && ../$(PYTHON) scripts/smoke_test.py

privacy: ## Run Rule P-01 privacy firewall red-team audit
	cd backend && ../$(PYTHON) scripts/verify_privacy.py

seed: ## Seed DuckDB database with graph nodes, edges, returns, and institutional users
	cd backend && ../$(PYTHON) scripts/seed_data.py --verify

backup: ## Create an immutable snapshot backup of DuckDB and Parquet datasets
	cd backend && ../$(PYTHON) scripts/backup.py

# =============================================================================
# 3. AUTOMATED TESTING SUITES
# =============================================================================

test: ## Run the entire test suite (116+ tests)
	$(PYTEST) backend/tests/ -v

unit: ## Run unit tests (engines, auth, fixtures)
	$(PYTEST) backend/tests/unit/ -v

integration: ## Run integration tests (APIs, boundary, expansion services)
	$(PYTEST) backend/tests/integration/ -v

chaos: ## Run adversarial chaos fuzzing suite & gateway circuit breaker tests
	$(PYTEST) backend/tests/chaos/ -v
	cd backend && ../$(PYTHON) scripts/chaos_drill.py

synthetic: ## Validate all 9 machine-readable synthetic benchmark fixtures
	$(PYTEST) backend/tests/integration/test_synthetic_data_fixtures.py -v

test-ast: ## Verify ADR-002 AST import isolation boundary (zero I/O in engines)
	$(PYTEST) backend/tests/integration/test_boundary_and_engine.py -v

test-perf: ## Validate sub-2.0s performance gate under high-dimensional load
	$(PYTEST) backend/tests/test_performance_gate.py -s -v

test-all: doctor smoke privacy test-ast synthetic test ## Run all diagnostic gates and full test suite

generate-fixtures: ## Regenerate all machine-readable synthetic test data in docs/synthetic_test_data/
	$(PYTHON) docs/synthetic_test_data/generate_synthetic_test_data.py

# =============================================================================
# 4. APPLICATION SERVICES (LOCAL DEV)
# =============================================================================

dev: ## Launch both backend (port 5051) and frontend (port 5050) concurrently
	./start.sh

backend: ## Run FastAPI backend with Uvicorn auto-reload on port 5051
	cd backend && ../$(PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 5051 --reload

frontend: ## Run Next.js 15 frontend on port 5050
	cd frontend && NEXT_PUBLIC_API_URL=http://localhost:5051 npm run dev -- -p 5050

mobile: ## Start Expo development bundler for React Native mobile application
	cd mobile && npm start

build: ## Build Next.js production bundle and verify TypeScript types
	cd frontend && npm run build

# =============================================================================
# 5. DOCKER COMPOSE
# =============================================================================

docker-build: ## Build Docker images for backend and frontend
	docker compose build

docker-up: ## Start backend and frontend containers in background
	docker compose up -d

docker-down: ## Stop and remove running containers
	docker compose down

docker-logs: ## Follow live logs from all running Docker containers
	docker compose logs -f

# =============================================================================
# 6. LOCAL KUBERNETES (KIND / MINIKUBE)
# =============================================================================

k8s-up: ## Create local Kind cluster and deploy RiskLattice manifests
	@$(KIND) create cluster --config deploy/k8s/local/kind-config.yaml || true
	@$(KUBECTL) apply -f deploy/k8s/local/namespace.yaml
	@$(KUBECTL) apply -f deploy/k8s/local/configmap.yaml
	@$(KUBECTL) apply -f deploy/k8s/local/secret.yaml
	@$(KUBECTL) apply -f deploy/k8s/local/backend.yaml
	@$(KUBECTL) apply -f deploy/k8s/local/frontend.yaml

k8s-down: ## Delete the local Kind cluster and purge Kubernetes resources
	@$(KIND) delete cluster --name risk-lattice-local

k8s-test: ## Run automated end-to-end flow test against local Kubernetes cluster
	./deploy/k8s/local/k8s-test.sh

k8s-status: ## Show status of all pods, services, and deployments in risk-lattice namespace
	@$(KUBECTL) get all -n risk-lattice

k8s-logs-backend: ## Stream live logs from backend deployment in Kubernetes
	@$(KUBECTL) logs -f deployment/risk-lattice-backend -n risk-lattice

k8s-logs-frontend: ## Stream live logs from frontend deployment in Kubernetes
	@$(KUBECTL) logs -f deployment/risk-lattice-frontend -n risk-lattice

k8s-port-forward: ## Forward ports 5051 (backend) and 5050 (frontend) to localhost
	@echo "Forwarding Backend on http://localhost:5051 and Frontend on http://localhost:5050..."
	@$(KUBECTL) port-forward svc/risk-lattice-backend 5051:5051 -n risk-lattice & \
	 $(KUBECTL) port-forward svc/risk-lattice-frontend 5050:5050 -n risk-lattice

# =============================================================================
# 7. CLEAN & HYGIENE
# =============================================================================

clean: ## Clean cached bytecode, temporary test artifacts, and build directories
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf frontend/.next
	rm -rf mobile/.expo
	@echo "Cleaned cache and build artifacts."
