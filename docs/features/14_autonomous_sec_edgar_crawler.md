# Feature 14: Autonomous SEC EDGAR 10-K/8-K Feed Monitor & Ingestion Engine

## Executive Overview
Corporate supply chains are not static; vendor relationships, sole-source concentration, and facility locations change with every quarterly and annual SEC disclosure. Manual data collection cannot keep pace with thousands of public filings.

RiskLattice incorporates an **Autonomous SEC EDGAR Feed Monitor** that continuously polls SEC filings (Forms 10-K, 10-Q, and 8-K), isolates relevant disclosure sections (Item 1A Risk Factors, Item 7 MD&A, and Item 1 Business Description), and extracts counterparty dependencies with confidence scoring and verbatim quote verification guardrails.

---

## Architectural Workflow

```
[SEC EDGAR Feed] ---> [Filing Ingestion] ---> [Section Filter] ---> [Semantic Extractor]
                                                                            |
                                                                            v
[Calibrated Graph] <--- [Confidence Scoring] <--- [Verbatim Quote Matcher] <+
```

### 1. Section Filtering
The crawler targets high-information sections of corporate disclosures:
- **Item 1 (Business)**: Principal suppliers, manufacturing agreements, sole-source arrangements.
- **Item 1A (Risk Factors)**: Geographic concentration risks, Taiwan Strait exposure, raw material availability.
- **Item 7 (MD&A)**: Supply disruptions, inventory write-downs, lead-time delays.

### 2. Verbatim Quote Guardrail (ADR-003)
To eliminate LLM hallucinations, every candidate edge extracted must match an exact substring from the source filing. If the candidate citation does not appear verbatim in the filing text, the edge is discarded immediately.

### 3. Confidence Scoring
Discovered edges are assigned confidence scores based on language explicitness:
- **High (0.85 - 1.00)**: Explicit named counterparty with quantifiable percentage (e.g., *"TSMC manufactures over 90% of our accelerated compute silicon"*).
- **Medium (0.65 - 0.84)**: Explicit named counterparty with qualitative dependence (e.g., *"We rely on Foxconn for the assembly of our flagship hardware"*).
- **Low (< 0.65)**: Generalized industry or geographic exposure without specific counterparty identification.

---

## Technical Implementation

### File Locations
- **Service Core**: `backend/app/services/edgar_crawler_service.py`
- **Agent Extractor**: `backend/app/agents/sec_extractor.py`
- **Unit Tests**: `backend/tests/test_llm.py::test_sec_extractor_verbatim_guardrail`
- **Integration Tests**: `backend/tests/integration/test_expansion_services.py::test_edgar_crawler_endpoints`
- **API Endpoints**:
  - `GET /api/v1/edgar/status`
  - `POST /api/v1/edgar/ingest`

### REST API Example
```json
{
  "ticker": "NVDA",
  "filing_type": "10-K",
  "accession_number": "0001045810-24-000029",
  "filing_text": "...We rely on Taiwan Semiconductor Manufacturing Company Limited (TSMC) to manufacture our GPU architectures..."
}
```

### Response:
```json
{
  "ticker": "NVDA",
  "discovered_edges": [
    {
      "source_id": "TSM",
      "target_id": "NVDA",
      "dependency_type": "FOUNDRY_WAFER",
      "weight": 0.38,
      "confidence": 0.94,
      "verbatim_quote": "We rely on Taiwan Semiconductor Manufacturing Company Limited (TSMC) to manufacture our GPU architectures",
      "sec_source": "Item 1A: Risk Factors"
    }
  ]
}
```

---

## Verification & Test Coverage
- `backend/tests/test_llm.py::test_sec_extractor_verbatim_guardrail`
- `backend/tests/test_llm.py::test_sec_extractor_benchmark_f1` (benchmarks extraction accuracy against gold dataset)
- `backend/tests/integration/test_expansion_services.py::test_edgar_crawler_endpoints`
