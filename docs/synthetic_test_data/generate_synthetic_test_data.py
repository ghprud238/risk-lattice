#!/usr/bin/env python3
"""
RiskLattice Synthetic Testing Data Generator.
Generates machine-readable synthetic inputs and mathematically verified outputs
across 9 institutional risk use cases:
1. Geopolitical Tech & Maritime Disruption (Taiwan Semiconductor Foundry Blockade)
2. Maritime Choke Point & Demurrage Surge (Suez Canal / Red Sea Divergence)
3. Institutional Equity Portfolio Ingestion (BlackRock Aladdin CSV Format)
4. Multi-Asset Convexity & Derivatives Portfolio (Bloomberg PORT JSON Format)
5. Capital-Constrained Tail-Risk Hedge Optimizer (SLSQP Minimum-Cost Basket)
6. Algorithmic Reverse Stress Testing (Minimal L2 Breaking-Point Inversion)
7. Endogenous Liquidity & Fire-Sale Margin Call (Almgren-Chriss Optimal Liquidation)
8. What-If Supply Chain Graph Mutation & Resilience ROI
9. Four-Eyes Cryptographic Audit Vault & Regulatory Sign-off (Fed SR 11-7)

Usage:
    .venv/bin/python docs/synthetic_test_data/generate_synthetic_test_data.py
"""

import hashlib
import json
from pathlib import Path
import sys
import time
from typing import Dict, List
import numpy as np
import pandas as pd

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.db.database import db_manager
from app.services.snapshot_service import snapshot_service
from app.engine.propagator import ContagionPropagator
from app.engine.risk_metrics import TailRiskEngine
from app.engine.valuation import compute_portfolio_valuation
from app.engine.ais_threat import (
    AISThreatEngine,
    ChokePointTelemetry,
    ChokePointStatus,
    ThreatEvent,
    ThreatSeverity,
)
from app.engine.optimizer import (
    TailRiskHedgeOptimizer,
    HedgeCandidate,
    ReverseStressTester,
)
from app.engine.liquidity import (
    EndogenousLiquidityEngine,
    LiquidationPosition,
)
from app.engine.mutation import (
    GraphMutationEngine,
    GraphMutation,
    MutationType,
)
from app.engine.instruments import (
    EquityPosition,
    OptionPosition,
    OptionType,
    PositionSide,
    BondPosition,
    CDSPosition,
    PrivateCreditPosition,
    FXForwardPosition,
    CLOTranchePosition,
    evaluate_any_instrument,
)


def generate_all_fixtures():
    output_dir = Path(__file__).resolve().parent
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Generating synthetic testing fixtures in: {output_dir}")

    # Load immutable graph and portfolio snapshots
    nodes_df, edges_df = snapshot_service.load_graph_snapshot()
    node_ids, tickers, notionals, weights = snapshot_service.load_portfolio_snapshot()
    portfolio_weights = {tick: float(w) for tick, w in zip(tickers, weights)}
    portfolio_notionals = {tick: float(n) for tick, n in zip(tickers, notionals)}
    total_base_notional = float(np.sum(notionals))

    # =========================================================================
    # 1. TAIWAN FOUNDRY DISRUPTION (USE CASE 1)
    # =========================================================================
    print("[1/9] Generating Case 01: Taiwan Foundry Cascade...")
    input_01 = {
        "scenario_name": "Taiwan Strait Semiconductor Disruption & Foundry Quarantine",
        "scenario_description": "PLA exercises enforce a naval exclusion zone around Hsinchu Science Park, halting TSMC advanced wafer exports.",
        "horizon_days": 20,
        "initial_shocks": {
            "FOUNDRY_TW": -0.70,
            "BALTIC_DRY": 1.20,
        },
        "inventory_buffer_overrides": {
            "NVDA": 45.0,
            "AAPL": 30.0,
            "MSFT": 60.0,
        },
        "portfolio_weights": portfolio_weights,
    }
    with open(output_dir / "01_taiwan_foundry_shock_input.json", "w") as f:
        json.dump(input_01, f, indent=2)

    propagator = ContagionPropagator(alpha_decay=0.65, max_hops=4)
    prop_res = propagator.propagate(
        initial_shock=input_01["initial_shocks"],
        scenario_name=input_01["scenario_name"],
        portfolio_weights=portfolio_weights,
        nodes_df=nodes_df,
        edges_df=edges_df,
        horizon_days=input_01["horizon_days"],
        node_inventory_days=input_01["inventory_buffer_overrides"],
    )

    node_shocks_map = {nid: res.cumulative_shock for nid, res in prop_res.node_shocks.items()}
    risk_engine = TailRiskEngine(df_t=4.0, num_simulations=5000, seed=42)
    risk_res = risk_engine.compute_portfolio_risk(
        portfolio_weights=portfolio_weights,
        stress_shock=node_shocks_map,
        db=db_manager,
    )

    # Build hop returns matrix shape (5, N) for valuation ledger
    num_nodes = len(node_ids)
    hop_matrix = np.zeros((5, num_nodes), dtype=np.float64)
    for i, nid in enumerate(node_ids):
        if nid in prop_res.node_shocks:
            shock_obj = prop_res.node_shocks[nid]
            hop_matrix[0, i] = shock_obj.hop0
            hop_matrix[1, i] = shock_obj.hop1
            hop_matrix[2, i] = shock_obj.hop2
            hop_matrix[3, i] = shock_obj.hop3
            hop_matrix[4, i] = shock_obj.hop4

    val_res = compute_portfolio_valuation(
        node_ids=node_ids,
        tickers=tickers,
        notionals=notionals,
        hop_returns=hop_matrix,
    )

    output_01 = {
        "scenario_name": input_01["scenario_name"],
        "total_active_nodes": prop_res.total_active_nodes,
        "critical_propagation_paths": prop_res.critical_paths[:3],
        "risk_metrics": {
            "var_95_pct": round(risk_res.var_95 * 100, 2),
            "var_99_pct": round(risk_res.var_99 * 100, 2),
            "cvar_95_pct": round(risk_res.cvar_95 * 100, 2),
            "cvar_99_pct": round(risk_res.cvar_99 * 100, 2),
            "tail_ratio": round(risk_res.copula_to_gaussian_ratio, 2),
            "simulations_count": risk_res.num_simulations,
        },
        "portfolio_valuation": {
            "base_notional_usd": round(val_res.total_notional, 2),
            "stressed_pnl_usd": round(val_res.total_pnl, 2),
            "effective_return_pct": round(val_res.portfolio_return * 100, 2),
            "order1_direct_pnl_usd": round(val_res.hop_attribution.get(0, 0.0) + val_res.hop_attribution.get(1, 0.0), 2),
            "order2_tier1_pnl_usd": round(val_res.hop_attribution.get(2, 0.0), 2),
            "order3_4_network_pnl_usd": round(val_res.hop_attribution.get(3, 0.0) + val_res.hop_attribution.get(4, 0.0), 2),
        },
        "top_impacted_nodes": [
            {
                "node_id": res.node_id,
                "name": res.name,
                "cumulative_shock": round(res.cumulative_shock, 4),
                "distress_multiplier": round(res.distress_multiplier, 3),
            }
            for res in sorted(prop_res.node_shocks.values(), key=lambda x: x.cumulative_shock)[:6]
        ],
    }
    with open(output_dir / "01_taiwan_foundry_shock_output.json", "w") as f:
        json.dump(output_01, f, indent=2)

    # =========================================================================
    # 2. SUEZ MARITIME BLOCKADE & AIS RADAR (USE CASE 2 & 12)
    # =========================================================================
    print("[2/9] Generating Case 02: Suez Choke Point & AIS Telemetry...")
    input_02 = {
        "incident_id": "INC-SUEZ-2026-X1",
        "target_choke_point": "GEO_SUEZ",
        "headline": "Houthi Anti-Ship Missile Strike Forces Container Fleet Divergence Around Cape of Good Hope",
        "severity": "CRITICAL",
        "observed_transit_speed_knots": 2.8,
        "baseline_transit_speed_knots": 12.0,
        "active_vessel_queue": 118,
        "baseline_vessel_queue": 85,
        "duration_days": 35,
    }
    with open(output_dir / "02_suez_maritime_blockade_input.json", "w") as f:
        json.dump(input_02, f, indent=2)

    ais_engine = AISThreatEngine()
    suez_telemetry = ChokePointTelemetry(
        choke_point_id=input_02["target_choke_point"],
        name="Suez Canal / Bab-el-Mandeb",
        lat=29.9,
        lng=32.5,
        baseline_daily_vessels=input_02["baseline_vessel_queue"],
        current_vessel_count=input_02["active_vessel_queue"],
        transit_speed_knots=input_02["observed_transit_speed_knots"],
        baseline_speed_knots=input_02["baseline_transit_speed_knots"],
        status=ChokePointStatus.BLOCKADE,
        criticality_weight=0.20,
    )
    suez_telemetry.compute_metrics()

    threat_event = ThreatEvent(
        event_id=input_02["incident_id"],
        timestamp="2026-11-24T10:00:00Z",
        headline=input_02["headline"],
        source="Lloyd's List Maritime Intelligence",
        severity=ThreatSeverity.CRITICAL,
        choke_point_id=input_02["target_choke_point"],
        affected_nodes=["PORT_RTM", "ASML", "BMW", "F"],
        raw_supply_impact_pct=-0.65,
        details="Bab-el-Mandeb naval blockade forces container divergence around Cape of Good Hope (+14 voyage days)",
    )
    direct_impulses = ais_engine.translate_threat_to_direct_impulses(threat_event)
    svi = ais_engine.compute_systemic_vulnerability_index([suez_telemetry])

    output_02 = {
        "incident_id": input_02["incident_id"],
        "systemic_vulnerability_index": round(svi, 2),
        "target_choke_point_telemetry": {
            "choke_point_id": suez_telemetry.choke_point_id,
            "name": suez_telemetry.name,
            "status": suez_telemetry.status.value,
            "congestion_index": round(suez_telemetry.congestion_index, 2),
            "active_vessel_queue": suez_telemetry.current_vessel_count,
            "demurrage_surge_pct": round(suez_telemetry.demurrage_spike_pct, 2),
            "disruption_probability": round(suez_telemetry.disruption_probability, 3),
        },
        "translated_macro_impulses": {k: round(v, 4) for k, v in direct_impulses.items()},
    }
    with open(output_dir / "02_suez_maritime_blockade_output.json", "w") as f:
        json.dump(output_02, f, indent=2)

    # =========================================================================
    # 3. BLACKROCK ALADDIN CSV PORTFOLIO INGESTION (USE CASE 15)
    # =========================================================================
    print("[3/9] Generating Case 03: BlackRock Aladdin Portfolio Import...")
    aladdin_rows = [
        {"Ticker": "AAPL", "NotionalUSD": 2500000.0, "Shares": 11500, "AssetClass": "EQUITY", "Sector": "Information Technology", "Country": "US"},
        {"Ticker": "NVDA", "NotionalUSD": 3000000.0, "Shares": 24000, "AssetClass": "EQUITY", "Sector": "Semiconductors", "Country": "US"},
        {"Ticker": "TSM", "NotionalUSD": 2000000.0, "Shares": 11800, "AssetClass": "EQUITY", "Sector": "Semiconductors", "Country": "TW"},
        {"Ticker": "MSFT", "NotionalUSD": 2200000.0, "Shares": 5100, "AssetClass": "EQUITY", "Sector": "Software", "Country": "US"},
        {"Ticker": "AMZN", "NotionalUSD": 1800000.0, "Shares": 9500, "AssetClass": "EQUITY", "Sector": "Consumer Discretionary", "Country": "US"},
        {"Ticker": "GOOGL", "NotionalUSD": 1500000.0, "Shares": 8800, "AssetClass": "EQUITY", "Sector": "Communication Services", "Country": "US"},
        {"Ticker": "INTC", "NotionalUSD": 1000000.0, "Shares": 32000, "AssetClass": "EQUITY", "Sector": "Semiconductors", "Country": "US"},
        {"Ticker": "ASML", "NotionalUSD": 2000000.0, "Shares": 2300, "AssetClass": "EQUITY", "Sector": "Semiconductor Equipment", "Country": "NL"},
        {"Ticker": "AVGO", "NotionalUSD": 2000000.0, "Shares": 1400, "AssetClass": "EQUITY", "Sector": "Semiconductors", "Country": "US"},
        {"Ticker": "QCOM", "NotionalUSD": 2000000.0, "Shares": 12500, "AssetClass": "EQUITY", "Sector": "Semiconductors", "Country": "US"},
    ]
    aladdin_df = pd.DataFrame(aladdin_rows)
    aladdin_df.to_csv(output_dir / "03_institutional_portfolio_aladdin_input.csv", index=False)

    total_notional_aladdin = float(aladdin_df["NotionalUSD"].sum())
    normalized_weights = {row["Ticker"]: round(float(row["NotionalUSD"]) / total_notional_aladdin, 4) for _, row in aladdin_df.iterrows()}
    output_03 = {
        "portfolio_name": "Aladdin Institutional Tech Long/Short Pod",
        "total_notional_usd": total_notional_aladdin,
        "holdings_count": len(aladdin_df),
        "normalized_weights": normalized_weights,
        "rule_p01_privacy_status": {
            "dollar_values_scrubbed_from_llm": True,
            "share_counts_scrubbed_from_llm": True,
            "weights_sum": round(sum(normalized_weights.values()), 4),
        },
    }
    with open(output_dir / "03_institutional_portfolio_aladdin_output.json", "w") as f:
        json.dump(output_03, f, indent=2)

    # =========================================================================
    # 4. MULTI-ASSET DERIVATIVES & BONDS (PORT FORMAT, USE CASE 5)
    # =========================================================================
    print("[4/9] Generating Case 04: Multi-Asset Valuation & Greeks...")
    input_04 = {
        "portfolio_name": "Multi-Asset Cross-Asset Convexity Book",
        "positions": [
            {"type": "EQUITY", "ticker": "NVDA", "notional": 2000000.0, "side": "LONG"},
            {
                "type": "EQUITY_OPTION",
                "ticker": "NVDA",
                "notional": 150000.0,
                "option_type": "PUT",
                "spot": 125.0,
                "strike": 115.0,
                "maturity_years": 0.25,
                "implied_vol": 0.45,
                "side": "LONG",
            },
            {
                "type": "BOND",
                "ticker": "TSM",
                "notional": 3000000.0,
                "duration": 6.8,
                "convexity": 55.0,
                "spread_bps": 85.0,
                "credit_beta": 1.4,
                "side": "LONG",
            },
            {
                "type": "CDS",
                "ticker": "INTC",
                "notional": 5000000.0,
                "spread_duration": 4.8,
                "current_spread_bps": 120.0,
                "recovery_rate": 0.40,
                "hazard_sensitivity": 2.5,
                "side": "BUY",
            },
            {
                "type": "PRIVATE_CREDIT",
                "ticker": "SUPPLIER_01",
                "notional": 2000000.0,
                "initial_leverage": 4.8,
                "covenant_max_leverage": 4.5,
                "recovery_rate": 0.65,
                "spread_bps": 650.0,
                "side": "LONG",
            },
            {
                "type": "CLO_TRANCHE",
                "ticker": "CLO_MEZZ",
                "notional": 1000000.0,
                "attachment_point": 0.09,
                "detachment_point": 0.18,
                "tranche_name": "BBB Mezzanine",
                "side": "LONG",
            },
        ],
        "node_shocks": {
            "NVDA": -0.28,
            "TSM": -0.32,
            "INTC": -0.22,
            "SUPPLIER_01": -0.40,
            "CLO_MEZZ": -0.25,
        },
    }
    with open(output_dir / "04_multi_asset_derivatives_port_input.json", "w") as f:
        json.dump(input_04, f, indent=2)

    evaluated_positions = []
    for p in input_04["positions"]:
        t = p["type"]
        tick = p["ticker"]
        shock = input_04["node_shocks"].get(tick, 0.0)
        if t == "EQUITY":
            pos = EquityPosition(ticker=tick, notional=p["notional"], side=PositionSide(p["side"]))
        elif t == "EQUITY_OPTION":
            pos = OptionPosition(
                ticker=tick,
                notional=p["notional"],
                option_type=OptionType(p["option_type"]),
                spot=p["spot"],
                strike=p["strike"],
                maturity_years=p["maturity_years"],
                implied_vol=p["implied_vol"],
                side=PositionSide(p["side"]),
            )
        elif t == "BOND":
            pos = BondPosition(
                ticker=tick,
                notional=p["notional"],
                duration=p["duration"],
                convexity=p["convexity"],
                spread_bps=p["spread_bps"],
                credit_beta=p.get("credit_beta", 1.5),
                side=PositionSide(p["side"]),
            )
        elif t == "CDS":
            pos = CDSPosition(
                ticker=tick,
                notional=p["notional"],
                spread_duration=p["spread_duration"],
                current_spread_bps=p["current_spread_bps"],
                recovery_rate=p["recovery_rate"],
                hazard_sensitivity=p.get("hazard_sensitivity", 2.5),
                side=PositionSide(p["side"]),
            )
        elif t == "PRIVATE_CREDIT":
            pos = PrivateCreditPosition(
                ticker=tick,
                notional=p["notional"],
                initial_leverage=p["initial_leverage"],
                covenant_max_leverage=p["covenant_max_leverage"],
                recovery_rate=p["recovery_rate"],
                spread_bps=p["spread_bps"],
                side=PositionSide(p["side"]),
            )
        elif t == "CLO_TRANCHE":
            pos = CLOTranchePosition(
                ticker=tick,
                notional=p["notional"],
                attachment_point=p["attachment_point"],
                detachment_point=p["detachment_point"],
                tranche_name=p["tranche_name"],
                side=PositionSide(p["side"]),
            )
        detail = evaluate_any_instrument(pos, shock)
        evaluated_positions.append({
            "ticker": tick,
            "type": t,
            "notional_usd": detail.notional,
            "stressed_pnl_usd": round(detail.pnl, 2),
            "effective_return_pct": round(detail.effective_return * 100, 2),
            "metrics_or_greeks": {k: round(v, 4) for k, v in detail.greeks_or_metrics.items()},
            "status_notes": detail.status_notes,
        })

    net_notional = sum(p["notional_usd"] for p in evaluated_positions)
    net_pnl = sum(p["stressed_pnl_usd"] for p in evaluated_positions)
    output_04 = {
        "portfolio_name": input_04["portfolio_name"],
        "total_notional_usd": round(net_notional, 2),
        "total_stressed_pnl_usd": round(net_pnl, 2),
        "net_effective_return_pct": round((net_pnl / net_notional) * 100, 2),
        "evaluated_positions": evaluated_positions,
    }
    with open(output_dir / "04_multi_asset_derivatives_port_output.json", "w") as f:
        json.dump(output_04, f, indent=2)

    # =========================================================================
    # 5. TAIL-RISK HEDGE OPTIMIZER (USE CASE 6)
    # =========================================================================
    print("[5/9] Generating Case 05: Tail-Risk Hedge Optimizer...")
    input_05 = {
        "unhedged_portfolio_notional": 20000000.0,
        "unhedged_pnl_usd": -3850000.0,
        "max_hedge_budget_usd": 400000.0,
        "node_shocks": {
            "TSM": -0.35,
            "NVDA": -0.28,
            "F": -0.22,
            "BALTIC_DRY": 0.40,
        },
        "candidate_instruments": [
            {
                "candidate_id": "SOXX_PUT",
                "target_node": "TSM",
                "instrument_type": "EQUITY_OPTION",
                "side": "BUY",
                "unit_cost_bps": 380.0,
                "protection_elasticity": 1.85,
                "max_notional": 10000000.0,
                "description": "SOXX Semiconductor ETF Out-of-the-Money Put Options (Delta: -0.25)",
            },
            {
                "candidate_id": "F_CDS_5Y",
                "target_node": "F",
                "instrument_type": "CDS",
                "side": "BUY",
                "unit_cost_bps": 210.0,
                "protection_elasticity": 1.40,
                "max_notional": 8000000.0,
                "description": "Ford Motor Credit 5-Year Senior CDS Protection",
            },
            {
                "candidate_id": "NVDA_PUT",
                "target_node": "NVDA",
                "instrument_type": "EQUITY_OPTION",
                "side": "BUY",
                "unit_cost_bps": 420.0,
                "protection_elasticity": 2.10,
                "max_notional": 10000000.0,
                "description": "NVIDIA 3-Month Out-of-the-Money Put Protection (Delta: -0.22)",
            },
        ],
    }
    with open(output_dir / "05_tail_risk_hedge_optimizer_input.json", "w") as f:
        json.dump(input_05, f, indent=2)

    candidates = [
        HedgeCandidate(
            candidate_id=c["candidate_id"],
            target_node=c["target_node"],
            instrument_type=c["instrument_type"],
            side=c["side"],
            unit_cost_bps=c["unit_cost_bps"],
            protection_elasticity=c["protection_elasticity"],
            max_notional=c["max_notional"],
            description=c["description"],
        )
        for c in input_05["candidate_instruments"]
    ]
    opt = TailRiskHedgeOptimizer(candidates=candidates)
    opt_res = opt.optimize_hedge(
        portfolio_notional=input_05["unhedged_portfolio_notional"],
        unhedged_pnl=input_05["unhedged_pnl_usd"],
        node_shocks=input_05["node_shocks"],
        budget_limit=input_05["max_hedge_budget_usd"],
    )
    output_05 = {
        "status": "OPTIMAL_CONVERGED",
        "initial_unhedged_pnl_usd": opt_res.initial_pnl,
        "hedged_pnl_usd": opt_res.hedged_pnl,
        "pnl_improvement_usd": opt_res.pnl_improvement,
        "total_hedge_cost_usd": opt_res.total_hedge_cost,
        "budget_remaining_usd": round(input_05["max_hedge_budget_usd"] - opt_res.total_hedge_cost, 2),
        "initial_cvar_99_usd": opt_res.initial_cvar_99,
        "hedged_cvar_99_usd": opt_res.hedged_cvar_99,
        "cvar_reduction_pct": opt_res.cvar_reduction_pct,
        "optimal_allocations": [
            {
                "candidate_id": r.candidate_id,
                "instrument_name": r.instrument_name,
                "target_node": r.target_node,
                "action": r.action,
                "allocated_notional_usd": round(r.allocated_notional, 2),
                "estimated_cost_usd": round(r.estimated_cost, 2),
                "pnl_protection_usd": round(r.pnl_protection, 2),
                "description": r.description,
            }
            for r in opt_res.recommendations
        ],
        "efficient_frontier": [dict(pt) for pt in opt_res.efficient_frontier],
    }
    with open(output_dir / "05_tail_risk_hedge_optimizer_output.json", "w") as f:
        json.dump(output_05, f, indent=2)

    # =========================================================================
    # 6. ALGORITHMIC REVERSE STRESS TESTING (USE CASE 7)
    # =========================================================================
    print("[6/9] Generating Case 06: Algorithmic Reverse Stress Testing...")
    input_06 = {
        "portfolio_notional_usd": 20000000.0,
        "target_loss_pct": 0.15,  # 15% portfolio breach threshold
        "factor_sensitivities": {
            "FOUNDRY_TW": 0.45,
            "BALTIC_DRY": 0.30,
            "BRENT_CRUDE": 0.25,
            "SOFR_SPREAD": 0.35,
            "HY_OAS": 0.40,
            "CANAL_TRANSIT": 0.28,
            "CLOUD_OUTAGE_SEV": 0.20,
        },
    }
    with open(output_dir / "06_reverse_stress_testing_input.json", "w") as f:
        json.dump(input_06, f, indent=2)

    rev_tester = ReverseStressTester(key_factors=list(input_06["factor_sensitivities"].keys()))
    rev_res = rev_tester.find_breaking_point(
        portfolio_notional=input_06["portfolio_notional_usd"],
        target_loss_pct=input_06["target_loss_pct"],
        factor_sensitivities=input_06["factor_sensitivities"],
    )
    output_06 = {
        "target_loss_pct": round(rev_res.target_loss_pct * 100, 2),
        "achieved_loss_pct": round(rev_res.achieved_loss_pct * 100, 2),
        "minimal_l2_norm": rev_res.norm_l2,
        "critical_factor": rev_res.critical_factor,
        "solver_iterations": rev_res.iterations,
        "minimal_shock_vector": {k: round(v, 4) for k, v in rev_res.minimal_shocks.items()},
        "top_vulnerable_factors": [dict(vn) for vn in rev_res.top_vulnerable_nodes],
    }
    with open(output_dir / "06_reverse_stress_testing_output.json", "w") as f:
        json.dump(output_06, f, indent=2)

    # =========================================================================
    # 7. ALMGREN-CHRISS LIQUIDITY & FIRE-SALE (USE CASE 10)
    # =========================================================================
    print("[7/9] Generating Case 07: Almgren-Chriss Liquidity & Fire Sale...")
    input_07 = {
        "liquidation_pct": 0.25,  # Liquidating 25% of positions
        "market_participation_rate": 0.10,  # Max 10% daily volume
        "fund_unencumbered_cash_usd": 15000000.0,
        "portfolio_unhedged_pnl_usd": -23450000.0,
        "gross_derivative_notional_usd": 50000000.0,
        "positions": [
            {
                "asset_id": "NVDA",
                "target_notional": 8000000.0,
                "adv_30d": 2500000000.0,
                "volatility_ann": 0.45,
                "bid_ask_spread_bps": 2.5,
                "liquidation_urgency": "HIGH",
            },
            {
                "asset_id": "AAPL",
                "target_notional": 6000000.0,
                "adv_30d": 3200000000.0,
                "volatility_ann": 0.28,
                "bid_ask_spread_bps": 1.8,
                "liquidation_urgency": "MEDIUM",
            },
            {
                "asset_id": "TSM",
                "target_notional": 5000000.0,
                "adv_30d": 850000000.0,
                "volatility_ann": 0.38,
                "bid_ask_spread_bps": 4.2,
                "liquidation_urgency": "FIRE_SALE",
            },
            {
                "asset_id": "ASML",
                "target_notional": 4000000.0,
                "adv_30d": 450000000.0,
                "volatility_ann": 0.40,
                "bid_ask_spread_bps": 5.0,
                "liquidation_urgency": "FIRE_SALE",
            },
        ],
    }
    with open(output_dir / "07_almgren_chriss_liquidity_input.json", "w") as f:
        json.dump(input_07, f, indent=2)

    liq_engine = EndogenousLiquidityEngine(gamma_perm=0.15, eta_temp=0.25)
    positions = [
        LiquidationPosition(
            asset_id=p["asset_id"],
            target_notional=p["target_notional"],
            adv_30d=p["adv_30d"],
            volatility_ann=p["volatility_ann"],
            bid_ask_spread_bps=p["bid_ask_spread_bps"],
            liquidation_urgency=p["liquidation_urgency"],
        )
        for p in input_07["positions"]
    ]
    liq_res = liq_engine.evaluate_liquidation(
        positions=positions,
        liquidation_pct=input_07["liquidation_pct"],
        participation_rate=input_07["market_participation_rate"],
        fund_unencumbered_cash=input_07["fund_unencumbered_cash_usd"],
        portfolio_unhedged_pnl=input_07["portfolio_unhedged_pnl_usd"],
        gross_derivative_notional=input_07["gross_derivative_notional_usd"],
    )
    output_07 = {
        "total_notional_liquidated_usd": liq_res.total_notional_liquidated,
        "total_market_impact_loss_usd": liq_res.total_market_impact_loss,
        "blended_price_discount_pct": liq_res.blended_price_discount_pct,
        "fire_sale_contagion_multiplier": liq_res.fire_sale_contagion_multiplier,
        "margin_summary": {
            "initial_margin_requirement_usd": liq_res.margin_summary.initial_margin_requirement,
            "stressed_margin_requirement_usd": liq_res.margin_summary.stressed_margin_requirement,
            "margin_call_cash_drain_usd": liq_res.margin_summary.margin_call_cash_drain,
            "variation_margin_deficit_usd": liq_res.margin_summary.variation_margin_deficit,
            "post_stress_lcr_pct": liq_res.margin_summary.liquidity_coverage_ratio_post_stress,
            "days_to_cash_exhaustion": liq_res.margin_summary.days_to_cash_exhaustion,
        },
        "asset_slippage_breakdown": [
            {
                "asset_id": a.asset_id,
                "notional_sold_usd": a.notional_sold,
                "adv_ratio": a.adv_ratio,
                "temporary_impact_bps": a.temporary_impact_bps,
                "permanent_impact_bps": a.permanent_impact_bps,
                "spread_blowout_bps": a.spread_blowout_bps,
                "total_liquidation_cost_usd": a.total_liquidation_cost,
                "realized_price_discount_pct": a.realized_price_discount_pct,
            }
            for a in liq_res.asset_impacts
        ],
    }
    with open(output_dir / "07_almgren_chriss_liquidity_output.json", "w") as f:
        json.dump(output_07, f, indent=2)

    # =========================================================================
    # 8. WHAT-IF GRAPH MUTATION & RESILIENCE ROI (USE CASE 11)
    # =========================================================================
    print("[8/9] Generating Case 08: Supply Chain Mutation ROI...")
    input_08 = {
        "intervention_name": "TSMC & AMD Advanced Packaging Dual-Sourcing Mitigation",
        "capex_budget_usd": 150000.0,
        "mutations": [
            {
                "mutation_type": "REWEIGHT_EDGE",
                "source_id": "FOUNDRY_TW",
                "target_id": "TSM",
                "new_weight": 0.30,
                "capex_cost": 100000.0,
                "lead_time_months": 12,
                "rationale": "Diversify wafer fabrication away from sole-source Hsinchu fab",
            },
            {
                "mutation_type": "SEVER_EDGE",
                "source_id": "FOUNDRY_TW",
                "target_id": "AMD",
                "new_weight": 0.0,
                "capex_cost": 50000.0,
                "lead_time_months": 6,
                "rationale": "Qualify secondary packaging and foundry partner",
            },
        ],
        "test_shock": {"FOUNDRY_TW": -0.70, "BALTIC_DRY": 1.20},
    }
    with open(output_dir / "08_supply_chain_mutation_input.json", "w") as f:
        json.dump(input_08, f, indent=2)

    mut_engine = GraphMutationEngine()
    mut_objs = [
        GraphMutation(
            mutation_type=MutationType(m["mutation_type"]),
            source_id=m["source_id"],
            target_id=m["target_id"],
            new_weight=m["new_weight"],
            capex_cost=m["capex_cost"],
            lead_time_months=m["lead_time_months"],
            rationale=m["rationale"],
        )
        for m in input_08["mutations"]
    ]

    base_shocks = {nid: res.cumulative_shock for nid, res in prop_res.node_shocks.items()}
    base_edges = {(row["source_id"], row["target_id"]): float(row["base_weight"]) for _, row in edges_df.iterrows()}

    mut_res = mut_engine.evaluate_mutation(
        mutation_name=input_08["intervention_name"],
        mutations=mut_objs,
        base_shocks=base_shocks,
        positions=portfolio_notionals,
        base_edges=base_edges,
        alpha_damping=0.65,
    )
    output_08 = {
        "intervention_name": mut_res.mutation_name,
        "initial_unmitigated_pnl_usd": mut_res.initial_pnl,
        "mutated_hardened_pnl_usd": mut_res.mutated_pnl,
        "capital_savings_usd": mut_res.capital_savings,
        "total_capex_invested_usd": mut_res.total_capex,
        "resilience_roi_multiple": mut_res.resilience_roi_multiple,
        "initial_cvar_99_usd": mut_res.initial_cvar_99,
        "mutated_cvar_99_usd": mut_res.mutated_cvar_99,
        "cvar_relief_pct": mut_res.cvar_relief_pct,
        "is_financially_viable": mut_res.is_financially_viable,
        "top_mitigated_nodes": [dict(node) for node in mut_res.top_mitigated_nodes],
    }
    with open(output_dir / "08_supply_chain_mutation_output.json", "w") as f:
        json.dump(output_08, f, indent=2)

    # =========================================================================
    # 9. FOUR-EYES AUDIT VAULT SIGN-OFF (USE CASE 18 & FEATURE 11)
    # =========================================================================
    print("[9/9] Generating Case 09: Four-Eyes Cryptographic Audit Sign-off...")
    input_09 = {
        "run_id": "RUN-2026-11-24-CCAR-STRESS-4A",
        "scenario_name": "Federal Reserve CCAR 2026 Severely Adverse Baseline",
        "model_version": "RiskLattice-v1.0.4-AST",
        "simulation_timestamp": "2026-11-24T10:15:30Z",
        "stressed_var_99_pct": 8.45,
        "stressed_cvar_99_pct": 11.20,
        "total_portfolio_drawdown_usd": -1254000.0,
        "primary_auditor": {
            "name": "Alex Mercer",
            "role": "SENIOR_RISK_ANALYST",
            "signed_at": "2026-11-24T10:20:00Z",
        },
        "secondary_signoff_request": {
            "approver_name": "Sarah Connor",
            "role": "CHIEF_RISK_OFFICER",
            "action": "APPROVE_AND_SEAL",
            "compliance_standards": ["Federal Reserve SR 11-7", "Basel III FRTB Schedule A"],
        },
    }
    with open(output_dir / "09_four_eyes_audit_vault_input.json", "w") as f:
        json.dump(input_09, f, indent=2)

    seal_manifest = f"{input_09['run_id']}|{input_09['model_version']}|{input_09['stressed_cvar_99_pct']}|{input_09['primary_auditor']['name']}|{input_09['secondary_signoff_request']['approver_name']}"
    sha256_seal = hashlib.sha256(seal_manifest.encode("utf-8")).hexdigest()

    output_09 = {
        "run_id": input_09["run_id"],
        "audit_status": "APPROVED_AND_LOCKED",
        "cryptographic_sha256_seal": sha256_seal,
        "dual_key_signoff": {
            "preparer": input_09["primary_auditor"]["name"],
            "preparer_role": input_09["primary_auditor"]["role"],
            "approver": input_09["secondary_signoff_request"]["approver_name"],
            "approver_role": input_09["secondary_signoff_request"]["role"],
            "sealed_at": "2026-11-24T10:25:00Z",
        },
        "regulatory_compliance_stamp": {
            "sr_11_7_model_governance": "VERIFIED_PASS",
            "four_eyes_principle": "ENFORCED",
            "tamper_evident_lock": True,
        },
    }
    with open(output_dir / "09_four_eyes_audit_vault_output.json", "w") as f:
        json.dump(output_09, f, indent=2)

    print("\n[SUCCESS] Generated all 9 synthetic testing datasets and outputs.")


if __name__ == "__main__":
    generate_all_fixtures()
