# Feature 16: Institutional PMS/OMS Adapters & Fed CCAR FR Y-14A Exporter

## Executive Overview
Enterprise risk software must integrate seamlessly with existing institutional infrastructure. Portfolio managers do not manually retype portfolios; they export positions from order and portfolio management systems like **BlackRock Aladdin** or **Bloomberg PORT**. Furthermore, Tier-1 banking organizations and hedge funds subject to Federal Reserve oversight must report scenario results in statutory formats.

RiskLattice provides automated parsers for institutional PMS/OMS files and generates regulatory-grade **Federal Reserve CCAR Form FR Y-14A Schedule A (Trading & Counterparty Mark-to-Market Loss)** submission packets.

---

## Supported Institutional Formats

### 1. BlackRock Aladdin CSV Parser
Parses Aladdin export files containing:
- Security Identifiers: CUSIP, ISIN, SEDOL, Ticker
- Asset Types: Equities, Options, Corporate Debt, CDS
- Market Value (USD), Weight, Delta-adjusted Notional, Duration, Spread01
- Normalized automatically into RiskLattice `Position` dataclasses.

### 2. Bloomberg PORT JSON Parser
Parses Bloomberg PORT portfolio attribution and exposure reports, resolving Bloomberg FIGI and proprietary ticker conventions.

### 3. Federal Reserve CCAR Form FR Y-14A Schedule A Exporter
Generates compliance-ready regulatory schedules required under the annual Comprehensive Capital Analysis and Review (CCAR) exercise:
- **Schedule A.1**: Trading Mark-to-Market (MtM) Shock Losses.
- **Schedule A.2**: Counterparty Default and Credit Valuation Adjustment (CVA) Losses.
- **Schedule A.3**: Multi-Tier Cascade Factor Attributions.
- **Schedule A.4**: 99% Expected Shortfall (CVaR) and 95% Value at Risk under Supervisory Severely Adverse conditions.

---

## Technical Implementation

### File Locations
- **Service Core**: `backend/app/services/institutional_adapters_service.py`
- **Unit & Integration Tests**: `backend/tests/integration/test_expansion_services.py::test_institutional_adapters_and_ccar_endpoint`
- **API Endpoints**:
  - `POST /api/v1/pms/aladdin/import`
  - `POST /api/v1/regulatory/ccar/export`

### Sample FR Y-14A Regulatory Export
```json
{
  "report_title": "Federal Reserve Form FR Y-14A Schedule A (Trading & Counterparty MtM Loss)",
  "reporting_institution": "Citadel Global Equities & Quantitative Strategies",
  "as_of_date": "2026-11-15",
  "supervisory_scenario": "Supervisory Severely Adverse (Taiwan Strait Maritime Interruption)",
  "portfolio_summary": {
    "gross_notional_usd": 100000000.0,
    "trading_mtm_loss_usd": -23450000.0,
    "trading_loss_pct": -23.45,
    "cvar_99_loss_usd": 29312500.0,
    "var_95_loss_usd": 21200000.0
  },
  "fr_y14a_line_items": [
    { "line_number": "1.A.1", "description": "Equity Cash Equities MtM Impact", "amount_usd": -8000000.0 },
    { "line_number": "1.A.2", "description": "Equity Derivatives & Convexity Loss", "amount_usd": -11200000.0 },
    { "line_number": "1.B.1", "description": "Corporate Credit Spread Widening & CDS", "amount_usd": -3250000.0 },
    { "line_number": "1.C.1", "description": "Liquidity Haircut & Almgren-Chriss Slippage", "amount_usd": -1000000.0 }
  ]
}
```

---

## Verification & Test Coverage
- `backend/tests/integration/test_expansion_services.py::test_institutional_adapters_and_ccar_endpoint` (verifies line items and CCAR compliance)
