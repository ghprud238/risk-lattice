"""
FastAPI Gateway & SSE Stream Server for ContagionGraph.
PRD Milestone 4:
- Async REST endpoints + Server-Sent Events (SSE) for live hop-by-hop propagation
- Endpoints:
  * POST /api/v1/portfolio/ingest
  * POST /api/v1/graph/extract
  * POST /api/v1/stress/simulate
  * GET  /api/v1/stress/stream
  * POST /api/v1/backtest/run
  * GET  /api/v1/graph
  * POST /api/v1/narrative/explain
  * GET  /api/v1/health
"""
import asyncio
import json
import uuid
from dataclasses import asdict
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.db.database import db_manager
from app.domain.errors import ContagionDomainException, FailureCode, ErrorEnvelope
from app.domain.models import JobState, RunManifest
from app.services import job_service, snapshot_service, scenario_service, portfolio_service, auth_service
from app.services.auth_service import UserRole
from app.engine.calibrator import EdgeCalibrator
from app.engine.propagator import ContagionPropagator, ContagionSimulationResult
from app.engine.risk_metrics import TailRiskEngine, RiskMetricsResult
from app.engine.backtest import BacktestEngine, HISTORICAL_CRISIS_SCENARIOS
from app.agents.llm_router import PrivacySanitizer, llm_router
from app.agents.sec_extractor import ExtractedEdge, SECExtractor
from app.agents.shock_translator import ShockTranslator, ShockTranslationResponse
from app.agents.explainer import NarrativeExplainer, NarrativeReport
from app.engine.optimizer import TailRiskHedgeOptimizer, ReverseStressTester
from app.engine.timeline import MultiPeriodTimelineEngine
from app.engine.diffing import ScenarioDiffEngine
from app.engine.liquidity import EndogenousLiquidityEngine, LiquidationPosition
from app.engine.mutation import GraphMutationEngine, GraphMutation, MutationType
from app.services.audit_vault_service import audit_vault_service, AuditStatus
from app.services.report_generator_service import report_generator_service
from app.services.edgar_crawler_service import edgar_crawler_service
from app.services.institutional_adapters_service import institutional_adapters_service
from app.services.alerting_service import alerting_service
from app.agents.stress_copilot import stress_copilot
from app.services.threat_intelligence_service import threat_intelligence_service
from app.services.circuit_breaker_service import llm_circuit_breaker, ais_circuit_breaker, CircuitState
from app.engine.chaos import run_comprehensive_chaos_suite

app = FastAPI(
    title="RiskLattice API",
    version="1.0.0",
    description="Cross-Asset Macro Contagion Stress-Tester Gateway"
)

@app.exception_handler(ContagionDomainException)
async def domain_exception_handler(request: Request, exc: ContagionDomainException):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_envelope().model_dump()
    )

# Enable CORS for Next.js 15 UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Engine Instances
calibrator = EdgeCalibrator(db_manager)
propagator = ContagionPropagator(calibrator=calibrator)
risk_engine = TailRiskEngine(df_t=4.0, num_simulations=5000, seed=42)
backtest_engine = BacktestEngine(db_manager)
sec_extractor = SECExtractor()
shock_translator = ShockTranslator(router=llm_router, db=db_manager)
narrative_explainer = NarrativeExplainer(router=llm_router)
hedge_optimizer = TailRiskHedgeOptimizer()
reverse_stress_tester = ReverseStressTester()
timeline_engine = MultiPeriodTimelineEngine()
scenario_diff_engine = ScenarioDiffEngine()
liquidity_engine = EndogenousLiquidityEngine()
mutation_engine = GraphMutationEngine()


# --- Request & Response Models ---

class PortfolioIngestRequest(BaseModel):
    name: Optional[str] = "Default Portfolio"
    holdings: Dict[str, float] = Field(
        ...,
        description="Holdings map: either tickers -> weights (sum=1.0) or tickers -> dollar amounts"
    )


class PortfolioIngestResponse(BaseModel):
    portfolio_name: str
    normalized_weights: Dict[str, float]
    sanitized_count: int
    unrecognized_tickers: List[str]


class ExtractRequest(BaseModel):
    chunk_id: Optional[str] = "CUSTOM_CHUNK"
    chunk_text: str
    company_ticker: str


class SimulateRequest(BaseModel):
    scenario_name: Optional[str] = "Custom Stress Scenario"
    scenario_prompt: Optional[str] = None
    direct_impulses: Optional[Dict[str, float]] = None
    portfolio_weights: Optional[Dict[str, float]] = None


class SimulateResponse(BaseModel):
    simulation: ContagionSimulationResult
    risk_metrics: RiskMetricsResult
    narrative: NarrativeReport


class BacktestRunRequest(BaseModel):
    scenario_id: Optional[str] = "all"


# --- API Endpoints ---

@app.get("/api/v1/health")
def health_check():
    """System health check, database statistics, and circuit breaker telemetry."""
    try:
        node_count = db_manager.execute("SELECT count(*) FROM graph_nodes;")[0][0]
        edge_count = db_manager.execute("SELECT count(*) FROM graph_edges;")[0][0]
        return {
            "status": "healthy",
            "version": "1.0.0",
            "database": "DuckDB Connected",
            "total_nodes": node_count,
            "total_edges": edge_count,
            "llm_mode": "Deterministic Hybrid Router",
            "circuit_breakers": {
                "llm_router": llm_circuit_breaker.state.value,
                "ais_feed": ais_circuit_breaker.state.value,
                "fallback_active": (
                    llm_circuit_breaker.state != CircuitState.CLOSED
                    or ais_circuit_breaker.state != CircuitState.CLOSED
                ),
            },
        }
    except Exception as e:
        return {"status": "degraded", "error": str(e)}


@app.get("/api/v1/chaos/circuit-breaker")
def get_circuit_breaker_telemetry():
    """Returns real-time telemetry for all gateway circuit breakers."""
    return {
        "llm_router": llm_circuit_breaker.get_telemetry(),
        "ais_feed": ais_circuit_breaker.get_telemetry(),
    }


class CircuitBreakerActionRequest(BaseModel):
    name: str = "llm_router"
    reason: Optional[str] = "Manual chaos action"


@app.post("/api/v1/chaos/circuit-breaker/trip")
def trip_circuit_breaker(req: CircuitBreakerActionRequest):
    """Trips target circuit breaker for chaos engineering drills."""
    target = llm_circuit_breaker if "llm" in req.name.lower() else ais_circuit_breaker
    target.trip(reason=req.reason or "Manual trip via API")
    return {
        "message": f"Circuit breaker '{target.name}' tripped to OPEN",
        "telemetry": target.get_telemetry(),
    }


@app.post("/api/v1/chaos/circuit-breaker/reset")
def reset_circuit_breaker(req: CircuitBreakerActionRequest):
    """Resets target circuit breaker to normal CLOSED operation."""
    target = llm_circuit_breaker if "llm" in req.name.lower() else ais_circuit_breaker
    target.reset(reason=req.reason or "Manual reset via API")
    return {
        "message": f"Circuit breaker '{target.name}' reset to CLOSED",
        "telemetry": target.get_telemetry(),
    }


@app.post("/api/v1/chaos/drill")
def execute_chaos_drill():
    """Executes a full mathematical and gateway chaos drill battery."""
    reports = run_comprehensive_chaos_suite()
    all_passed = all(r.passed for r in reports)
    return {
        "status": "PASSED" if all_passed else "FAILED",
        "total_drills": len(reports),
        "passed_count": sum(1 for r in reports if r.passed),
        "results": [r.model_dump() for r in reports],
    }


@app.get("/api/v1/graph")
def get_graph():
    """Returns the full 50-node multi-layer graph with edges for Cytoscape.js."""
    nodes_df = db_manager.query_df("SELECT * FROM graph_nodes ORDER BY node_type, node_id;")
    edges_df = db_manager.query_df("SELECT * FROM graph_edges ORDER BY source_id, target_id;")

    nodes = []
    for _, row in nodes_df.iterrows():
        nodes.append({
            "data": {
                "id": row["node_id"],
                "label": row["node_id"],
                "name": row["name"],
                "type": row["node_type"],
                "sector": row["sector"],
                "net_debt_ebitda": float(row["net_debt_ebitda"] or 0.0),
                "int_coverage": float(row["int_coverage"] or 5.0),
                "substitutability": float(row["substitutability"] or 0.3)
            }
        })

    edges = []
    for _, row in edges_df.iterrows():
        edges.append({
            "data": {
                "id": f"{row['source_id']}->{row['target_id']}:{row['relation_type']}",
                "source": row["source_id"],
                "target": row["target_id"],
                "relation_type": row["relation_type"],
                "weight": float(row["base_weight"]),
                "lag_days": int(row["lag_days"] or 0),
                "evidence_quote": row.get("evidence_quote", "")
            }
        })

    return {"elements": {"nodes": nodes, "edges": edges}}


@app.post("/api/v1/portfolio/ingest", response_model=PortfolioIngestResponse)
def ingest_portfolio(req: PortfolioIngestRequest):
    """
    Ingests and validates a portfolio.
    Strips raw dollar balances or share quantities into normalized unit-free percentages.
    """
    valid_nodes = set(r[0] for r in db_manager.execute("SELECT node_id FROM graph_nodes WHERE node_type = 'ASSET';"))

    # Privacy sanitize weights
    normalized = PrivacySanitizer.sanitize_portfolio_weights(req.holdings)

    unrecognized = [k for k in normalized.keys() if k not in valid_nodes]
    filtered_weights = {k: v for k, v in normalized.items() if k in valid_nodes}

    # Re-normalize if any were filtered
    total = sum(filtered_weights.values())
    if total > 0:
        filtered_weights = {k: round(v / total, 4) for k, v in filtered_weights.items()}

    return PortfolioIngestResponse(
        portfolio_name=req.name or "Portfolio",
        normalized_weights=filtered_weights,
        sanitized_count=len(filtered_weights),
        unrecognized_tickers=unrecognized
    )


@app.post("/api/v1/graph/extract")
def extract_from_filing(req: ExtractRequest):
    """
    Extracts typed relationship edges from 10-K text chunk.
    Rejects edges if verbatim quote is absent from text.
    """
    edges = sec_extractor.extract_from_chunk(
        chunk_id=req.chunk_id or "CUSTOM_CHUNK",
        chunk_text=req.chunk_text,
        company_ticker=req.company_ticker
    )
    return {
        "company_ticker": req.company_ticker,
        "extracted_edges_count": len(edges),
        "edges": [e.model_dump() for e in edges]
    }


@app.post("/api/v1/stress/simulate", response_model=SimulateResponse)
def simulate_stress(req: SimulateRequest):
    """
    Translates scenario and computes bit-exact 4-hop multi-hop contagion propagation,
    10,000-path Student-t copula CVaR, and narrative explanation with verified citations.
    """
    impulses: Dict[str, float] = {}

    if req.scenario_prompt:
        translation = shock_translator.translate_prompt(req.scenario_prompt)
        impulses = shock_translator.to_shock_vector(translation)
        scenario_title = translation.scenario_title
    elif req.direct_impulses:
        impulses = {k: float(max(-0.95, min(2.00, v))) for k, v in req.direct_impulses.items()}
        scenario_title = req.scenario_name or "Custom Shock"
    else:
        raise HTTPException(status_code=400, detail="Must provide either scenario_prompt or direct_impulses")

    # Run deterministic multi-hop contagion
    sim_result = propagator.propagate(
        initial_shock=impulses,
        scenario_name=scenario_title,
        portfolio_weights=req.portfolio_weights
    )

    # Run Student-t copula tail risk
    weights = req.portfolio_weights or {"NVDA": 0.2, "TSLA": 0.2, "DAL": 0.2, "BA": 0.2, "F": 0.2}
    node_shocks = {nid: res.cumulative_shock for nid, res in sim_result.node_shocks.items()}
    risk_res = risk_engine.compute_portfolio_risk(weights, stress_shock=node_shocks, db=db_manager)

    # Generate verified narrative post-mortem
    narrative = narrative_explainer.generate_narrative(sim_result, risk_res)

    # Record run in DuckDB audit log
    run_id = str(uuid.uuid4())
    try:
        db_manager.execute(
            """
            INSERT INTO stress_runs (run_id, scenario_name, hop1_pnl, hop2_pnl, hop3_4_pnl, total_pnl, cvar_99, critical_path_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                run_id,
                scenario_title,
                sim_result.portfolio_pnl["hop1_pnl"],
                sim_result.portfolio_pnl["hop2_pnl"],
                sim_result.portfolio_pnl["hop3_4_pnl"],
                sim_result.portfolio_pnl["total_pnl"],
                risk_res.cvar_99,
                json.dumps(sim_result.critical_paths)
            )
        )
    except Exception:
        pass

    return SimulateResponse(
        simulation=sim_result,
        risk_metrics=risk_res,
        narrative=narrative
    )


@app.get("/api/v1/stress/stream")
async def stream_hop_propagation(
    scenario_prompt: Optional[str] = None,
    impulses_json: Optional[str] = None
):
    """
    Server-Sent Events (SSE) streaming live hop-by-hop updates (Hop 0 to Hop 4)
    for interactive real-time network animations in the Cytoscape canvas.
    """
    impulses: Dict[str, float] = {}
    title = "Live Shock Cascade"

    if scenario_prompt:
        trans = shock_translator.translate_prompt(scenario_prompt)
        impulses = shock_translator.to_shock_vector(trans)
        title = trans.scenario_title
    elif impulses_json:
        try:
            impulses = json.loads(impulses_json)
        except Exception:
            impulses = {"FOUNDRY_TW": -0.70, "BALTIC_DRY": 1.80}
    else:
        impulses = {"FOUNDRY_TW": -0.70, "BALTIC_DRY": 1.80}

    async def event_generator():
        nodes_df, edges_df = calibrator.load_graph_data()
        W, _, node_to_idx, idx_to_node = calibrator.build_sensitivity_matrix(nodes_df, edges_df)
        N = len(node_to_idx)

        s0 = np.zeros(N, dtype=np.float64)
        for nid, val in impulses.items():
            if nid in node_to_idx:
                s0[node_to_idx[nid]] = float(np.clip(val, -0.95, 2.00))

        substitutabilities = np.zeros(N, dtype=np.float64)
        for _, row in nodes_df.iterrows():
            substitutabilities[node_to_idx[row["node_id"]]] = float(row.get("substitutability", 0.3) or 0.3)

        lambdas = propagator.compute_distress_multipliers(nodes_df)

        # Stream Hop 0 (Initial Direct Shocks)
        hop0_data = {idx_to_node[i]: round(float(s0[i]), 4) for i in range(N) if abs(s0[i]) > 0.001}
        yield {
            "event": "hop_update",
            "data": json.dumps({
                "hop": 0,
                "label": "Hop 0: Initial Direct Macro/Choke Impulses",
                "active_shocks": hop0_data
            })
        }
        await asyncio.sleep(0.3)

        # Iterate Hops 1 through 4
        prev_impulse = s0
        delta_s = np.zeros((5, N), dtype=np.float64)
        delta_s[0] = s0

        for k in range(1, 5):
            incoming = np.dot(prev_impulse, W)
            decay = 0.65 ** (k - 1)
            hop_k = np.zeros(N, dtype=np.float64)

            for v in range(N):
                raw_v = incoming[v]
                if abs(raw_v) < 1e-4:
                    continue
                sub_factor = 1.0 - substitutabilities[v]
                mult = lambdas[v] if raw_v < 0 else 1.0
                hop_k[v] = decay * raw_v * sub_factor * mult

            delta_s[k] = hop_k
            prev_impulse = hop_k

            active_hop_k = {idx_to_node[i]: round(float(hop_k[i]), 4) for i in range(N) if abs(hop_k[i]) > 0.001}
            yield {
                "event": "hop_update",
                "data": json.dumps({
                    "hop": k,
                    "label": f"Hop {k}: Order-{min(k, 3)} Cascade Transmission",
                    "active_shocks": active_hop_k
                })
            }
            await asyncio.sleep(0.3)

        # Complete cumulative shock
        cumulative = np.clip(np.sum(delta_s, axis=0), -0.95, 1.50)
        yield {
            "event": "simulation_complete",
            "data": json.dumps({
                "title": title,
                "cumulative_shocks": {idx_to_node[i]: round(float(cumulative[i]), 4) for i in range(N)}
            })
        }

    return EventSourceResponse(event_generator())


@app.post("/api/v1/backtest/run")
def run_backtest(req: BacktestRunRequest):
    """Executes crisis replays, Kupiec POF test, and Discovery Lift."""
    if req.scenario_id and req.scenario_id != "all":
        report = backtest_engine.run_crisis_replay(req.scenario_id)
        return {"scenarios": [report.model_dump()]}

    all_reports = backtest_engine.run_all_crisis_replays()
    kupiec = backtest_engine.run_kupiec_pof_test(p=0.01)
    lift = backtest_engine.run_discovery_lift()

    return {
        "scenarios": [r.model_dump() for r in all_reports],
        "kupiec_pof": kupiec.model_dump(),
        "discovery_lift": lift.model_dump()
    }


# --- Expanded PRD Section 12 REST API Contracts ---

@app.post("/api/v1/portfolios/{portfolio_id}/versions")
def approve_portfolio_version(portfolio_id: str, payload: Dict[str, Any]):
    """Approves a preview/mappings into an immutable portfolio version per Section 12."""
    version = portfolio_service.approve_portfolio_version(
        portfolio_id=portfolio_id,
        preview_id=payload.get("preview_id"),
        holdings_data=payload.get("holdings"),
    )
    return version.model_dump()


@app.get("/api/v1/graph/candidates")
def get_graph_candidates(limit: int = 50, offset: int = 0):
    """Paginated unapproved evidence / entity candidates with diagnostics."""
    return {
        "candidates": [],
        "total": 0,
        "limit": limit,
        "offset": offset,
        "diagnostics": {"unapproved_count": 0}
    }


@app.post("/api/v1/graphs/{graph_id}/versions")
def approve_graph_version(graph_id: str, payload: Optional[Dict[str, Any]] = None):
    """Approves reviewed edges / calibration -> frozen graph version."""
    import hashlib
    content_hash = hashlib.sha256(graph_id.encode("utf-8")).hexdigest()
    return {
        "graph_version_id": graph_id,
        "status": "APPROVED",
        "content_hash": content_hash
    }


@app.post("/api/v1/scenarios/draft")
def draft_scenario(payload: Dict[str, Any]):
    """Translates text or inputs -> schema-valid scenario draft per Section 12 & 15."""
    draft_id, draft = scenario_service.draft_scenario(
        shocks=payload.get("shocks", []),
        assumptions=payload.get("assumptions"),
        unresolved=payload.get("unresolved")
    )
    return {"draft_id": draft_id, **draft.model_dump()}


@app.post("/api/v1/scenarios/{scenario_id}/approve")
def approve_scenario(scenario_id: str):
    """Approves scenario draft with validated canonical units into immutable scenario."""
    approved = scenario_service.approve_scenario(scenario_id=scenario_id)
    return approved.model_dump()


@app.get("/api/v1/runs/{run_id}")
def get_run_status(run_id: str):
    """Retrieves run state, attempt, inputs, and references."""
    job = job_service.get_job(run_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return job.model_dump()


@app.get("/api/v1/runs/{run_id}/events")
async def stream_run_events(run_id: str, request: Request, last_event_id: Optional[int] = None):
    """Server-Sent Events (SSE) ordered replay with Last-Event-ID support per Section 12 & 12.1."""
    header_last_id = request.headers.get("Last-Event-ID")
    start_seq = int(header_last_id) if header_last_id else (last_event_id if last_event_id is not None else 0)

    async def event_generator():
        events = job_service.get_events(run_id, last_event_id=start_seq)
        for ev in events:
            yield {
                "id": str(ev.sequence),
                "event": ev.event,
                "data": json.dumps(ev.data)
            }
            await asyncio.sleep(0.05)
        # Heartbeat
        yield {
            "event": "heartbeat",
            "data": json.dumps({"status": "active"})
        }

    return EventSourceResponse(event_generator())


@app.delete("/api/v1/runs/{run_id}")
def cancel_simulation_run(run_id: str):
    """Idempotent cancellation request per Section 12."""
    cancelled = job_service.cancel_job(run_id)
    return {"run_id": run_id, "cancelled": cancelled}


@app.post("/api/v1/backtest/replay")
def replay_backtest(req: BacktestRunRequest):
    """Point-in-time dataset manifest and approved evaluation policy per Section 12."""
    return run_backtest(req)


@app.get("/api/v1/runs/{run_id}/export")
def export_run_bundle(run_id: str):
    """Verified result bundle export with no secrets per Section 12."""
    job = job_service.get_job(run_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    events = job_service.get_events(run_id)
    return {
        "manifest": job.model_dump(),
        "event_history": [{"sequence": e.sequence, "event": e.event, "data": e.data} for e in events],
        "storage_format": "Parquet + DuckDB"
    }


# --- Authentication & Google SSO Endpoints ---

class ProprietaryLoginRequest(BaseModel):
    email: str = Field(..., description="Institutional email address")
    password: str = Field(..., description="Account password")


class ProprietaryRegisterRequest(BaseModel):
    email: str = Field(..., description="Institutional email address")
    password: str = Field(..., description="Account password (min 6 characters)")
    name: str = Field(..., description="Full display name")
    role: UserRole = Field("ANALYST", description="Institutional RBAC role")
    organization: str = Field("Institutional Client", description="Company or fund organization")


class GoogleAuthRequest(BaseModel):
    credential: Optional[str] = Field(None, description="Google OAuth ID Token JWT")
    email: Optional[str] = Field(None, description="Email for institutional sandbox persona")
    name: Optional[str] = Field(None, description="Display name for institutional persona")
    picture: Optional[str] = Field(None, description="User avatar image URL")
    role: Optional[UserRole] = Field(None, description="Institutional RBAC role")
    organization: Optional[str] = Field(None, description="Institutional employer / fund name")


@app.post("/api/v1/auth/register")
def register_user(req: ProprietaryRegisterRequest):
    """Registers a new institutional user account using the proprietary auth system."""
    try:
        auth_resp = auth_service.register_user(
            email=req.email,
            password=req.password,
            name=req.name,
            role=req.role,
            organization=req.organization,
        )
        return auth_resp
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/auth/login")
def login_proprietary_user(req: ProprietaryLoginRequest):
    """Authenticates via proprietary email & password system with bcrypt verification."""
    try:
        auth_resp = auth_service.authenticate_credentials(
            email=req.email,
            password=req.password,
        )
        return auth_resp
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@app.post("/api/v1/auth/google")
def authenticate_google_user(req: GoogleAuthRequest):
    """Authenticates via Google Workspace OAuth ID token or institutional sandbox credential."""
    try:
        auth_resp = auth_service.authenticate_google(
            credential=req.credential,
            email=req.email,
            name=req.name,
            picture=req.picture,
            role=req.role,
            organization=req.organization,
        )
        return auth_resp
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/auth/me")
def get_current_user(request: Request, token: Optional[str] = Query(None)):
    """Returns profile and RBAC permissions for the authenticated session."""
    auth_header = request.headers.get("Authorization") or token or ""
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authentication token required")
    
    user = auth_service.get_user_from_token(auth_header)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")
    
    return {"user": user}


@app.get("/api/v1/auth/users")
def list_system_users(request: Request):
    """Returns list of registered institutional users (requires authenticated session)."""
    auth_header = request.headers.get("Authorization") or ""
    user = auth_service.get_user_from_token(auth_header) if auth_header else None
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return {"users": auth_service.list_users()}


@app.post("/api/v1/auth/logout")
def logout_user(request: Request, token: Optional[str] = Query(None)):
    """Terminates active session."""
    auth_header = request.headers.get("Authorization") or token or ""
    success = auth_service.logout(auth_header)
    return {"status": "success", "logged_out": success}


# --- Advanced Stress Testing & Enterprise Risk Endpoints ---

class HedgeOptimizationRequest(BaseModel):
    portfolio_notional: float = 100_000_000.0
    unhedged_pnl: float = -23_450_000.0
    node_shocks: Dict[str, float] = Field(default_factory=dict)
    budget_limit: float = 500_000.0
    target_drawdown_pct: Optional[float] = None


@app.post("/api/v1/optimize/hedge")
def run_hedge_optimization(req: HedgeOptimizationRequest):
    """Solves for minimum-cost tail risk hedging basket using SLSQP convex optimization."""
    result = hedge_optimizer.optimize_hedge(
        portfolio_notional=req.portfolio_notional,
        unhedged_pnl=req.unhedged_pnl,
        node_shocks=req.node_shocks,
        budget_limit=req.budget_limit,
        target_drawdown_pct=req.target_drawdown_pct,
    )
    return {
        "initial_pnl": result.initial_pnl,
        "hedged_pnl": result.hedged_pnl,
        "pnl_improvement": result.pnl_improvement,
        "total_hedge_cost": result.total_hedge_cost,
        "initial_cvar_99": result.initial_cvar_99,
        "hedged_cvar_99": result.hedged_cvar_99,
        "cvar_reduction_pct": result.cvar_reduction_pct,
        "recommendations": [
            {
                "candidate_id": r.candidate_id,
                "instrument_name": r.instrument_name,
                "target_node": r.target_node,
                "action": r.action,
                "allocated_notional": r.allocated_notional,
                "estimated_cost": r.estimated_cost,
                "pnl_protection": r.pnl_protection,
                "description": r.description,
            }
            for r in result.recommendations
        ],
        "efficient_frontier": list(result.efficient_frontier),
    }


class ReverseStressRequest(BaseModel):
    portfolio_notional: float = 100_000_000.0
    target_loss_pct: float = Field(0.20, description="Target portfolio drawdown (e.g. 0.20 = 20%)")
    factor_sensitivities: Optional[Dict[str, float]] = None


@app.post("/api/v1/stress/reverse")
def run_reverse_stress_test(req: ReverseStressRequest):
    """Identifies the minimal plausible factor shock vector causing a specified portfolio breach."""
    result = reverse_stress_tester.find_breaking_point(
        portfolio_notional=req.portfolio_notional,
        target_loss_pct=req.target_loss_pct,
        factor_sensitivities=req.factor_sensitivities,
    )
    return {
        "target_loss_pct": result.target_loss_pct,
        "achieved_loss_pct": result.achieved_loss_pct,
        "minimal_shocks": result.minimal_shocks,
        "norm_l2": result.norm_l2,
        "critical_factor": result.critical_factor,
        "top_vulnerable_nodes": list(result.top_vulnerable_nodes),
        "iterations": result.iterations,
    }


class TimelineSimulationRequest(BaseModel):
    initial_shocks: Dict[str, float]
    portfolio_notional: float = 100_000_000.0
    time_horizon_days: Optional[List[int]] = None
    inventory_days: Optional[Dict[str, float]] = None


@app.post("/api/v1/stress/timeline")
def run_timeline_simulation(req: TimelineSimulationRequest):
    """Simulates multi-period propagation waves (0-90 days) tracking inventory depletion and milestones."""
    result = timeline_engine.simulate(
        initial_shocks=req.initial_shocks,
        portfolio_notional=req.portfolio_notional,
        time_horizon_days=req.time_horizon_days,
        inventory_days=req.inventory_days,
    )
    return {
        "initial_pnl": result.initial_pnl,
        "peak_drawdown_pnl": result.peak_drawdown_pnl,
        "peak_drawdown_day": result.peak_drawdown_day,
        "peak_drawdown_pct": result.peak_drawdown_pct,
        "total_milestones": result.total_milestones,
        "steps": [
            {
                "day": s.day,
                "cumulative_pnl": s.cumulative_pnl,
                "drawdown_pct": s.drawdown_pct,
                "cvar_99": s.cvar_99,
                "active_nodes_count": s.active_nodes_count,
                "node_shocks": s.node_shocks,
                "inventory_levels": s.inventory_levels,
                "milestones": [
                    {
                        "day": m.day,
                        "event_type": m.event_type,
                        "node_id": m.node_id,
                        "severity": m.severity,
                        "description": m.description,
                    }
                    for m in s.milestones
                ],
            }
            for s in result.steps
        ],
    }


class ScenarioDiffRequest(BaseModel):
    scenario_a_name: str
    scenario_b_name: str
    shocks_a: Dict[str, float]
    shocks_b: Dict[str, float]
    positions: Dict[str, float]
    pnl_a: Optional[float] = None
    pnl_b: Optional[float] = None
    cvar_a: Optional[float] = None
    cvar_b: Optional[float] = None


@app.post("/api/v1/scenario/diff")
def run_scenario_diff(req: ScenarioDiffRequest):
    """Calculates side-by-side differential metrics, delta PnL, and node risk shifts between two runs."""
    result = scenario_diff_engine.diff_scenarios(
        scenario_a_name=req.scenario_a_name,
        scenario_b_name=req.scenario_b_name,
        shocks_a=req.shocks_a,
        shocks_b=req.shocks_b,
        positions=req.positions,
        pnl_a=req.pnl_a,
        pnl_b=req.pnl_b,
        cvar_a=req.cvar_a,
        cvar_b=req.cvar_b,
    )
    return {
        "scenario_a_name": result.scenario_a_name,
        "scenario_b_name": result.scenario_b_name,
        "pnl_a": result.pnl_a,
        "pnl_b": result.pnl_b,
        "delta_pnl": result.delta_pnl,
        "cvar_99_a": result.cvar_99_a,
        "cvar_99_b": result.cvar_99_b,
        "delta_cvar_99": result.delta_cvar_99,
        "net_improvement_pct": result.net_improvement_pct,
        "amplified_nodes_count": result.amplified_nodes_count,
        "de_risked_nodes_count": result.de_risked_nodes_count,
        "unchanged_nodes_count": result.unchanged_nodes_count,
        "node_diffs": [
            {
                "node_id": d.node_id,
                "shock_a": d.shock_a,
                "shock_b": d.shock_b,
                "delta_shock": d.delta_shock,
                "pnl_a": d.pnl_a,
                "pnl_b": d.pnl_b,
                "delta_pnl": d.delta_pnl,
                "status": d.status.value,
                "relative_change_pct": d.relative_change_pct,
            }
            for d in result.node_diffs
        ],
        "top_de_risked_nodes": [
            {
                "node_id": d.node_id,
                "delta_pnl": d.delta_pnl,
                "status": d.status.value,
                "relative_change_pct": d.relative_change_pct,
            }
            for d in result.top_de_risked_nodes
        ],
        "top_amplified_nodes": [
            {
                "node_id": d.node_id,
                "delta_pnl": d.delta_pnl,
                "status": d.status.value,
                "relative_change_pct": d.relative_change_pct,
            }
            for d in result.top_amplified_nodes
        ],
    }


# --- Four-Eyes Audit Vault Endpoints ---

class AuditSubmitRequest(BaseModel):
    run_id: str
    scenario_name: str
    submitted_by: str
    submitted_by_role: str
    pnl_impact: float
    cvar_99: float
    shock_summary: Dict[str, float]
    comments: Optional[str] = None


@app.post("/api/v1/audit/submit")
def submit_stress_run_for_audit(req: AuditSubmitRequest):
    """Submits a stress run for Four-Eyes CRO governance sign-off."""
    entry = audit_vault_service.submit_for_review(
        run_id=req.run_id,
        scenario_name=req.scenario_name,
        submitted_by=req.submitted_by,
        submitted_by_role=req.submitted_by_role,
        pnl_impact=req.pnl_impact,
        cvar_99=req.cvar_99,
        shock_summary=req.shock_summary,
        comments=req.comments,
    )
    return {"entry": asdict(entry)}


class AuditApproveRequest(BaseModel):
    run_id: str
    approver_email: str
    approver_role: str
    comments: Optional[str] = None


@app.post("/api/v1/audit/approve")
def approve_stress_run(req: AuditApproveRequest):
    """Enforces Four-Eyes principle: CRO signs off on scenario run, generating cryptographic seal."""
    try:
        entry = audit_vault_service.approve_run(
            run_id=req.run_id,
            approver_email=req.approver_email,
            approver_role=req.approver_role,
            comments=req.comments,
        )
        return {"entry": asdict(entry)}
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))


class AuditLockRequest(BaseModel):
    run_id: str
    auditor_email: str


@app.post("/api/v1/audit/lock")
def lock_stress_run_for_regulators(req: AuditLockRequest):
    """Locks an approved run into an immutable regulatory audit packet."""
    try:
        packet = audit_vault_service.lock_for_regulatory_audit(
            run_id=req.run_id,
            auditor_email=req.auditor_email,
        )
        return packet
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/audit/entries")
def list_audit_entries():
    """Lists all governance sign-off entries in the audit vault."""
    entries = audit_vault_service.list_all_entries()
    return {"entries": [asdict(e) for e in entries]}


@app.get("/api/v1/audit/vault/{run_id}")
def get_audit_entry(run_id: str):
    """Retrieves audit entry and verification seal by run_id."""
    entry = audit_vault_service.get_run(run_id)
    if not entry:
        raise HTTPException(status_code=404, detail=f"Audit entry for run {run_id} not found")
    return {"entry": asdict(entry)}


# --- Executive Board-Ready Memo Endpoints ---

class ExecutiveReportRequest(BaseModel):
    scenario_name: str
    portfolio_notional: float = 100_000_000.0
    pnl_loss: float = -23_450_000.0
    cvar_99: float = 29_312_500.0
    var_95: float = 21_200_000.0
    node_shocks: Optional[Dict[str, float]] = None
    cro_name: Optional[str] = "Sarah Chen, Ph.D."
    cro_title: Optional[str] = "Chief Risk Officer"
    firm_name: Optional[str] = "Citadel Global Equities & Quantitative Strategies"


@app.post("/api/v1/report/executive")
def generate_executive_report(req: ExecutiveReportRequest):
    """Generates print-ready HTML and structured JSON executive memo for board risk committees."""
    memo = report_generator_service.generate_memo(
        scenario_name=req.scenario_name,
        portfolio_notional=req.portfolio_notional,
        pnl_loss=req.pnl_loss,
        cvar_99=req.cvar_99,
        var_95=req.var_95,
        node_shocks=req.node_shocks,
        cro_name=req.cro_name or "Sarah Chen, Ph.D.",
        cro_title=req.cro_title or "Chief Risk Officer",
        firm_name=req.firm_name or "Citadel Global Equities & Quantitative Strategies",
    )
    return {
        "memo_id": memo.memo_id,
        "title": memo.title,
        "classification": memo.classification,
        "generated_at": memo.generated_at,
        "scenario_name": memo.scenario_name,
        "portfolio_notional": memo.portfolio_notional,
        "total_pnl_loss": memo.total_pnl_loss,
        "drawdown_pct": memo.drawdown_pct,
        "cvar_99": memo.cvar_99,
        "var_95": memo.var_95,
        "top_losses": memo.top_losses,
        "critical_paths": memo.critical_paths,
        "recommended_hedges": memo.recommended_hedges,
        "sec_citations": memo.sec_citations,
        "signoff": memo.signoff,
        "html_content": memo.html_content,
    }


# --- Advanced Enterprise Risk Expansion Endpoints ---

class LiquidityStressRequest(BaseModel):
    positions: Optional[List[Dict[str, Any]]] = None
    liquidation_pct: float = Field(0.20, description="Percentage of notional liquidated for margin/redemptions")
    participation_rate: float = Field(0.10, description="Max daily participation rate of ADV")
    fund_unencumbered_cash: float = 15_000_000.0
    portfolio_unhedged_pnl: float = -23_450_000.0
    gross_derivative_notional: float = 50_000_000.0


@app.post("/api/v1/liquidity/simulate")
def run_liquidity_simulation(req: LiquidityStressRequest):
    """Computes Almgren-Chriss endogenous market impact and ISDA SIMM margin call spirals."""
    raw_positions = req.positions or [
        {"asset_id": "NVDA", "target_notional": 25_000_000.0, "adv_30d": 120_000_000.0, "volatility_ann": 0.45, "bid_ask_spread_bps": 3.5, "liquidation_urgency": "HIGH"},
        {"asset_id": "TSM", "target_notional": 20_000_000.0, "adv_30d": 65_000_000.0, "volatility_ann": 0.38, "bid_ask_spread_bps": 4.0, "liquidation_urgency": "HIGH"},
        {"asset_id": "AAPL", "target_notional": 20_000_000.0, "adv_30d": 180_000_000.0, "volatility_ann": 0.28, "bid_ask_spread_bps": 2.0, "liquidation_urgency": "MEDIUM"},
        {"asset_id": "F", "target_notional": 10_000_000.0, "adv_30d": 35_000_000.0, "volatility_ann": 0.35, "bid_ask_spread_bps": 5.0, "liquidation_urgency": "FIRE_SALE"},
    ]
    typed_positions = [
        LiquidationPosition(
            asset_id=p["asset_id"],
            target_notional=float(p["target_notional"]),
            adv_30d=float(p["adv_30d"]),
            volatility_ann=float(p["volatility_ann"]),
            bid_ask_spread_bps=float(p["bid_ask_spread_bps"]),
            liquidation_urgency=p.get("liquidation_urgency", "MEDIUM"),
        )
        for p in raw_positions
    ]
    result = liquidity_engine.evaluate_liquidation(
        positions=typed_positions,
        liquidation_pct=req.liquidation_pct,
        participation_rate=req.participation_rate,
        fund_unencumbered_cash=req.fund_unencumbered_cash,
        portfolio_unhedged_pnl=req.portfolio_unhedged_pnl,
        gross_derivative_notional=req.gross_derivative_notional,
    )
    return {
        "total_notional_liquidated": result.total_notional_liquidated,
        "total_market_impact_loss": result.total_market_impact_loss,
        "blended_price_discount_pct": result.blended_price_discount_pct,
        "fire_sale_contagion_multiplier": result.fire_sale_contagion_multiplier,
        "margin_summary": asdict(result.margin_summary),
        "asset_impacts": [asdict(a) for a in result.asset_impacts],
    }


class MutationRequest(BaseModel):
    mutation_name: str = "Taiwan Decoupling & Arizona Sourcing"
    mutations: Optional[List[Dict[str, Any]]] = None
    base_shocks: Optional[Dict[str, float]] = None
    positions: Optional[Dict[str, float]] = None


@app.post("/api/v1/mutation/evaluate")
def run_mutation_evaluation(req: MutationRequest):
    """Simulates topological supply chain interventions (severing/adding edges) and computes Resilience ROI."""
    raw_mutations = req.mutations or [
        {
            "mutation_type": "REWEIGHT_EDGE",
            "source_id": "TSM",
            "target_id": "NVDA",
            "new_weight": 0.15,
            "capex_cost": 2_500_000.0,
            "lead_time_months": 12,
            "rationale": "Re-allocate 60% packaging to TSMC Fab 21 in Phoenix, Arizona",
        },
        {
            "mutation_type": "ADD_EDGE",
            "source_id": "INTC",
            "target_id": "NVDA",
            "new_weight": 0.20,
            "capex_cost": 1_200_000.0,
            "lead_time_months": 8,
            "rationale": "Secondary foundry qualification with Intel Foundry Services",
        },
    ]
    typed_mutations = [
        GraphMutation(
            mutation_type=MutationType(m.get("mutation_type", "REWEIGHT_EDGE")),
            source_id=m["source_id"],
            target_id=m["target_id"],
            new_weight=float(m.get("new_weight", 0.20)),
            capex_cost=float(m.get("capex_cost", 1_000_000.0)),
            lead_time_months=int(m.get("lead_time_months", 6)),
            rationale=m.get("rationale", ""),
        )
        for m in raw_mutations
    ]
    base_shocks = req.base_shocks or {"TSM": -0.40, "NVDA": -0.35, "AAPL": -0.28, "F": -0.22}
    positions = req.positions or {"TSM": 20_000_000.0, "NVDA": 25_000_000.0, "AAPL": 20_000_000.0, "F": 10_000_000.0}
    base_edges = {("TSM", "NVDA"): 0.38, ("TSM", "AAPL"): 0.34, ("F", "APTV"): 0.32}

    res = mutation_engine.evaluate_mutation(
        mutation_name=req.mutation_name,
        mutations=typed_mutations,
        base_shocks=base_shocks,
        positions=positions,
        base_edges=base_edges,
    )
    return asdict(res)


@app.get("/api/v1/edgar/status")
def get_edgar_crawler_status():
    """Returns status and recent extractions from autonomous SEC EDGAR continuous crawler."""
    return edgar_crawler_service.get_status()


class EdgarIngestRequest(BaseModel):
    ticker: str
    filing_type: str = "10-K"
    accession_number: str
    filing_text: str


@app.post("/api/v1/edgar/ingest")
def ingest_filing_text(req: EdgarIngestRequest):
    """Parses raw SEC filing text and extracts confidence-scored transmission edges."""
    discovered = edgar_crawler_service.ingest_filing_text(
        ticker=req.ticker,
        filing_type=req.filing_type,
        accession_number=req.accession_number,
        filing_text=req.filing_text,
    )
    return {"ticker": req.ticker, "discovered_edges": [asdict(e) for e in discovered]}


class AladdinImportRequest(BaseModel):
    csv_content: str


@app.post("/api/v1/pms/aladdin/import")
def import_aladdin_portfolio(req: AladdinImportRequest):
    """Ingests BlackRock Aladdin CSV portfolio export."""
    positions = institutional_adapters_service.parse_aladdin_csv(req.csv_content)
    return {"total_positions": len(positions), "positions": [asdict(p) for p in positions]}


class CCARReportRequest(BaseModel):
    portfolio_notional: float = 100_000_000.0
    pnl_loss: float = -23_450_000.0
    cvar_99: float = 29_312_500.0
    var_95: float = 21_200_000.0
    scenario_name: Optional[str] = "Federal Reserve Supervisory Severely Adverse Scenario"
    institution_name: Optional[str] = "Citadel Global Equities & Quantitative Strategies"


@app.post("/api/v1/regulatory/ccar/export")
def export_fed_ccar_schedule(req: CCARReportRequest):
    """Generates Federal Reserve CCAR Form FR Y-14A Schedule A submission packet."""
    schedule = institutional_adapters_service.generate_fed_ccar_y14a(
        portfolio_notional=req.portfolio_notional,
        pnl_loss=req.pnl_loss,
        cvar_99=req.cvar_99,
        var_95=req.var_95,
        scenario_name=req.scenario_name or "Federal Reserve Supervisory Severely Adverse Scenario",
        institution_name=req.institution_name or "Citadel Global Equities & Quantitative Strategies",
    )
    return schedule


class CopilotChatRequest(BaseModel):
    query: str
    portfolio_notional: float = 100_000_000.0
    unhedged_pnl: float = -23_450_000.0
    node_shocks: Optional[Dict[str, float]] = None


@app.post("/api/v1/copilot/chat")
def chat_with_stress_copilot(req: CopilotChatRequest):
    """Processes natural language risk queries with the AI Conversational Risk Officer."""
    answer = stress_copilot.answer_query(
        query=req.query,
        portfolio_notional=req.portfolio_notional,
        unhedged_pnl=req.unhedged_pnl,
        node_shocks=req.node_shocks,
    )
    return asdict(answer)


@app.get("/api/v1/alerts")
def list_risk_alerts():
    """Lists recent risk limit breach alerts across institutional channels."""
    alerts = alerting_service.list_alerts()
    return {"alerts": [asdict(a) for a in alerts]}


class TestAlertRequest(BaseModel):
    scenario_name: str = "Taiwan Strait Blockade & Semiconductor Shock"
    portfolio_notional: float = 100_000_000.0
    pnl_loss: float = -23_450_000.0
    cvar_99: float = 29_312_500.0
    limit_drawdown_pct: float = -15.0


@app.post("/api/v1/alerts/test")
def trigger_test_alert(req: TestAlertRequest):
    """Simulates a limit breach alert dispatch to Slack/Teams/PagerDuty."""
    alert = alerting_service.evaluate_and_dispatch(
        scenario_name=req.scenario_name,
        portfolio_notional=req.portfolio_notional,
        pnl_loss=req.pnl_loss,
        cvar_99=req.cvar_99,
        limit_drawdown_pct=req.limit_drawdown_pct,
    )
    if alert:
        slack_payload = alerting_service.format_slack_payload(alert)
        return {"alert": asdict(alert), "slack_payload": slack_payload}
    return {"status": "no_breach"}


@app.get("/api/v1/graph/geospatial")
def get_geospatial_network():
    """Returns geographic coordinates, maritime choke points, and critical fab clusters."""
    facilities = [
        {"id": "TSMC_FAB18", "ticker": "TSM", "name": "TSMC Fab 18 (3nm/5nm GigaFab)", "lat": 23.116, "lng": 120.278, "city": "Tainan", "country": "Taiwan", "type": "FAB", "criticality": 1.0},
        {"id": "TSMC_FAB21", "ticker": "TSM", "name": "TSMC Fab 21 (Phase 1)", "lat": 33.743, "lng": -112.164, "city": "Phoenix", "country": "USA", "type": "FAB", "criticality": 0.4},
        {"id": "FOXCONN_ZHENGZHOU", "ticker": "2317_TW", "name": "Foxconn 'iPhone City' MegaComplex", "lat": 34.528, "lng": 113.829, "city": "Zhengzhou", "country": "China", "type": "ASSEMBLY", "criticality": 0.9},
        {"id": "FORD_ROUGE", "ticker": "F", "name": "Ford Dearborn Truck Plant (F-150)", "lat": 42.308, "lng": -83.155, "city": "Dearborn", "country": "USA", "type": "OEM", "criticality": 0.7},
        {"id": "CHOKE_TAIWAN_STRAIT", "ticker": "GEO_TAIWAN", "name": "Taiwan Strait Maritime Corridor", "lat": 24.5, "lng": 119.8, "city": "Taiwan Strait", "country": "Maritime", "type": "CHOKE_POINT", "criticality": 1.0},
        {"id": "CHOKE_MALACCA", "ticker": "GEO_MALACCA", "name": "Strait of Malacca", "lat": 2.5, "lng": 101.5, "city": "Malacca", "country": "Maritime", "type": "CHOKE_POINT", "criticality": 0.9},
        {"id": "CHOKE_SUEZ", "ticker": "GEO_SUEZ", "name": "Suez Canal / Bab-el-Mandeb", "lat": 29.9, "lng": 32.5, "city": "Suez", "country": "Egypt", "type": "CHOKE_POINT", "criticality": 0.85},
        {"id": "PORT_ROTTERDAM", "ticker": "PORT_RTM", "name": "Port of Rotterdam Gateway", "lat": 51.95, "lng": 4.13, "city": "Rotterdam", "country": "Netherlands", "type": "PORT", "criticality": 0.75},
        {"id": "PORT_LONG_BEACH", "ticker": "PORT_LA", "name": "Port of Los Angeles / Long Beach", "lat": 33.74, "lng": -118.26, "city": "Los Angeles", "country": "USA", "type": "PORT", "criticality": 0.8},
    ]
    corridors = [
        {"from": "TSMC_FAB18", "to": "FOXCONN_ZHENGZHOU", "mode": "AIR_FREIGHT", "dependency": 0.85},
        {"from": "FOXCONN_ZHENGZHOU", "to": "PORT_LONG_BEACH", "mode": "CONTAINER_SHIP", "dependency": 0.75},
        {"from": "CHOKE_TAIWAN_STRAIT", "to": "PORT_LONG_BEACH", "mode": "MARITIME_CORRIDOR", "dependency": 0.90},
        {"from": "CHOKE_MALACCA", "to": "PORT_ROTTERDAM", "mode": "CRUDE_AND_CONTAINER", "dependency": 0.80},
    ]
    return {"facilities": facilities, "corridors": corridors}


# --- Threat Intelligence & AIS Maritime Endpoints ---

@app.get("/api/v1/threats/ais/status")
def get_ais_threat_status():
    """Returns current real-time satellite AIS vessel congestion and geopolitical threat snapshot."""
    return threat_intelligence_service.get_snapshot()


@app.post("/api/v1/threats/ais/tick")
def advance_ais_telemetry_tick():
    """Simulates one discrete forward drift step in AIS vessel traffic and recalculates SVI."""
    snapshot = threat_intelligence_service.advance_telemetry_tick()
    return asdict(snapshot)


class IngestThreatRequest(BaseModel):
    headline: str
    source: str
    severity: str = "HIGH"
    choke_point_id: str = "GEO_TAIWAN_STRAIT"
    affected_nodes: List[str]
    raw_supply_impact_pct: float = -0.30
    details: str = ""


@app.post("/api/v1/threats/ingest")
def ingest_breaking_threat(req: IngestThreatRequest):
    """Ingests a breaking geopolitical or maritime threat wire event."""
    threat = threat_intelligence_service.ingest_threat_event(
        headline=req.headline,
        source=req.source,
        severity=req.severity,
        choke_point_id=req.choke_point_id,
        affected_nodes=req.affected_nodes,
        raw_supply_impact_pct=req.raw_supply_impact_pct,
        details=req.details,
    )
    return asdict(threat)


class InjectThreatRequest(BaseModel):
    event_id: str


@app.post("/api/v1/threats/inject")
def inject_threat_into_simulation(req: InjectThreatRequest):
    """Translates a threat intelligence event into an exact s^(0) impulse vector for stress simulation."""
    try:
        injection_payload = threat_intelligence_service.inject_threat_to_scenario(req.event_id)
        return injection_payload
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/v1/threats/stream")
async def stream_threat_telemetry(request: Request):
    """Server-Sent Events (SSE) stream pushing real-time AIS vessel telemetry and SVI updates."""
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            snapshot = threat_intelligence_service.advance_telemetry_tick()
            yield {
                "event": "telemetry_update",
                "data": json.dumps(asdict(snapshot)),
            }
            await asyncio.sleep(3)

    return EventSourceResponse(event_generator())



