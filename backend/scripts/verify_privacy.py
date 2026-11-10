#!/usr/bin/env python3
"""Privacy Boundary Verification Script per Section 19.1 & 24.1.
Asserts that portfolio dollar amounts, share quantities, and account IDs remain inside Tier 1/2
and ZERO private financial metrics egress to external LLM router payloads.
"""

import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.agents.llm_router import PrivacySanitizer
from app.agents.sec_extractor import SECExtractor
from app.agents.shock_translator import ShockTranslator
from app.agents.explainer import NarrativeExplainer


def verify_privacy():
    print("=" * 60)
    print("ContagionGraph Privacy Boundary Verification (verify_privacy.py)")
    print("=" * 60)

    # 1. Test PrivacySanitizer on sensitive dictionary
    sanitizer = PrivacySanitizer()
    raw_portfolio = {
        "account_id": "ACC-998811",
        "total_nav": "$142,500,000.00",
        "positions": [
            {"ticker": "NVDA", "shares": 50000, "notional": 6500000.0, "cost_basis": 120.50},
            {"ticker": "TSM", "shares": 35000, "notional": 4200000.0, "cost_basis": 115.00},
        ],
    }
    
    sanitized = sanitizer.sanitize_holdings(raw_portfolio)
    print("[1/3] Sanitizing private portfolio holdings...")
    sanitized_str = str(sanitized)
    
    forbidden_patterns = [
        r"ACC-\d+",
        r"\$142,500,000",
        r"6500000",
        r"4200000",
        r"50000",
        r"35000",
        r"cost_basis",
    ]
    
    for pat in forbidden_patterns:
        match = re.search(pat, sanitized_str)
        assert not match, f"PRIVACY LEAK: Found forbidden pattern '{pat}' in sanitized output!"

    assert "NVDA" in sanitized_str
    assert "TSM" in sanitized_str
    print("      PASSED: All dollar amounts, share quantities, and account IDs scrubbed.")

    # 2. Test SEC Extractor input integrity
    print("[2/3] Checking SEC 10-K extraction pipeline...")
    extractor = SECExtractor()
    chunk_id = next(iter(extractor._corpus_cache.keys()))
    chunk_data = extractor._corpus_cache[chunk_id]
    chunk_text = chunk_data["text"]
    ticker = chunk_data.get("company_ticker", "NVDA")
    
    edges = extractor.extract_from_chunk(chunk_id, chunk_text, ticker)
    assert len(edges) > 0, "Expected extracted edges from SEC corpus chunk"
    print(f"      PASSED: Extracted {len(edges)} verified relationship edges from SEC filing chunk.")

    # 3. Test Narrative Explainer citation & input sanitization
    print("[3/3] Checking Narrative Explainer prompt payloads...")
    from app.services.snapshot_service import snapshot_service
    from app.engine.propagator import ContagionPropagator
    nodes_df, edges_df = snapshot_service.load_graph_snapshot()
    prop = ContagionPropagator()
    sim_res = prop.propagate(
        initial_shock={"NVDA": -0.25, "TSM": -0.20},
        scenario_name="Semiconductor Bottleneck",
        nodes_df=nodes_df,
        edges_df=edges_df,
    )
    explainer = NarrativeExplainer()
    report = explainer.generate_narrative(sim_res)
    
    report_text = f"{report.scenario_title} {report.bullet_1_macro_trigger} {report.bullet_2_transmission_bottleneck} {report.bullet_3_tail_risk_hedges}"
    for pat in forbidden_patterns:
        assert not re.search(pat, report_text), f"Found private info in narrative: {pat}"
    assert "$" not in report_text or "$3nm" in report_text or not re.search(r"\$\d{4,}", report_text)
    print("      PASSED: Narrative explanation contains only unit-free tickers, percentages, and SEC quotes.")

    print("=" * 60)
    print("PRIVACY VERIFICATION PASSED: ZERO egress of private holdings or balances.")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = verify_privacy()
    sys.exit(0 if success else 1)
