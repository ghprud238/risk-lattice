# RiskLattice Mobile & Client-Server Architecture Guide

This guide details the architectural division of labor between the **RiskLattice Backend Engine**, the **React Web Application** (`frontend/`), and the **React Native / Expo Mobile Application** (`mobile/`).

---

## 1. Executive Summary & Client-Server Division of Labor

Financial risk managers, Chief Risk Officers (CROs), and portfolio managers need access to critical threat intelligence and stress metrics outside the trading floor. A sudden naval blockade in the Taiwan Strait or a missile strike near the Bab-el-Mandeb Strait requires immediate risk triage, executive decision-making, and regulatory dual-key approval—even when away from a desktop Bloomberg/Aladdin terminal.

To support this while upholding institutional security standards (Federal Reserve SR 11-7, Basel III, and Rule P-01 privacy guarantees), RiskLattice enforces a strict **three-tier client-server separation**:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       RISKLATTICE CLIENT TIER                                  │
├───────────────────────────────────────────────┬─────────────────────────────────────────────────┤
│            WEB CLIENT (frontend/)             │             MOBILE CLIENT (mobile/)             │
│            React 19 / Next.js 15              │            React Native / Expo SDK 58           │
│                   Port 5050                   │                 iOS & Android                   │
├───────────────────────────────────────────────┼─────────────────────────────────────────────────┤
│ • Full Cytoscape.js interactive network graph │ • Real-time Satellite AIS Maritime Radar & SVI  │
│ • Deep multi-period timeline scrubber (0-90d) │ • 1-Tap Factor Shock Injection (Taiwan, Suez)   │
│ • Raw CSV/JSON portfolio blotter upload       │ • 3-Stage PnL Waterfall (Direct, Supplier, Net) │
│ • Algorithmic reverse stress testing          │ • Conversational AI CRO Copilot Chat            │
│ • Comprehensive CCAR FR Y-14A Schedule A export│ • 1-Tap Four-Eyes Biometric Dual-Key Sign & Seal│
│ • Side-by-side scenario diffing (A/B)         │ • Network switcher (Local, Emulator, LAN IP)    │
└───────────────────────────────────────────────┴─────────────────────────────────────────────────┘
                                                │
                                                │ REST API / Server-Sent Events (SSE)
                                                │ JSON Payloads (Shared TypeScript Types)
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   GATEWAY & ORCHESTRATION TIER                                  │
│                                        FastAPI (Port 5051)                                      │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ • Authentication & 4-tier RBAC (Google OAuth2 / JWT / Persona Headers)                          │
│ • Live Satellite AIS telemetry simulator & background drift ticker (8 choke points)             │
│ • Rule P-01 Local Privacy Scrubber (Removes dollar values & positions before external prompts)  │
│ • LiteLLM / Ollama local semantic translation & verbatim SEC 10-K extraction                     │
│ • In-memory frozen scenario snapshots & event dispatcher                                         │
└───────────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                                │
                                                │ Pure In-Memory DataFrames & Typed Structs
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                              DETERMINISTIC QUANT ENGINE (AST ISOLATED)                          │
│                                       Python 3.12 / NumPy / SciPy                               │
├─────────────────────────────────────────────────────────────────────────────────────────────────┤
│ • 4-Hop Damped Contagion Propagator (alpha = 0.65, non-linear leverage distress)                │
│ • 10,000-Path Student-t Copula Monte Carlo Engine (nu = 5, tail-dependence lambda_U)           │
│ • Multi-Asset Valuation (Equities, Options Greeks, Bonds, CDS, Private Credit, CLO Tranches)    │
│ • Endogenous Liquidity & Fire-Sale Slippage (Almgren-Chriss, 2000)                              │
│ • Cryptographic Audit Trail (SHA-256 Run Seals, Kupiec POF Likelihood Ratio Tests)              │
│ ❌ AST ISOLATION GUARANTEE: Never imports FastAPI, DuckDB, HTTP clients, or LLM libraries.      │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Why Run Heavy Math on the Server?

1. **Deterministic Floating-Point Fidelity**:
   Monte Carlo simulations involving 10,000 paths across correlated Student-$t$ Copulas with 5 degrees of freedom require high-performance NumPy/SciPy linear algebra and BLAS routines. Running this client-side on mobile devices would drain battery, cause thermal throttling, and introduce platform-dependent floating-point divergence.
2. **Regulatory Model Auditability (SR 11-7 & Basel III)**:
   Bank regulators prohibit decentralized, unversioned client-side risk calculations. All stress matrices must execute within an immutable, auditable container that logs SHA-256 run seals to the Four-Eyes audit vault.
3. **Institutional Confidentiality (Rule P-01)**:
   Private supply-chain dependency graphs (derived from proprietary supplier contracts) and portfolio trade blotters reside securely within DuckDB behind the corporate firewall. The mobile client only receives aggregated, post-processed telemetry and scenario outputs.

---

## 3. Shared Type Architecture (`shared/types/risk-lattice.ts`)

To prevent client-server drift, both the React web application and React Native mobile application share a single source of truth for domain schemas located at `shared/types/risk-lattice.ts`:

- **Threat & AIS Types**: `ThreatSnapshot`, `ChokePointTelemetry`, `ThreatEvent`
- **Simulation Types**: `SimulationResult`, `PortfolioPnL`, `RiskMetricsResult`, `ContagionNodeImpact`
- **Audit & Governance Types**: `AuditEntry`, `AuditSignoffRequest`, `AuditSignoffResponse`
- **Copilot & AI Types**: `CopilotMessage`, `CopilotResponse`, `Citation`
- **User & Persona Types**: `UserProfile`, `UserRole`, `SystemHealth`

---

## 4. Mobile Application Structure (`mobile/`)

The mobile application is engineered with **React Native** and **Expo SDK 58** (`react: 19.3.0`, `react-native: 0.88.1`) using TypeScript in strict mode:

```
mobile/
├── App.tsx                     # Root application container & tab coordinator
├── app.json                    # Expo project configuration
├── package.json                # Dependencies: expo, react-native-safe-area-context
├── tsconfig.json               # TypeScript configuration with strict mode
└── src/
    ├── config/
    │   └── api.ts              # API client gateway, network switcher, & mock fallbacks
    ├── theme/
    │   └── colors.ts           # Institutional dark palette (Cyber Cyan, Emerald, Crimson)
    ├── components/
    │   ├── Header.tsx          # Real-time connection status & CRO persona indicator
    │   ├── SviGauge.tsx        # Systemic Vulnerability Index (SVI 0-100) circular gauge
    │   ├── ChokePointCard.tsx  # Maritime choke point status, speed delta, & demurrage
    │   ├── ThreatWireCard.tsx  # Real-time intelligence wire with 1-tap shock injection
    │   ├── WaterfallCard.tsx   # 3-Stage PnL breakdown & 99% CVaR proportional bar
    │   └── TabBar.tsx          # Institutional bottom navigation bar
    └── screens/
        ├── RadarScreen.tsx     # Live AIS maritime radar, SVI gauge, & breaking threat wire
        ├── StressScreen.tsx    # Factor shock simulator, 3-stage PnL waterfall, & MCR table
        ├── CopilotScreen.tsx   # Conversational AI CRO with 10-K citations & prompt chips
        ├── AuditScreen.tsx     # Four-Eyes governance vault & 1-tap cryptographic dual sign-off
        └── SettingsScreen.tsx  # Dynamic Gateway host switcher & institutional persona picker
```

---

## 5. Walkthrough of the 5 Core Mobile Screens

### 5.1 Radar Screen (`RadarScreen.tsx`)
- **Systemic Vulnerability Index (SVI $0-100$)**: Real-time composite indicator derived from maritime congestion across 5 key trade choke points.
- **1-Tap Advance Drift**: Advance time by $+1$ hour to simulate stochastic vessel arrivals and queue growth.
- **5 Maritime Choke Points**: Monitored live:
  - **Taiwan Strait**: TSMC wafer transit corridors, container queue, speed collapse.
  - **Malacca Strait**: Hydrocarbon and electronics shipping lane.
  - **Suez Canal**: Europe-Asia container freight lane.
  - **Strait of Hormuz**: Global crude supply artery.
  - **Panama Canal**: Trans-Pacific/Atlantic container routing.
- **Live Threat Wire Feed**: Breaking geopolitical and cyber events with a **1-Tap "⚡ Inject Shock"** button that instantly transitions to the Stress Simulator.

### 5.2 Stress Simulation Screen (`StressScreen.tsx`)
- **Factor Shock Grid**: Select from institutional macro factors (`FOUNDRY_TW`, `BALTIC_DRY`, `BRENT_CRUDE`, `SOFR_SPREAD`).
- **Interactive Shock Magnitude**: Adjust shock depth ($-15\%$ to $-60\%$) with instant calculation.
- **3-Stage PnL Waterfall Visualization**:
  - **1st Order (Direct Impact)**: Immediate valuation shocks on primary equity/bond holdings.
  - **2nd Order (Tier-1/2 Suppliers)**: Unhedged supply chain cascading disruption.
  - **3rd/4th Order (Contagion & Liquidity)**: Debt covenant breaches and fire-sale margin spirals.
- **Risk Metrics Summary**: Tail Ratio ($12.2\times$), Student-$t$ Copula 99% CVaR, and Marginal Contribution to Risk (MCR).

### 5.3 AI Copilot Screen (`CopilotScreen.tsx`)
- **Conversational CRO Assistant**: Natural language querying of portfolio exposures, supplier concentration, and mitigation strategies.
- **Suggested Prompts**: 1-tap institutional chips (*"Why is Apple impacted by a foundry shock?"*, *"What hedge minimizes Taiwan drawdown under $500k?"*).
- **Verbatim SEC 10-K Citations**: Every AI response cites exact character-offset text from company disclosures, ensuring zero hallucination.

### 5.4 Audit & Governance Screen (`AuditScreen.tsx`)
- **Four-Eyes Principle Enforcement**: Federal Reserve SR 11-7 compliance requiring independent secondary sign-off on stress tests.
- **Run Audit Log**: Full list of historical simulations with timestamp, model version, and status (`PENDING_APPROVAL` vs `APPROVED`).
- **1-Tap Biometric Dual-Sign & Seal**: Signs the stress test run, generates an immutable **SHA-256 digital seal**, and locks the scenario for regulatory filing.

### 5.5 Settings & Gateway Configuration (`SettingsScreen.tsx`)
- **Network Gateway Switcher**: Connect to any backend environment with 1 tap:
  - **iOS Simulator Preset**: `http://localhost:5051`
  - **Android Emulator Preset**: `http://10.0.2.2:5051`
  - **LAN / Local Wi-Fi Preset**: `http://192.168.1.100:5051` (customizable)
- **Ping Server Utility**: Instant connectivity verification with round-trip latency.
- **Enterprise Persona Switcher**: Switch between `Chief Risk Officer (Sarah)`, `Portfolio Manager (David)`, `Risk Analyst (Alex)`, and `Internal Auditor (Elena)`.

---

## 6. How to Run & Test the Mobile App

### 6.1 Prerequisites
1. Ensure the RiskLattice backend is running on port 5051:
   ```bash
   cd /Users/dpcubed/projects/risk-lattice
   uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 5051
   ```
2. Verify backend health:
   ```bash
   curl http://localhost:5051/api/v1/health
   ```

### 6.2 Running the Mobile App with Expo
```bash
cd /Users/dpcubed/projects/risk-lattice/mobile

# Start Expo development server
npm run start
```

Inside the interactive terminal:
- Press **`i`** to launch in the **iOS Simulator** (requires Xcode).
- Press **`a`** to launch in the **Android Emulator** (requires Android Studio).
- Press **`w`** to launch in a **Web Browser** preview.
- Scan the printed QR code with the **Expo Go app** on a physical iPhone or Android device on the same local Wi-Fi.

### 6.3 Configuring Physical Device Network Connection
When testing on a physical iPhone or Android phone:
1. Find your computer's local Wi-Fi IP address:
   ```bash
   ipconfig getifaddr en0   # macOS
   ```
2. In the mobile app, navigate to the **Config** tab.
3. Select **LAN IP (Wi-Fi)** and enter `http://<YOUR_IP>:5051`.
4. Tap **Ping Server** to confirm connectivity.

### 6.4 Zero-Network Offline Mock Fallback
The mobile app includes a resilient offline mock layer. If the backend is unreachable, the API service automatically falls back to deterministic, mathematically grounded mock fixtures, enabling complete UI evaluation without network connectivity.

---

## 7. Security & Rule P-01 Compliance

- **No Dollar Exposure**: The mobile app never transmits un-sanitized client portfolio positions or cash values to third-party services.
- **Biometric Authentication Ready**: The Audit Vault interface is structured for local Secure Enclave / FaceID biometric verification before signing cryptographic run seals.
- **Scoped RBAC**: Client requests transmit standard institutional role tokens, restricting unauthorized users from approving stress tests or modifying model parameters.
