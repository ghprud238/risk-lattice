#!/usr/bin/env bash
# RiskLattice Local Kubernetes Verification Test Script
# Tests the full end-to-end flow on local Kubernetes (Kind)

set -e

export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../../.." && pwd)"
CLUSTER_NAME="risk-lattice-local"
NAMESPACE="risk-lattice"

echo "=========================================================="
echo "  RiskLattice Local Kubernetes Verification Test Suite"
echo "=========================================================="

# 1. Check or Create Kind Cluster
if kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
  echo "[1/6] Kind cluster '${CLUSTER_NAME}' already active."
else
  echo "[1/6] Creating Kind cluster '${CLUSTER_NAME}'..."
  kind create cluster --config "$SCRIPT_DIR/kind-config.yaml"
fi

kubectl cluster-info --context "kind-${CLUSTER_NAME}"

# 2. Build Docker Images
echo "[2/6] Building backend and frontend Docker images..."
docker build -t risk-lattice-backend:latest -f "$ROOT_DIR/backend/Dockerfile" "$ROOT_DIR/backend"
docker build -t risk-lattice-frontend:latest --build-arg NEXT_PUBLIC_API_URL="http://localhost:5051" -f "$ROOT_DIR/frontend/Dockerfile" "$ROOT_DIR/frontend"

# 3. Load Images into Kind Cluster
echo "[3/6] Sideloading images into Kind cluster '${CLUSTER_NAME}'..."
kind load docker-image risk-lattice-backend:latest --name "${CLUSTER_NAME}"
kind load docker-image risk-lattice-frontend:latest --name "${CLUSTER_NAME}"

# 4. Apply Kubernetes Manifests
echo "[4/6] Applying Kubernetes manifests..."
kubectl apply -f "$SCRIPT_DIR/namespace.yaml"
kubectl apply -f "$SCRIPT_DIR/configmap.yaml"
kubectl apply -f "$SCRIPT_DIR/secret.yaml"
kubectl apply -f "$SCRIPT_DIR/backend.yaml"
kubectl apply -f "$SCRIPT_DIR/frontend.yaml"

# 5. Wait for Pods to Roll Out
echo "[5/6] Waiting for deployments to become ready in namespace '${NAMESPACE}'..."
kubectl rollout status deployment/risk-lattice-backend -n "${NAMESPACE}" --timeout=120s
kubectl rollout status deployment/risk-lattice-frontend -n "${NAMESPACE}" --timeout=120s

kubectl get pods,services -n "${NAMESPACE}"

# 6. Test Live Service Flows
echo "[6/6] Testing live application flow..."
BACKEND_POD=$(kubectl get pod -l app=risk-lattice-backend -n "${NAMESPACE}" -o jsonpath="{.items[0].metadata.name}")

# A. Backend Health Probe
echo " -> Testing Backend Health Check..."
HEALTH_RESP=$(kubectl exec -i "$BACKEND_POD" -n "${NAMESPACE}" -- curl -s http://127.0.0.1:5051/api/v1/health)
echo "    Response: $HEALTH_RESP"
if echo "$HEALTH_RESP" | grep -q '"status":"healthy"'; then
  echo "    [PASS] Backend health endpoint verified."
else
  echo "    [FAIL] Backend health check failed."
  exit 1
fi

# B. Proprietary Authentication Check
echo " -> Testing Proprietary Login Authentication..."
AUTH_RESP=$(kubectl exec -i "$BACKEND_POD" -n "${NAMESPACE}" -- curl -s -X POST http://127.0.0.1:5051/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"cro@risklattice.com","password":"cro123!"}')
echo "    Response: $(echo "$AUTH_RESP" | cut -c 1-120)..."
if echo "$AUTH_RESP" | grep -q '"role":"CHIEF_RISK_OFFICER"'; then
  echo "    [PASS] Proprietary login verified. JWT session created."
  TOKEN=$(echo "$AUTH_RESP" | grep -o '"token":"[^"]*' | cut -d'"' -f4)
else
  echo "    [FAIL] Authentication failed."
  exit 1
fi

# C. Quant Stress Test Simulation Flow
echo " -> Testing 4-Hop Contagion & Tail Risk Simulation..."
SIM_RESP=$(kubectl exec -i "$BACKEND_POD" -n "${NAMESPACE}" -- curl -s -X POST http://127.0.0.1:5051/api/v1/stress/simulate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"direct_impulses":{"FOUNDRY_TW":-0.70,"BALTIC_DRY":1.20},"scenario_name":"K8s Cluster E2E Disruption"}')
echo "    Response: $(echo "$SIM_RESP" | cut -c 1-140)..."
if echo "$SIM_RESP" | grep -q '"simulation"'; then
  echo "    [PASS] Multi-hop contagion simulation verified on Kubernetes."
else
  echo "    [FAIL] Simulation failed."
  exit 1
fi

# D. Frontend Service Check
echo " -> Testing Frontend Service..."
FRONTEND_POD=$(kubectl get pod -l app=risk-lattice-frontend -n "${NAMESPACE}" -o jsonpath="{.items[0].metadata.name}")
FRONTEND_RESP=$(kubectl exec -i "$FRONTEND_POD" -n "${NAMESPACE}" -- sh -c "wget -S --spider http://127.0.0.1:5050 2>&1 | grep 'HTTP/' || curl -sI http://127.0.0.1:5050/ | head -n 1")
echo "    Response: $FRONTEND_RESP"
if echo "$FRONTEND_RESP" | grep -q "200"; then
  echo "    [PASS] Frontend SSR service verified on Kubernetes."
else
  echo "    [FAIL] Frontend service check failed."
  exit 1
fi

echo ""
echo "=========================================================="
echo "  [SUCCESS] All Local Kubernetes Flows Verified!"
echo "  Cluster:  ${CLUSTER_NAME}"
echo "  Backend:  NodePort 30081 -> http://127.0.0.1:30081"
echo "  Frontend: NodePort 30080 -> http://127.0.0.1:30080"
echo "=========================================================="
