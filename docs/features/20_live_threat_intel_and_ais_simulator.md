# Feature 20: Live Threat Intelligence Feed & AIS Maritime Simulator

## Executive Overview
Geopolitical shocks and maritime transit interruptions unfold in real time before public corporations file quarterly SEC reports. By the time a 10-K is released, market pricing has already absorbed the damage.

The **Live Threat Intelligence Feed & AIS Maritime Simulator** transforms RiskLattice from an offline analytical model into an active, continuous risk monitoring and early-warning operations center. It couples real-time **Satellite AIS (Automatic Identification System)** commercial vessel tracking across the world's 5 critical maritime corridors with a continuous geopolitical threat intelligence feed, computing an aggregate **Systemic Vulnerability Index (SVI)** and enabling 1-click shock injection into the quantitative stress canvas.

---

## The 5 Monitored Maritime Choke Points

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              SATELLITE AIS MONITORED MARITIME CORRIDORS                                │
├─────────────────────────┬──────────────────────┬───────────────────────┬───────────────────────────────┤
│       CHOKE POINT       │   BASELINE FLEET     │   BASELINE SPEED      │       GLOBAL DEPENDENCY       │
├─────────────────────────┼──────────────────────┼───────────────────────┼───────────────────────────────┤
│ **Taiwan Strait**       │ 240 vessels / day    │ 16.5 knots            │ 65% of advanced 3nm/5nm silicon│
│ **Strait of Malacca**   │ 320 vessels / day    │ 15.0 knots            │ Middle East crude to E. Asia  │
│ **Suez Canal / Red Sea**│ 85 vessels / day     │ 12.0 knots            │ 12% of global container trade │
│ **Strait of Hormuz**    │ 110 vessels / day    │ 14.0 knots            │ 21% of global petroleum liquids│
│ **Panama Canal**        │ 36 vessels / day     │ 8.0 knots             │ US Gulf LNG, grain, bulk coal │
└─────────────────────────┴──────────────────────┴───────────────────────┴───────────────────────────────┘
```

---

## Mathematical Formulation

### 1. Non-Linear Congestion Index ($C_i$)
For choke point $i$ with current vessel count $V_i$, baseline daily capacity $V_{0, i}$, current average speed $s_i$, and baseline speed $s_{0, i}$:
$$C_i = \left(\frac{V_i}{V_{0, i}}\right) \cdot \left(\max\left(1.0, \frac{s_{0, i}}{\max(0.5, s_i)}\right)\right)^{0.8}$$
When naval drills or accidents force ships to anchor (speed dropping from 16 to 3 knots), $C_i$ surges non-linearly above $4.0\times$.

### 2. Demurrage & Charter Surge Model
$$\text{DemurrageSpike}_i = \max\left(0.0, \, (C_i - 1.0) \cdot 45.0\%\right)$$
Quantifies the daily container/tanker charter rate escalation caused by transit queues.

### 3. Disruption Probability ($\mathbb{P}_{\text{disrupt}}$)
Modeled via a calibrated logistic response incorporating operational status penalties:
$$\mathbb{P}_{\text{disrupt}, i} = \frac{1}{1 + e^{-\left(2.0 \cdot (C_i - 1.8) + 3.0 \cdot \text{StatusPenalty}_i\right)}}$$
where $\text{StatusPenalty}_i \in \{0.15\text{ (Elevated)}, 0.50\text{ (Drill/Obstruction)}, 0.85\text{ (Blockade)}\}$.

### 4. Systemic Vulnerability Index (SVI)
A global fragility index on a scale of $0 - 100$:
$$\text{SVI} = 100 \cdot \sum_{i=1}^5 w_i \cdot \min\left(1.0, \, \frac{C_i - 1.0}{2.5} \cdot 0.6 + 0.4 \cdot \text{StatusPenalty}_i\right)$$
with weights: Taiwan ($0.35$), Malacca ($0.25$), Suez ($0.20$), Hormuz ($0.15$), Panama ($0.05$).

### 5. Threat-to-Impulse Vector Mapping ($s^{(0)}$)
When a live threat wire arrives, the engine translates it into a direct shock vector:
$$s^{(0)}_j = \text{clamp}\left( -\left|\text{RawShock}\right| \cdot \mu_{\text{severity}} \cdot \text{TierDecay}_j, \, -0.95, \, -0.02 \right)$$
where $\text{TierDecay}_j = 0.85^j$ across downstream affected tickers ($j=0$ primary foundry, $j=1$ module assembler, etc.).

---

## Technical Implementation

### File Locations
- **Scientific Engine**: `backend/app/engine/ais_threat.py` (AST isolated, pure NumPy/math)
- **Service Layer**: `backend/app/services/threat_intelligence_service.py`
- **Unit & Integration Tests**: `backend/tests/unit/test_ais_threat.py` (5 tests passing)
- **Frontend Radar**: `frontend/src/components/ThreatIntelligenceRadar.tsx`
- **Dashboard Tab**: `frontend/src/app/page.tsx` (`"radar"`)

### REST & Streaming API Endpoints
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/threats/ais/status` | Current snapshot of 5 choke points, active vessels, speeds, and SVI |
| `POST` | `/api/v1/threats/ais/tick` | Advances vessel positions and queue drift by one discrete simulation step |
| `POST` | `/api/v1/threats/ingest` | Ingests a new breaking geopolitical or maritime threat wire event |
| `POST` | `/api/v1/threats/inject` | Translates a threat event into an exact direct impulse vector $s^{(0)}$ |
| `GET` | `/api/v1/threats/stream` | Server-Sent Events (SSE) live stream broadcasting telemetry updates |

---

## Verification & Test Coverage
- `test_choke_point_telemetry_metrics`: validates non-linear congestion index, demurrage surge, and disruption probability.
- `test_systemic_vulnerability_index_bounds`: verifies $0 \le \text{SVI} \le 100$ and monotonic increase under blockade.
- `test_translate_threat_to_direct_impulses`: verifies tier decay and negative shock bounds.
- `test_threat_intelligence_service_lifecycle`: verifies tick advancement and scenario injection payload.
- `test_threat_api_endpoints`: verifies status, tick, ingest, and injection endpoints via TestClient.
- `test_engine_ast_import_isolation`: confirms zero database/web/LLM imports in `ais_threat.py`.
