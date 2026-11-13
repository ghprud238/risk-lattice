"""Multi-Asset Financial Instruments Valuation Engine.
PRD Section 16 & Section 24.1 compliant:
- Pure scientific computing with zero database, network, or LLM imports (AST isolated).
- Valuation for:
    1. Single-Stock Equities (Long/Short)
    2. Equity Options (Black-Scholes Delta-Gamma-Vega with volatility skew)
    3. Corporate Bonds (Modified duration, convexity, credit spread widening)
    4. Single-Name Credit Default Swaps (CDS hazard rate jump & MtM)
    5. Private Credit / Direct Lending (Debt/EBITDA covenant breach & impairment)
    6. FX Forwards (Cross-currency depreciation)
    7. Structured Credit / CLO Tranches (Attachment/Detachment waterfall loss)
"""

from dataclasses import dataclass
from enum import Enum
import math
from typing import Any, Dict, List, Literal, Optional, Tuple, Union
import numpy as np
from scipy import stats


class InstrumentType(str, Enum):
    EQUITY = "EQUITY"
    EQUITY_OPTION = "EQUITY_OPTION"
    BOND = "BOND"
    CDS = "CDS"
    PRIVATE_CREDIT = "PRIVATE_CREDIT"
    FX_FORWARD = "FX_FORWARD"
    CLO_TRANCHE = "CLO_TRANCHE"


class PositionSide(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    BUY = "BUY"
    SELL = "SELL"


class OptionType(str, Enum):
    CALL = "CALL"
    PUT = "PUT"


@dataclass(frozen=True)
class InstrumentValuationDetail:
    instrument_type: InstrumentType
    notional: float
    effective_return: float
    pnl: float
    greeks_or_metrics: Dict[str, float]
    status_notes: str


@dataclass(frozen=True)
class EquityPosition:
    ticker: str
    notional: float
    side: PositionSide = PositionSide.LONG

    @property
    def direction(self) -> float:
        return 1.0 if self.side in (PositionSide.LONG, PositionSide.BUY) else -1.0


@dataclass(frozen=True)
class OptionPosition:
    ticker: str
    notional: float  # Total dollar value / premium base
    option_type: OptionType
    spot: float
    strike: float
    maturity_years: float
    implied_vol: float
    risk_free_rate: float = 0.04
    vol_skew: float = 0.35  # Skew sensitivity to underlying negative shock
    side: PositionSide = PositionSide.LONG

    @property
    def direction(self) -> float:
        return 1.0 if self.side in (PositionSide.LONG, PositionSide.BUY) else -1.0


@dataclass(frozen=True)
class BondPosition:
    ticker: str
    notional: float
    duration: float  # Modified duration (e.g. 5.5 years)
    convexity: float = 35.0  # Convexity measure
    spread_bps: float = 180.0  # Baseline OAS / credit spread in bps
    credit_beta: float = 1.5  # Sensitivity of credit spread to asset shock
    side: PositionSide = PositionSide.LONG

    @property
    def direction(self) -> float:
        return 1.0 if self.side in (PositionSide.LONG, PositionSide.BUY) else -1.0


@dataclass(frozen=True)
class CDSPosition:
    ticker: str
    notional: float
    spread_duration: float = 4.5
    current_spread_bps: float = 120.0
    recovery_rate: float = 0.40  # Standard ISDA corporate recovery
    hazard_sensitivity: float = 2.5
    side: PositionSide = PositionSide.BUY  # BUY = Long protection, SELL = Short protection

    @property
    def direction(self) -> float:
        # BUY protection profits when credit deteriorates (hazard rate jumps)
        return 1.0 if self.side in (PositionSide.BUY, PositionSide.LONG) else -1.0


@dataclass(frozen=True)
class PrivateCreditPosition:
    ticker: str
    notional: float
    initial_leverage: float  # Net Debt / EBITDA (e.g. 4.2x)
    covenant_max_leverage: float = 5.5  # Maintenance covenant ceiling
    recovery_rate: float = 0.60  # Senior secured direct lending recovery
    spread_bps: float = 650.0
    side: PositionSide = PositionSide.LONG

    @property
    def direction(self) -> float:
        return 1.0 if self.side in (PositionSide.LONG, PositionSide.BUY) else -1.0


@dataclass(frozen=True)
class FXForwardPosition:
    ticker: str
    notional: float
    fx_rate: float
    fx_beta: float = 0.75  # Elasticity of currency depreciation to asset shock
    side: PositionSide = PositionSide.LONG

    @property
    def direction(self) -> float:
        return 1.0 if self.side in (PositionSide.LONG, PositionSide.BUY) else -1.0


@dataclass(frozen=True)
class CLOTranchePosition:
    ticker: str
    notional: float
    attachment_point: float  # e.g., 0.10 for Mezzanine BBB
    detachment_point: float  # e.g., 0.20
    tranche_name: str = "BBB Mezzanine"
    side: PositionSide = PositionSide.LONG

    @property
    def direction(self) -> float:
        return 1.0 if self.side in (PositionSide.LONG, PositionSide.BUY) else -1.0


# ---------------------------------------------------------------------------
# Black-Scholes Formula Helpers (Pure SciPy/NumPy)
# ---------------------------------------------------------------------------

def _black_scholes_price(
    spot: float,
    strike: float,
    t: float,
    r: float,
    sigma: float,
    option_type: OptionType,
) -> Tuple[float, float, float, float]:
    """Calculates Black-Scholes price and Greeks (Delta, Gamma, Vega)."""
    if t <= 1e-4 or sigma <= 1e-4 or spot <= 1e-4 or strike <= 1e-4:
        # Intrinsic value at boundary
        if option_type == OptionType.CALL:
            price = max(0.0, spot - strike)
            delta = 1.0 if spot > strike else 0.0
        else:
            price = max(0.0, strike - spot)
            delta = -1.0 if spot < strike else 0.0
        return price, delta, 0.0, 0.0

    sqrt_t = math.sqrt(t)
    d1 = (math.log(spot / strike) + (r + 0.5 * sigma * sigma) * t) / (sigma * sqrt_t)
    d2 = d1 - sigma * sqrt_t

    norm_d1 = float(stats.norm.cdf(d1))
    norm_d2 = float(stats.norm.cdf(d2))
    pdf_d1 = float(stats.norm.pdf(d1))

    df = math.exp(-r * t)

    if option_type == OptionType.CALL:
        price = spot * norm_d1 - strike * df * norm_d2
        delta = norm_d1
    else:
        price = strike * df * float(stats.norm.cdf(-d2)) - spot * float(stats.norm.cdf(-d1))
        delta = norm_d1 - 1.0

    gamma = pdf_d1 / (spot * sigma * sqrt_t) if (spot * sigma * sqrt_t) > 0 else 0.0
    vega = spot * pdf_d1 * sqrt_t * 0.01  # Vega per 1% vol shift

    return max(0.0, price), delta, gamma, vega


# ---------------------------------------------------------------------------
# Instrument Evaluation Dispatchers
# ---------------------------------------------------------------------------

def evaluate_equity(pos: EquityPosition, shock: float) -> InstrumentValuationDetail:
    """Evaluates standard single-stock equity long/short position."""
    eff_ret = pos.direction * shock
    pnl = pos.notional * eff_ret
    return InstrumentValuationDetail(
        instrument_type=InstrumentType.EQUITY,
        notional=pos.notional,
        effective_return=eff_ret,
        pnl=pnl,
        greeks_or_metrics={"delta": pos.direction, "beta": 1.0},
        status_notes=f"Equity {pos.side.value} return {shock:.4f}",
    )


def evaluate_option(
    pos: OptionPosition, shock: float, distress_multiplier: float = 1.0
) -> InstrumentValuationDetail:
    """Evaluates equity option position under spot shock and volatility skew.
    
    Protective Put: When shock < 0, Put value increases, generating positive PnL.
    Long Call: Drops when shock < 0.
    """
    s0 = pos.spot
    # Perturb underlying spot
    s1 = max(0.01, s0 * (1.0 + shock))
    # Volatility skew: negative shock triggers vol spike
    excess_shock = max(0.0, -shock)
    vol_jump = pos.vol_skew * excess_shock * distress_multiplier
    sigma0 = pos.implied_vol
    sigma1 = max(0.02, sigma0 + vol_jump)

    p0, delta0, gamma0, vega0 = _black_scholes_price(
        spot=s0,
        strike=pos.strike,
        t=pos.maturity_years,
        r=pos.risk_free_rate,
        sigma=sigma0,
        option_type=pos.option_type,
    )

    p1, delta1, gamma1, vega1 = _black_scholes_price(
        spot=s1,
        strike=pos.strike,
        t=pos.maturity_years,
        r=pos.risk_free_rate,
        sigma=sigma1,
        option_type=pos.option_type,
    )

    # Relative option price return
    if p0 > 1e-4:
        opt_return = (p1 - p0) / p0
    else:
        opt_return = (p1 - p0) / max(1e-4, pos.strike * 0.05)

    pnl = pos.notional * opt_return * pos.direction

    return InstrumentValuationDetail(
        instrument_type=InstrumentType.EQUITY_OPTION,
        notional=pos.notional,
        effective_return=opt_return * pos.direction,
        pnl=pnl,
        greeks_or_metrics={
            "price_before": p0,
            "price_after": p1,
            "delta": delta0,
            "gamma": gamma0,
            "vega": vega0,
            "vol_before": sigma0,
            "vol_after": sigma1,
        },
        status_notes=(
            f"{pos.side.value} {pos.option_type.value} [K={pos.strike}]: "
            f"Spot {s0:.1f}->{s1:.1f}, Vol {sigma0:.1%}->{sigma1:.1%}"
        ),
    )


def evaluate_bond(
    pos: BondPosition, shock: float, distress_multiplier: float = 1.0
) -> InstrumentValuationDetail:
    """Evaluates corporate bond under duration and convexity with credit spread widening.
    Credit spread widening: Delta y = credit_beta * max(0, -shock) * distress_multiplier
    """
    excess_shock = max(0.0, -shock)
    # Credit spread delta in decimal yield (e.g., 150 bps -> 0.0150)
    delta_spread_bps = pos.credit_beta * excess_shock * distress_multiplier * 1000.0
    delta_y = delta_spread_bps / 10000.0

    # Percentage price change via modified duration and convexity:
    # dP/P = -D_mod * dy + 0.5 * C * (dy)^2
    price_pct_change = -pos.duration * delta_y + 0.5 * pos.convexity * (delta_y ** 2)
    eff_ret = pos.direction * price_pct_change
    pnl = pos.notional * eff_ret

    return InstrumentValuationDetail(
        instrument_type=InstrumentType.BOND,
        notional=pos.notional,
        effective_return=eff_ret,
        pnl=pnl,
        greeks_or_metrics={
            "duration": pos.duration,
            "convexity": pos.convexity,
            "spread_widening_bps": delta_spread_bps,
            "yield_delta": delta_y,
            "price_pct_change": price_pct_change,
        },
        status_notes=f"Bond D={pos.duration:.1f}y: Spread +{delta_spread_bps:.1f} bps, dP/P={price_pct_change:.2%}",
    )


def evaluate_cds(
    pos: CDSPosition, shock: float, distress_multiplier: float = 1.0
) -> InstrumentValuationDetail:
    """Evaluates Single-Name Credit Default Swap under hazard rate jump.
    BUY Protection profits when credit deteriorates (hazard rate jumps).
    """
    s0 = pos.current_spread_bps / 10000.0
    gamma0 = s0 / max(0.01, (1.0 - pos.recovery_rate))

    excess_shock = max(0.0, -shock)
    # Stressed hazard rate exponential surge
    hazard_multiplier = math.exp(pos.hazard_sensitivity * excess_shock * distress_multiplier)
    gamma1 = gamma0 * hazard_multiplier

    s1 = gamma1 * (1.0 - pos.recovery_rate)
    delta_s = s1 - s0

    # MtM PnL = Direction * Notional * SpreadDuration * DeltaSpread
    pnl = pos.direction * pos.notional * pos.spread_duration * delta_s
    eff_ret = pnl / pos.notional if pos.notional > 0 else 0.0

    return InstrumentValuationDetail(
        instrument_type=InstrumentType.CDS,
        notional=pos.notional,
        effective_return=eff_ret,
        pnl=pnl,
        greeks_or_metrics={
            "spread_duration": pos.spread_duration,
            "spread_before_bps": pos.current_spread_bps,
            "spread_after_bps": s1 * 10000.0,
            "hazard_rate_before": gamma0,
            "hazard_rate_after": gamma1,
            "delta_spread_bps": delta_s * 10000.0,
        },
        status_notes=(
            f"CDS {pos.side.value} Protection: Spread {pos.current_spread_bps:.0f} -> "
            f"{s1 * 10000.0:.0f} bps (+{delta_s * 10000.0:.0f} bps)"
        ),
    )


def evaluate_private_credit(
    pos: PrivateCreditPosition, shock: float, distress_multiplier: float = 1.0
) -> InstrumentValuationDetail:
    """Evaluates Private Credit / Direct Lending loan under debt covenant breach test."""
    excess_shock = max(0.0, -shock)
    # EBITDA contraction
    ebitda_contraction = min(0.80, excess_shock * distress_multiplier)
    stressed_leverage = pos.initial_leverage / max(0.20, (1.0 - ebitda_contraction))

    covenant_breached = stressed_leverage > pos.covenant_max_leverage

    if covenant_breached:
        # Covenant breach impairment haircut
        excess_leverage = stressed_leverage - pos.covenant_max_leverage
        haircut = min(1.0 - pos.recovery_rate, 0.08 + 0.12 * excess_leverage)
        eff_ret = -haircut * pos.direction
        pnl = pos.notional * eff_ret
        notes = (
            f"COVENANT BREACH! Leverage {pos.initial_leverage:.1f}x -> {stressed_leverage:.1f}x "
            f"(Limit: {pos.covenant_max_leverage:.1f}x). Impairment: {haircut:.1%}"
        )
    else:
        # Minor spread widening penalty
        spread_widening_penalty = 0.015 * (stressed_leverage - pos.initial_leverage)
        eff_ret = -spread_widening_penalty * pos.direction
        pnl = pos.notional * eff_ret
        notes = f"Compliant: Leverage {pos.initial_leverage:.1f}x -> {stressed_leverage:.1f}x (Under {pos.covenant_max_leverage:.1f}x)"

    return InstrumentValuationDetail(
        instrument_type=InstrumentType.PRIVATE_CREDIT,
        notional=pos.notional,
        effective_return=eff_ret,
        pnl=pnl,
        greeks_or_metrics={
            "initial_leverage": pos.initial_leverage,
            "stressed_leverage": stressed_leverage,
            "covenant_limit": pos.covenant_max_leverage,
            "covenant_breached": 1.0 if covenant_breached else 0.0,
        },
        status_notes=notes,
    )


def evaluate_fx_forward(pos: FXForwardPosition, shock: float) -> InstrumentValuationDetail:
    """Evaluates foreign exchange forward / cross-currency hedging."""
    # Currency depreciation proportional to foreign equity/macro shock
    fx_pct_change = pos.fx_beta * shock
    eff_ret = pos.direction * fx_pct_change
    pnl = pos.notional * eff_ret

    return InstrumentValuationDetail(
        instrument_type=InstrumentType.FX_FORWARD,
        notional=pos.notional,
        effective_return=eff_ret,
        pnl=pnl,
        greeks_or_metrics={"fx_pct_change": fx_pct_change, "fx_beta": pos.fx_beta},
        status_notes=f"FX Forward {pos.side.value}: Currency shift {fx_pct_change:.2%}",
    )


def evaluate_clo_tranche(
    pos: CLOTranchePosition, shock: float, collateral_loss_scale: float = 1.0
) -> InstrumentValuationDetail:
    """Evaluates Structured Credit / CLO tranche waterfall under collateral pool loss."""
    # Collateral pool loss driven by severe corporate contraction
    pool_loss = min(1.0, max(0.0, abs(shock) * collateral_loss_scale))
    att = pos.attachment_point
    det = pos.detachment_point
    width = max(1e-4, det - att)

    # Tranche loss rate between att and det
    tranche_loss_rate = (min(det, max(att, pool_loss)) - att) / width
    eff_ret = -pos.direction * tranche_loss_rate
    pnl = pos.notional * eff_ret

    return InstrumentValuationDetail(
        instrument_type=InstrumentType.CLO_TRANCHE,
        notional=pos.notional,
        effective_return=eff_ret,
        pnl=pnl,
        greeks_or_metrics={
            "pool_loss": pool_loss,
            "attachment": att,
            "detachment": det,
            "tranche_loss_rate": tranche_loss_rate,
        },
        status_notes=(
            f"CLO {pos.tranche_name} [{att:.1%}-{det:.1%}]: "
            f"Pool Loss {pool_loss:.1%} -> Tranche Impairment {tranche_loss_rate:.1%}"
        ),
    )


def evaluate_any_instrument(
    instrument: Union[
        EquityPosition,
        OptionPosition,
        BondPosition,
        CDSPosition,
        PrivateCreditPosition,
        FXForwardPosition,
        CLOTranchePosition,
    ],
    shock: float,
    distress_multiplier: float = 1.0,
) -> InstrumentValuationDetail:
    """Unified dispatcher for any multi-asset financial instrument."""
    if isinstance(instrument, OptionPosition):
        return evaluate_option(instrument, shock, distress_multiplier)
    elif isinstance(instrument, BondPosition):
        return evaluate_bond(instrument, shock, distress_multiplier)
    elif isinstance(instrument, CDSPosition):
        return evaluate_cds(instrument, shock, distress_multiplier)
    elif isinstance(instrument, PrivateCreditPosition):
        return evaluate_private_credit(instrument, shock, distress_multiplier)
    elif isinstance(instrument, FXForwardPosition):
        return evaluate_fx_forward(instrument, shock)
    elif isinstance(instrument, CLOTranchePosition):
        return evaluate_clo_tranche(instrument, shock)
    else:
        return evaluate_equity(instrument, shock)
