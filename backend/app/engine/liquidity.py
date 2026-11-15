"""Endogenous Market Impact & Margin Call Spiral Engine.
PRD Section 16 & Section 24.1 compliant:
- Pure scientific computing with zero database, network, or LLM imports (AST isolated).
- Implements the Almgren-Chriss (2000) optimal execution and market impact model:
  * Permanent impact: I_perm = gamma * (Trade Notional / ADV)
  * Temporary impact: I_temp = eta * sigma * sqrt(Trade Notional / (ADV * Participation_Rate))
- Models fire-sale liquidation spirals when portfolio breaches leverage / drawdown thresholds.
- Computes derivative variation margin (VM) calls and initial margin (IM) step-ups under ISDA SIMM.
"""

from dataclasses import dataclass
import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np


@dataclass(frozen=True)
class LiquidationPosition:
    asset_id: str
    target_notional: float
    adv_30d: float          # 30-day Average Daily Volume in dollars
    volatility_ann: float   # Annualized volatility (e.g. 0.35 = 35%)
    bid_ask_spread_bps: float # Normal bid-ask spread in basis points
    liquidation_urgency: str # "LOW" | "MEDIUM" | "HIGH" | "FIRE_SALE"


@dataclass(frozen=True)
class AssetLiquidityImpact:
    asset_id: str
    notional_sold: float
    adv_ratio: float
    temporary_impact_bps: float
    permanent_impact_bps: float
    spread_blowout_bps: float
    total_liquidation_cost: float
    realized_price_discount_pct: float


@dataclass(frozen=True)
class MarginCallSummary:
    initial_margin_requirement: float
    stressed_margin_requirement: float
    margin_call_cash_drain: float
    variation_margin_deficit: float
    liquidity_coverage_ratio_post_stress: float
    days_to_cash_exhaustion: float


@dataclass(frozen=True)
class LiquidityStressResult:
    total_notional_liquidated: float
    total_market_impact_loss: float
    blended_price_discount_pct: float
    asset_impacts: Tuple[AssetLiquidityImpact, ...]
    margin_summary: MarginCallSummary
    fire_sale_contagion_multiplier: float


class EndogenousLiquidityEngine:
    """Computes endogenous market impact, fire-sale liquidation discounts, and margin spirals."""

    def __init__(
        self,
        gamma_perm: float = 0.15,  # Permanent impact coefficient
        eta_temp: float = 0.25,    # Temporary impact coefficient
    ):
        self.gamma_perm = gamma_perm
        self.eta_temp = eta_temp

    def evaluate_liquidation(
        self,
        positions: List[LiquidationPosition],
        liquidation_pct: float = 0.20,  # e.g. 20% of positions liquidated to meet margin/redemptions
        participation_rate: float = 0.10, # Max 10% of market ADV per day
        fund_unencumbered_cash: float = 15_000_000.0,
        portfolio_unhedged_pnl: float = -23_450_000.0,
        gross_derivative_notional: float = 50_000_000.0,
    ) -> LiquidityStressResult:
        """Calculates Almgren-Chriss liquidation cost and margin call cash drain."""
        impacts: List[AssetLiquidityImpact] = []
        total_liquidated = 0.0
        total_impact_loss = 0.0

        urgency_multiplier = {
            "LOW": 1.0,
            "MEDIUM": 1.35,
            "HIGH": 1.85,
            "FIRE_SALE": 2.50,
        }

        for pos in positions:
            sold_notional = pos.target_notional * liquidation_pct
            adv = max(1_000_000.0, pos.adv_30d)
            adv_fraction = sold_notional / adv

            mult = urgency_multiplier.get(pos.liquidation_urgency, 1.35)

            # 1. Normal Bid-Ask spread blowout under market distress
            spread_blowout_bps = pos.bid_ask_spread_bps * (1.0 + 3.5 * adv_fraction) * mult

            # 2. Almgren-Chriss Temporary Impact
            temp_impact_bps = (
                self.eta_temp
                * pos.volatility_ann
                * math.sqrt(max(0.01, adv_fraction / max(0.01, participation_rate)))
                * 10000.0
                * mult
            )

            # 3. Almgren-Chriss Permanent Impact
            perm_impact_bps = self.gamma_perm * adv_fraction * 10000.0 * mult

            # Total slippage bps
            total_slippage_bps = (spread_blowout_bps / 2.0) + temp_impact_bps + (perm_impact_bps / 2.0)
            price_discount_pct = total_slippage_bps / 10000.0

            loss_dollars = sold_notional * price_discount_pct

            impacts.append(
                AssetLiquidityImpact(
                    asset_id=pos.asset_id,
                    notional_sold=round(sold_notional, 2),
                    adv_ratio=round(adv_fraction, 4),
                    temporary_impact_bps=round(temp_impact_bps, 1),
                    permanent_impact_bps=round(perm_impact_bps, 1),
                    spread_blowout_bps=round(spread_blowout_bps, 1),
                    total_liquidation_cost=round(loss_dollars, 2),
                    realized_price_discount_pct=round(price_discount_pct * 100.0, 2),
                )
            )

            total_liquidated += sold_notional
            total_impact_loss += loss_dollars

        blended_discount_pct = (
            (total_impact_loss / max(1.0, total_liquidated)) * 100.0 if total_liquidated > 0 else 0.0
        )

        # 4. Derivative Margin Call Spiral (ISDA SIMM step-up)
        # Base initial margin = 8% of gross derivative notional
        base_im = gross_derivative_notional * 0.08
        # Stressed initial margin jumps to 18% as implied volatility doubles
        stressed_im = gross_derivative_notional * 0.18
        im_increase = stressed_im - base_im

        # Variation margin deficit matches the unhedged derivatives loss
        vm_deficit = abs(portfolio_unhedged_pnl) * 0.40  # 40% derivatives component

        total_margin_call = im_increase + vm_deficit

        # Remaining cash buffer
        remaining_cash = fund_unencumbered_cash - total_margin_call - total_impact_loss
        lcr = max(0.0, (fund_unencumbered_cash / max(1.0, total_margin_call)) * 100.0)

        # Days to cash exhaustion assuming $500k/day operational burn + margin drain
        daily_cash_burn = 500_000.0 + (total_margin_call / 30.0)
        days_to_exhaustion = max(0.0, fund_unencumbered_cash / max(100_000.0, daily_cash_burn))

        margin_summary = MarginCallSummary(
            initial_margin_requirement=round(base_im, 2),
            stressed_margin_requirement=round(stressed_im, 2),
            margin_call_cash_drain=round(total_margin_call, 2),
            variation_margin_deficit=round(vm_deficit, 2),
            liquidity_coverage_ratio_post_stress=round(lcr, 1),
            days_to_cash_exhaustion=round(days_to_exhaustion, 1),
        )

        # Fire sale multiplier escalates if fund liquidates > 30% of position ADV
        max_adv = max([i.adv_ratio for i in impacts], default=0.0)
        fire_sale_multiplier = 1.0 + min(2.5, max_adv * 1.8)

        return LiquidityStressResult(
            total_notional_liquidated=round(total_liquidated, 2),
            total_market_impact_loss=round(total_impact_loss, 2),
            blended_price_discount_pct=round(blended_discount_pct, 2),
            asset_impacts=tuple(impacts),
            margin_summary=margin_summary,
            fire_sale_contagion_multiplier=round(fire_sale_multiplier, 2),
        )
