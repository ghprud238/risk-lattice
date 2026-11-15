# Feature 18: AI Conversational Stress Copilot

## Executive Overview
Executive leaders and portfolio managers often lack the time to manually configure complex scenario JSON bodies or navigate 50-node graph visualizations. They need an intelligent, conversational interface capable of understanding macro inquiries, executing deterministic graph analytics, retrieving verbatim SEC 10-K citations, and proposing concrete mitigation strategies.

The **AI Stress Copilot** functions as an autonomous, conversational Chief Risk Officer, bridging high-level natural language queries and bit-exact quantitative simulation.

---

## Architectural Workflow

```
[User Natural Language Query]
          |
          v
[Semantic Intent Classifier & Entity Extractor]
          |
          v
[Deterministic Graph Analytics Kernel] (Hop metrics, DOI, Almgren-Chriss, CVaR)
          |
          v
[Audited SEC 10-K RAG Retriever] (Verbatim quote extraction)
          |
          v
[Structured Copilot Response Card]
(Headline Loss + Metrics Grid + SEC Citations + Action Recommendations)
```

---

## Capabilities & Query Classes

1. **Geographic & Counterparty Exposure**:
   - Query: *"What is our total portfolio exposure to TSMC Fab 18 in Taiwan?"*
   - Copilot: Calculates direct and 2nd-order downstream exposures ($-\$18.5\text{M}$ across Nvidia, Apple, and Foxconn), provides exact fab coordinates ($23.116^\circ\text{N}, 120.278^\circ\text{E}$), and cites Nvidia's 10-K foundry risk disclosure.
2. **Inventory Buffer & Safety Stock Vulnerability**:
   - Query: *"Which portfolio holding has the lowest inventory buffer?"*
   - Copilot: Identifies Apple (30 days of buffer) and Ford (42 days) vs Nvidia (85 days), explaining why Apple suffers immediate Hop 1 disruption while Nvidia absorbs the initial 60 days.
3. **Actionable Tail Hedge Recommendations**:
   - Query: *"Recommend an optimal \$500k tail hedge basket."*
   - Copilot: Invokes the Tail-Risk Hedge Optimizer, returning specific contract counts for SOXX OTM Puts and CDX High Yield CDS.
4. **Macro Factor Transmission**:
   - Query: *"How does a 40% oil spike affect our industrials book?"*
   - Copilot: Traces Strait of Hormuz disruption through petrochemical refiners to automotive margins.

---

## Technical Implementation

### File Locations
- **Agent Core**: `backend/app/agents/stress_copilot.py`
- **Unit & Integration Tests**: `backend/tests/integration/test_expansion_services.py::test_copilot_chat_endpoint`
- **API Endpoint**: `POST /api/v1/copilot/chat`
- **Frontend Component**: `frontend/src/components/StressCopilot.tsx`

---

## Verification & Test Coverage
- `backend/tests/integration/test_expansion_services.py::test_copilot_chat_endpoint` (verifies headline, metrics, citations, and mitigations)
