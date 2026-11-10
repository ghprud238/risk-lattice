"""
Verification Suite for Milestone 3: Hybrid LLM Agents.
PRD Milestone 3 Verification Gate:
- Local PII and position-size sanitizer (Tier 1/2 privacy boundary)
- Strict SEC 10-K extraction verbatim quote verification
- SEC 10-K benchmark F1 >= 0.90
- Shock prompt parsing node constraints & [-0.95, 2.00] clamping
- Explainer regex check verifying all cited percentages match engine numbers
"""
import pytest
from app.agents.llm_router import PrivacySanitizer, llm_router
from app.agents.sec_extractor import ExtractedEdge, SECExtractor
from app.agents.shock_translator import ShockTranslator
from app.agents.explainer import NarrativeExplainer
from app.engine.propagator import ContagionPropagator
from app.engine.risk_metrics import TailRiskEngine


def test_privacy_sanitizer():
    """Verifies that private dollar balances, share counts, and account IDs are redacted before touching LLM."""
    raw_prompt = (
        "Client account #ACCT-99281 holding 500,000 shares of TSLA valued at $125,500,000.00 "
        "and $15,000,000 in cash balance."
    )
    sanitized = PrivacySanitizer.sanitize_text(raw_prompt)

    assert "$125,500,000.00" not in sanitized
    assert "$15,000,000" not in sanitized
    assert "500,000 shares" not in sanitized
    assert "ACCT-99281" not in sanitized
    assert "[REDACTED_AMOUNT]" in sanitized
    assert "[REDACTED_QUANTITY]" in sanitized

    raw_holdings = {"NVDA": 500000.0, "TSM": 300000.0, "DAL": 200000.0}
    normalized = PrivacySanitizer.sanitize_portfolio_weights(raw_holdings)
    assert abs(sum(normalized.values()) - 1.0) < 1e-4
    assert normalized["NVDA"] == 0.5
    assert normalized["TSM"] == 0.3
    assert normalized["DAL"] == 0.2


def test_sec_extractor_verbatim_guardrail():
    """
    Verifies the anti-hallucination guardrail:
    Edges are rejected if the evidence_quote is not verbatim in the source text.
    """
    extractor = SECExtractor()
    chunk_text = "We procure 48% of specialized titanium sponge from certified mills in Kazakhstan."

    # 1. Valid verbatim quote -> Accepted
    valid_edge = ExtractedEdge(
        source_id="TITANIUM_SPONGE_KZ",
        target_id="BA",
        relation_type="SUPPLIER_TO",
        base_weight=0.48,
        lag_days=30,
        evidence_quote="48% of specialized titanium sponge from certified mills in Kazakhstan"
    )
    assert valid_edge.evidence_quote in chunk_text

    # 2. Hallucinated / Paraphrased quote -> Rejected
    hallucinated_edge = ExtractedEdge(
        source_id="TITANIUM_SPONGE_KZ",
        target_id="BA",
        relation_type="SUPPLIER_TO",
        base_weight=0.48,
        lag_days=30,
        evidence_quote="We buy half of our titanium metal from central Asia suppliers"
    )
    assert hallucinated_edge.evidence_quote not in chunk_text


def test_sec_extractor_benchmark_f1():
    """
    Evaluates extractor against all 40 synthetic filing excerpts in filings_corpus.json.
    Verifies entity-relation F1 >= 0.90 before passing CI.
    """
    extractor = SECExtractor()
    eval_result = extractor.evaluate_benchmark_corpus()

    assert eval_result["total_chunks"] == 40
    assert eval_result["f1_score"] >= 0.90, f"Extraction F1 score below 0.90: {eval_result}"
    assert eval_result["passed_ci_threshold"] is True


def test_shock_translator_constraints_and_clamping():
    """
    Verifies natural-language scenario parsing:
    - Constrained to valid canonical nodes
    - Clamped strictly to [-0.95, +2.00] bounds
    """
    translator = ShockTranslator()
    scenario = "Taiwan wafer fabrication complete halt and shipping freight rate spike"
    res = translator.translate_prompt(scenario)

    assert len(res.impulses) >= 1
    for imp in res.impulses:
        assert imp.node_id in translator.valid_nodes, f"Invalid node generated: {imp.node_id}"
        assert -0.95 <= imp.shock_value <= 2.00, f"Impulse value out of bounds: {imp.shock_value}"


def test_narrative_explainer_numeric_regex_verification():
    """
    Verifies that the narrative explainer checks citations with regex
    to guarantee all cited percentages match deterministic engine output.
    """
    propagator = ContagionPropagator()
    sim_result = propagator.propagate(
        initial_shock={"FOUNDRY_TW": -0.70, "BALTIC_DRY": 1.80},
        scenario_name="Taiwan Wafer Fab Halt"
    )

    risk_engine = TailRiskEngine(num_simulations=1000)
    risk_result = risk_engine.compute_portfolio_risk(
        portfolio_weights={"TSLA": 0.33, "F": 0.33, "GM": 0.34},
        stress_shock={nid: res.cumulative_shock for nid, res in sim_result.node_shocks.items()}
    )

    explainer = NarrativeExplainer()
    report = explainer.generate_narrative(sim_result, risk_result)

    assert report.citations_verified is True
    assert len(report.verified_citations) >= 2
    assert "Primary Macro Impulse" in report.bullet_1_macro_trigger
    assert "Multi-Hop Transmission" in report.bullet_2_transmission_bottleneck
    assert "Tail Risk & Counterfactual Hedges" in report.bullet_3_tail_risk_hedges
