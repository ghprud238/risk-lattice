# Feature 19: Multi-Channel Webhook Alerting System

## Executive Overview
Stress-testing results cannot remain isolated within a static web dashboard. When an overnight batch stress simulation or an intraday SEC filing update detects a breach of institutional Risk Appetite Limits (e.g. Drawdown $> 15\%$ or 99% CVaR $> \$25\text{M}$), risk personnel must be alerted immediately via existing communication channels.

The **Multi-Channel Webhook Alerting System** monitors simulation results against configurable risk appetite limits and dispatches formatted alerts to **Slack (Block Kit)**, **Microsoft Teams (Adaptive Cards)**, and **PagerDuty (Incident Events)**.

---

## Slack Block Kit Alert Architecture

Breach notifications are structured using Slack's interactive Block Kit schema:
1. **Header Block**: Visual alert banner with severity tag (`[CRITICAL RISK APPETITE BREACH]`).
2. **Section Block**: High-level breach headline, scenario name, and total simulated loss.
3. **Fields Block**:
   - Simulated Drawdown vs Limit (e.g., `-23.45%` vs `-15.00%` Limit).
   - 99% Tail CVaR / Expected Shortfall ($-\$29.31\text{M}$).
   - Top Vulnerability Node (e.g., `TSM: -40.0%`).
4. **Context Block**: Audit run hash and timestamp.
5. **Action Buttons**: Direct interactive buttons to *"Inspect in RiskLattice"* and *"Review in Audit Vault"*.

---

## Technical Implementation

### File Locations
- **Service Core**: `backend/app/services/alerting_service.py`
- **Unit & Integration Tests**: `backend/tests/integration/test_expansion_services.py::test_alerting_and_geospatial_endpoints`
- **API Endpoints**:
  - `GET /api/v1/alerts` (List recent alerts)
  - `POST /api/v1/alerts/test` (Trigger test alert dispatch)

### Alert Payload Example
```json
{
  "scenario_name": "Taiwan Strait Blockade & Semiconductor Shock",
  "portfolio_notional": 100000000.0,
  "pnl_loss": -23450000.0,
  "cvar_99": 29312500.0,
  "limit_drawdown_pct": -15.0
}
```

### Generated Slack Block Kit Payload Excerpt
```json
{
  "channel": "#risk-committee-alerts",
  "text": "CRITICAL RISK APPETITE BREACH: Simulated loss -23.45% exceeds limit -15.00%",
  "blocks": [
    {
      "type": "header",
      "text": { "type": "plain_text", "text": "🚨 RISK APPETITE BREACH: Taiwan Strait Blockade", "emoji": true }
    },
    {
      "type": "section",
      "fields": [
        { "type": "mrkdwn", "text": "*Simulated Drawdown:*\n`-23.45%`" },
        { "type": "mrkdwn", "text": "*Risk Appetite Limit:*\n`-15.00%`" },
        { "type": "mrkdwn", "text": "*Total Portfolio Loss:*\n`-$23,450,000`" },
        { "type": "mrkdwn", "text": "*99% Tail CVaR:*\n`-$29,312,500`" }
      ]
    }
  ]
}
```

---

## Verification & Test Coverage
- `backend/tests/integration/test_expansion_services.py::test_alerting_and_geospatial_endpoints` (verifies alert generation and Slack Block Kit payload structure)
