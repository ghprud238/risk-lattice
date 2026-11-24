# RiskLattice Enterprise Debugging Guide

A comprehensive, field-tested troubleshooting and debugging guide for developers, quant engineers, and DevOps teams running **RiskLattice** across local development, Docker containers, and local Kubernetes clusters.

---

## 1. Fast Diagnostics & Health Verification

Before diving into deep code debugging, run the automated diagnostic scripts from the project root:

```bash
cd /Users/dpcubed/projects/risk-lattice

# 1. Environment & Database Integrity Check (0.08s)
.venv/bin/python backend/scripts/doctor.py

# 2. Ultra-Fast Offline Math Engine Smoke Test (0.12s)
.venv/bin/python backend/scripts/smoke_test.py

# 3. Privacy Firewall Red-Team Audit (Rule P-01)
.venv/bin/python backend/scripts/verify_privacy.py

# 4. Adversarial Chaos Engineering & Fuzzing Drills
.venv/bin/python backend/scripts/chaos_drill.py
```

---

## 2. Backend Debugging (FastAPI & Quantitative Engines)

### 2.1 One-Click VS Code / IDE Debugging (`.vscode/launch.json`)

RiskLattice includes pre-configured VS Code debug launch profiles. Press `F5` in VS Code or Cursor to trigger:
- **`Backend: FastAPI (Uvicorn Debug)`**: Boots Uvicorn on port `5051` with auto-reload, source maps, and `LOG_LEVEL=DEBUG`.
- **`Pytest: Current File`**: Runs the currently active test file with step-through breakpoints and `-s` (unmuted stdout).
- **`Script: Smoke Test`**: Executes the mathematical smoke test under the active debugger.
- **`Full Stack: Backend + Frontend`**: Concurrently boots both FastAPI (`5051`) and Next.js (`5050`) under unified debug sessions.

### 2.2 Interactive Command-Line Debugging (`pdb` / `breakpoint()`)

Insert standard Python breakpoints anywhere in `backend/app/`:

```python
# Place inside any endpoint or engine function:
breakpoint()
```

Run Uvicorn or Pytest with unbuffered output:

```bash
# Debug an endpoint interactively
PYTHONPATH=backend .venv/bin/python -m uvicorn app.main:app --port 5051 --reload

# Drop into PDB on test failure
.venv/bin/pytest backend/tests/test_math.py -v --pdb
```

### 2.3 Debugging Pure Compute Engines vs. Service Layer (ADR-002 AST Rule)

RiskLattice strictly separates pure mathematical compute functions from I/O:
- All code in `backend/app/engine/*.py` **must remain 100% deterministic** with zero imports of `duckdb`, `fastapi`, `requests`, `httpx`, or `litellm`.
- To verify that your code modifications have not violated AST isolation:

```bash
.venv/bin/pytest backend/tests/integration/test_boundary_and_engine.py -v
```

If an isolation error occurs, the test will print the exact disallowed AST import node and line number.

### 2.4 Inspecting the DuckDB Database Directly

RiskLattice persists graph snapshots, returns, users, and audit logs inside `backend/data/contagion.duckdb`:

```bash
# Open interactive DuckDB CLI
.venv/bin/python -c "
import duckdb
con = duckdb.connect('backend/data/contagion.duckdb')
print('=== TABLES ===')
print(con.execute('SHOW TABLES;').fetchall())
print('\n=== RECENT USERS ===')
print(con.execute('SELECT user_id, email, role, auth_provider FROM users LIMIT 5;').df())
print('\n=== ACTIVE SESSIONS ===')
print(con.execute('SELECT session_token, user_id, expires_at FROM user_sessions;').fetchall())
"
```

### 2.5 Real-Time Server-Sent Events (SSE) Stream Debugging

To monitor real-time Monte Carlo copula simulation steps or live AIS radar telemetry events directly from the terminal:

```bash
# Listen to live simulation SSE events
curl -N http://localhost:5051/api/v1/stream

# Trigger a test simulation in another terminal:
curl -X POST http://localhost:5051/api/v1/simulate \
  -H "Content-Type: application/json" \
  -d '{"initial_shock": {"FOUNDRY_TW": -0.70}}'
```

---

## 3. Frontend Debugging (Next.js 15 & React)

### 3.1 Next.js Development Server

Run the development server with clear terminal logging:

```bash
cd /Users/dpcubed/projects/risk-lattice/frontend
NEXT_PUBLIC_API_URL=http://localhost:5051 npm run dev -- -p 5050
```

### 3.2 Browser DevTools Inspection

1. **Authentication Token Inspection**:
   Open Chrome DevTools (`F12`) $\to$ **Application** $\to$ **Local Storage** $\to$ `http://localhost:5050`:
   - `risklattice_token`: Contains the cryptographically signed JWT session token.
   - `risklattice_user`: Contains the active user profile, assigned role (`CHIEF_RISK_OFFICER`, etc.), and permission matrix.
   - To clear session manually: `localStorage.clear()` in the Console, then refresh.

2. **Network Tab (SSE & REST)**:
   - Filter by `Fetch/XHR` to inspect REST calls (`/api/v1/auth/login`, `/api/v1/simulate`, `/api/v1/optimizer`).
   - Click on `/api/v1/stream` $\to$ **EventStream** tab to see streaming JSON frames in real time as the multi-hop wave propagates.

3. **Cytoscape Graph Visualizer Debugging**:
   - The interactive graph component is located at `frontend/src/components/CytoscapeGraph.tsx`.
   - To inspect loaded elements, open Console and check `window.__CY_INSTANCE__` (if debug mode enabled).
   - Ensure nodes with zero shock still render with default muted slate colors, and nodes with $S_v < -0.20$ highlight with red neon distress rings.

---

## 4. Local Kubernetes Debugging (Kind / Minikube)

### 4.1 Checking Cluster & Pod Status

```bash
export PATH="/opt/homebrew/bin:$PATH"

# 1. List all pods and services in risk-lattice namespace
kubectl get all -n risk-lattice

# 2. Describe failing or crashing pods
kubectl describe pod -l app=risk-lattice-backend -n risk-lattice

# 3. Stream live container logs
kubectl logs -f deployment/risk-lattice-backend -n risk-lattice
kubectl logs -f deployment/risk-lattice-frontend -n risk-lattice
```

### 4.2 Executing Inside Running Pods

```bash
# Open interactive shell in backend pod
kubectl exec -it deployment/risk-lattice-backend -n risk-lattice -- /bin/sh

# Test internal health check from within the pod
curl http://127.0.0.1:5051/api/v1/health
```

### 4.3 Direct Port-Forwarding (Bypassing Ingress / NodePort)

If NodePort `30080`/`30081` is blocked by local firewalls, use standard port-forwarding:

```bash
# Forward Backend to localhost:5051
kubectl port-forward svc/risk-lattice-backend 5051:5051 -n risk-lattice

# Forward Frontend to localhost:5050
kubectl port-forward svc/risk-lattice-frontend 5050:5050 -n risk-lattice
```

---

## 5. Common Troubleshooting Matrix

| Issue / Symptom | Root Cause | Immediate Fix |
| :--- | :--- | :--- |
| `duckdb.IOException: Could not set lock on file ... Database locked` | Another process holds an exclusive write lock on `contagion.duckdb`. | Run `lsof \| grep contagion.duckdb` and terminate the orphaned process, or restart Uvicorn. |
| `Address already in use: 5051` or `5050` | Orphaned Uvicorn or Next.js background process. | Run `lsof -ti:5051 \| xargs kill -9` and `lsof -ti:5050 \| xargs kill -9`. |
| `401 Unauthorized: Invalid or expired session token` | Session token in `localStorage` expired or server restart wiped cache. | Click **Log Out** on the login screen or run `localStorage.clear()` in browser console. Use pre-seeded credentials `cro@risklattice.com` / `cro123!`. |
| `Failed to connect to Docker daemon` | Docker Desktop is not running on macOS. | Run `open -a Docker` and wait 10 seconds for `docker ps` to return ready. |
| `Kind node image not found` | Offline network during first cluster creation. | Ensure internet connection is active so `kindest/node:v1.34.0` can download once. |
| `Copula simulation covariance matrix is singular` | Redundant collinear asset returns. | Higham (2002) near-PSD eigenvalue projection automatically engages in `app.engine.risk_metrics.py`. Check logs for `[PSD_REPAIR]` notice. |
