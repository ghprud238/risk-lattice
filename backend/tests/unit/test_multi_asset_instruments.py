"""Unit tests for Multi-Asset Financial Instruments Valuation Engine.
Tests all non-linear pricing models:
1. Equity (Long/Short)
2. Equity Options (Black-Scholes Delta-Gamma-Vega & Skew)
3. Corporate Bonds (Modified Duration, Convexity, Credit Widening)
4. Single-Name Credit Default Swaps (CDS Hazard Rate Jump)
5. Private Credit / Direct Lending (Debt/EBITDA Covenant Breach)
6. FX Forwards (Cross-Currency Shifts)
7. Structured Credit / CLO Tranche (Attachment/Detachment Waterfall)
8. End-to-End Multi-Asset Portfolio Valuation Integration
"""

import numpy as np
import pytest

from app.engine.instruments import (
    BondPosition,
    CDSPosition,
    CLOTranchePosition,
    EquityPosition,
    FXForwardPosition,
    InstrumentType,
    OptionPosition,
    OptionType,
    PositionSide,
    PrivateCreditPosition,
    evaluate_bond,
    evaluate_cds,
    evaluate_clo_tranche,
    evaluate_equity,
    evaluate_fx_forward,
    evaluate_option,
    evaluate_private_credit,
)
from app.engine.valuation import compute_portfolio_valuation


def test_equity_valuation_long_and_short():
    """Validates linear equity long and short positions under stress shock."""
    long_pos = EquityPosition(ticker="AAPL", notional=1_000_000.0, side=PositionSide.LONG)
    short_pos = EquityPosition(ticker="AAPL", notional=1_000_000.0, side=PositionSide.SHORT)

    detail_long = evaluate_equity(long_pos, shock=-0.15)
    detail_short = evaluate_equity(short_pos, shock=-0.15)

    assert detail_long.pnl == pytest.approx(-150_000.0)
    assert detail_long.effective_return == pytest.approx(-0.15)

    # Short position profits from negative underlying shock
    assert detail_short.pnl == pytest.approx(150_000.0)
    assert detail_short.effective_return == pytest.approx(0.15)


def test_protective_put_tail_risk_hedge():
    """Validates that a Long Put Option acts as an asymmetric tail-risk hedge.
    When the underlying crashes by -25%, the Put spikes in value due to Delta and Vol Skew.
    """
    put_pos = OptionPosition(
        ticker="TSM",
        notional=100_000.0,
        option_type=OptionType.PUT,
        spot=100.0,
        strike=95.0,  # Out of the money
        maturity_years=0.5,
        implied_vol=0.25,
        risk_free_rate=0.04,
        vol_skew=0.40,
        side=PositionSide.LONG,
    )

    detail = evaluate_option(put_pos, shock=-0.25, distress_multiplier=1.2)

    assert detail.instrument_type == InstrumentType.EQUITY_OPTION
    # Put price must increase substantially
    assert detail.greeks_or_metrics["price_after"] > detail.greeks_or_metrics["price_before"]
    # Volatility must spike with skew
    assert detail.greeks_or_metrics["vol_after"] > detail.greeks_or_metrics["vol_before"]
    # Return and PnL must be strongly positive (protective hedge)
    assert detail.effective_return > 1.0  # > 100% gain on put premium
    assert detail.pnl > 100_000.0


def test_long_call_loss_under_spot_crash():
    """Validates that a Long Call Option loses value when underlying spot drops."""
    call_pos = OptionPosition(
        ticker="NVDA",
        notional=200_000.0,
        option_type=OptionType.CALL,
        spot=120.0,
        strike=125.0,
        maturity_years=0.5,
        implied_vol=0.35,
        risk_free_rate=0.04,
        side=PositionSide.LONG,
    )

    detail = evaluate_option(call_pos, shock=-0.20, distress_multiplier=1.0)
    assert detail.pnl < 0.0
    assert detail.effective_return < 0.0
    assert detail.greeks_or_metrics["price_after"] < detail.greeks_or_metrics["price_before"]


def test_corporate_bond_duration_convexity_and_distress():
    """Validates bond pricing under modified duration, convexity, and credit spread widening."""
    bond_pos = BondPosition(
        ticker="F",
        notional=5_000_000.0,
        duration=6.5,
        convexity=45.0,
        spread_bps=220.0,
        credit_beta=2.0,
        side=PositionSide.LONG,
    )

    # Under negative shock with high distress multiplier (lambda_v = 1.8)
    detail = evaluate_bond(bond_pos, shock=-0.20, distress_multiplier=1.8)

    assert detail.instrument_type == InstrumentType.BOND
    # Spread widening = 2.0 * 0.20 * 1.8 * 1000 = 720 bps
    assert detail.greeks_or_metrics["spread_widening_bps"] == pytest.approx(720.0)
    assert detail.greeks_or_metrics["yield_delta"] == pytest.approx(0.0720)

    # dP/P = -6.5 * 0.072 + 0.5 * 45.0 * (0.072^2) = -0.468 + 0.1166 = -0.3514
    expected_pct = -6.5 * 0.0720 + 0.5 * 45.0 * (0.0720 ** 2)
    assert detail.effective_return == pytest.approx(expected_pct, rel=1e-3)
    assert detail.pnl < 0.0
    assert detail.pnl == pytest.approx(5_000_000.0 * expected_pct, rel=1e-3)


def test_cds_buy_protection_hazard_rate_jump():
    """Validates Single-Name CDS BUY protection under exponential hazard rate jump."""
    cds_pos = CDSPosition(
        ticker="BA",
        notional=10_000_000.0,
        spread_duration=4.2,
        current_spread_bps=150.0,
        recovery_rate=0.40,
        hazard_sensitivity=2.5,
        side=PositionSide.BUY,
    )

    detail = evaluate_cds(cds_pos, shock=-0.25, distress_multiplier=1.5)

    assert detail.instrument_type == InstrumentType.CDS
    # Hazard rate must jump significantly
    assert detail.greeks_or_metrics["hazard_rate_after"] > detail.greeks_or_metrics["hazard_rate_before"]
    # Spread must widen
    assert detail.greeks_or_metrics["delta_spread_bps"] > 0.0
    # BUY protection gains MtM profit
    assert detail.pnl > 0.0
    assert detail.effective_return > 0.0


def test_private_credit_covenant_breach_and_haircut():
    """Validates Private Credit / Direct Lending covenant breach test."""
    loan_pos = PrivateCreditPosition(
        ticker="CORP_MID",
        notional=15_000_000.0,
        initial_leverage=4.2,
        covenant_max_leverage=5.5,
        recovery_rate=0.60,
        side=PositionSide.LONG,
    )

    # Case 1: Mild shock (-5%), Stressed leverage = 4.2 / 0.95 = 4.42x <= 5.5x (Compliant)
    mild_detail = evaluate_private_credit(loan_pos, shock=-0.05, distress_multiplier=1.0)
    assert mild_detail.greeks_or_metrics["covenant_breached"] == 0.0
    assert mild_detail.effective_return < 0.0
    assert abs(mild_detail.effective_return) < 0.05  # Minimal penalty

    # Case 2: Severe shock (-35%) with distress lambda=1.4, Stressed leverage jumps > 5.5x
    severe_detail = evaluate_private_credit(loan_pos, shock=-0.35, distress_multiplier=1.4)
    assert severe_detail.greeks_or_metrics["covenant_breached"] == 1.0
    # Impairment haircut must trigger
    assert severe_detail.effective_return < -0.15
    assert severe_detail.pnl < -2_000_000.0


def test_fx_forward_currency_hedging():
    """Validates FX Forward contract hedging foreign exchange depreciation."""
    fx_pos = FXForwardPosition(
        ticker="EUR_HEDGE",
        notional=8_000_000.0,
        fx_rate=1.08,
        fx_beta=0.80,
        side=PositionSide.LONG,
    )

    detail = evaluate_fx_forward(fx_pos, shock=-0.15)
    # Currency shift = 0.80 * -0.15 = -0.12 (-12%)
    assert detail.greeks_or_metrics["fx_pct_change"] == pytest.approx(-0.12)
    assert detail.pnl == pytest.approx(8_000_000.0 * -0.12)


def test_clo_tranche_waterfall_loss_absorption():
    """Validates CLO Tranche waterfall loss absorption across subordination levels."""
    # Mezzanine BBB Tranche [10%, 20%]
    mezz_tranche = CLOTranchePosition(
        ticker="CLO_BBB",
        notional=5_000_000.0,
        attachment_point=0.10,
        detachment_point=0.20,
        tranche_name="BBB Mezzanine",
        side=PositionSide.LONG,
    )

    # 1. Pool loss 5% (< 10% attachment) -> Tranche loss is 0%
    detail_safe = evaluate_clo_tranche(mezz_tranche, shock=0.05, collateral_loss_scale=1.0)
    assert detail_safe.greeks_or_metrics["tranche_loss_rate"] == 0.0
    assert detail_safe.pnl == 0.0

    # 2. Pool loss 15% (midpoint of [10%, 20%]) -> Tranche loss is 50%
    detail_mid = evaluate_clo_tranche(mezz_tranche, shock=0.15, collateral_loss_scale=1.0)
    assert detail_mid.greeks_or_metrics["tranche_loss_rate"] == pytest.approx(0.50)
    assert detail_mid.pnl == pytest.approx(-2_500_000.0)

    # 3. Pool loss 25% (> 20% detachment) -> Tranche completely wiped out (100% loss)
    detail_wiped = evaluate_clo_tranche(mezz_tranche, shock=0.25, collateral_loss_scale=1.0)
    assert detail_wiped.greeks_or_metrics["tranche_loss_rate"] == pytest.approx(1.00)
    assert detail_wiped.pnl == pytest.approx(-5_000_000.0)


def test_portfolio_valuation_multi_asset_integration():
    """Integrates Equity, Put Option, Bond, and CDS into compute_portfolio_valuation."""
    node_ids = ["NODE_TSM", "NODE_TSM_PUT", "NODE_F_BOND", "NODE_BA_CDS"]
    tickers = ["TSM", "TSM_PUT", "F_BOND", "BA_CDS"]
    notionals = np.array([10_000_000.0, 500_000.0, 4_000_000.0, 6_000_000.0], dtype=np.float64)

    # Hop returns matrix: hop 0 direct shock -20% on TSM, hop 1..4 propagation
    K_plus_1 = 5
    hop_returns = np.zeros((K_plus_1, 4), dtype=np.float64)
    hop_returns[0] = np.array([-0.20, -0.20, -0.15, -0.18])
    hop_returns[1] = np.array([-0.05, -0.05, -0.04, -0.03])

    instruments = [
        EquityPosition(ticker="TSM", notional=10_000_000.0, side=PositionSide.LONG),
        OptionPosition(
            ticker="TSM_PUT",
            notional=500_000.0,
            option_type=OptionType.PUT,
            spot=100.0,
            strike=95.0,
            maturity_years=0.5,
            implied_vol=0.25,
            vol_skew=0.40,
            side=PositionSide.LONG,
        ),
        BondPosition(
            ticker="F_BOND",
            notional=4_000_000.0,
            duration=5.0,
            convexity=30.0,
            credit_beta=1.5,
            side=PositionSide.LONG,
        ),
        CDSPosition(
            ticker="BA_CDS",
            notional=6_000_000.0,
            spread_duration=4.0,
            current_spread_bps=140.0,
            side=PositionSide.BUY,  # Buy protection gains when BA deteriorates
        ),
    ]

    distress = np.array([1.0, 1.0, 1.6, 1.5], dtype=np.float64)

    result = compute_portfolio_valuation(
        node_ids=node_ids,
        tickers=tickers,
        notionals=notionals,
        hop_returns=hop_returns,
        instrument_positions=instruments,
        distress_multipliers=distress,
    )

    assert result.total_notional == pytest.approx(20_500_000.0)
    assert len(result.asset_valuations) == 4

    # TSM equity loses money
    assert result.asset_valuations[0].pnl < 0.0

    # TSM Put option makes money (protective hedge!)
    assert result.asset_valuations[1].pnl > 0.0
    assert result.asset_valuations[1].instrument_detail is not None
    assert result.asset_valuations[1].instrument_detail.instrument_type == InstrumentType.EQUITY_OPTION

    # Ford bond loses money due to duration & credit spread widening
    assert result.asset_valuations[2].pnl < 0.0
    assert result.asset_valuations[2].instrument_detail.instrument_type == InstrumentType.BOND

    # BA CDS BUY protection gains money, offsetting the bond loss!
    assert result.asset_valuations[3].pnl > 0.0
    assert result.asset_valuations[3].instrument_detail.instrument_type == InstrumentType.CDS
