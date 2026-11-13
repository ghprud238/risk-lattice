"""Valuation, Attribution, and Audit Ledger per Section 16.4.
Strict mathematical core: zero network/DB/FastAPI imports.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from app.engine.instruments import InstrumentValuationDetail, evaluate_any_instrument


@dataclass(frozen=True)
class AssetValuation:
    node_id: str
    ticker: str
    notional: float
    local_return: float
    fx_return: float
    base_return: float
    pnl: float
    hop_pnls: Tuple[float, ...]  # PnL attributed to hop 0, hop 1, ..., hop K
    channel_pnls: Dict[str, float]  # PnL attributed to SUPPLY, CUSTOMER, CREDIT, SECTOR, DIRECT
    instrument_detail: Optional[InstrumentValuationDetail] = None


@dataclass(frozen=True)
class PortfolioValuationResult:
    total_notional: float
    total_pnl: float
    portfolio_return: float
    asset_valuations: Tuple[AssetValuation, ...]
    hop_attribution: Dict[int, float]  # hop -> total dollar PnL
    channel_attribution: Dict[str, float]  # channel -> total dollar PnL


def compound_return(r_local: float, r_fx: float = 0.0) -> float:
    """Computes base-currency compounded return incorporating cross-term per Case N-10.
    r_base = (1 + r_local) * (1 + r_fx) - 1 = r_local + r_fx + r_local * r_fx
    """
    return (1.0 + r_local) * (1.0 + r_fx) - 1.0


def compute_portfolio_valuation(
    node_ids: List[str],
    tickers: List[str],
    notionals: np.ndarray,
    hop_returns: np.ndarray,  # shape: (K+1, num_nodes) where hop 0 is seed, hop 1..K are increments
    fx_returns: Optional[np.ndarray] = None,  # shape: (num_nodes,)
    node_channel_breakdown: Optional[Dict[str, Dict[str, float]]] = None,
    instrument_positions: Optional[List[Any]] = None,
    distress_multipliers: Optional[np.ndarray] = None,
) -> PortfolioValuationResult:
    """Evaluates portfolio positions, returns, and attribution ledger per Section 16.4.
    Supports multi-asset instruments (Options, Bonds, CDS, Private Credit, FX, CLO).
    
    Args:
        node_ids: List of node IDs
        tickers: List of ticker strings
        notionals: Dollar notionals array (shape: N)
        hop_returns: Incremental return matrix (shape: (K+1, N))
        fx_returns: FX return against base currency (shape: N, default 0.0)
        node_channel_breakdown: Channel return proportion per node
        instrument_positions: Optional list of instrument positions for non-linear valuation
        distress_multipliers: Optional array of distress multipliers (lambda_v)
    """
    num_nodes = len(node_ids)
    k_plus_1 = hop_returns.shape[0]

    if fx_returns is None:
        fx_returns = np.zeros(num_nodes, dtype=np.float64)

    if distress_multipliers is None:
        distress_multipliers = np.ones(num_nodes, dtype=np.float64)

    # Total local return is sum of hops: r_local = sum_k hop_returns[k]
    raw_local_returns = np.sum(hop_returns, axis=0)
    effective_local_returns = np.zeros(num_nodes, dtype=np.float64)
    instrument_details: List[Optional[InstrumentValuationDetail]] = []

    for i in range(num_nodes):
        raw_ret = float(raw_local_returns[i])
        if instrument_positions and i < len(instrument_positions) and instrument_positions[i] is not None:
            inst = instrument_positions[i]
            detail = evaluate_any_instrument(inst, raw_ret, float(distress_multipliers[i]))
            effective_local_returns[i] = detail.effective_return
            instrument_details.append(detail)
        else:
            effective_local_returns[i] = raw_ret
            instrument_details.append(None)
    
    # Base return with exact FX cross-term (Case N-10)
    base_returns = (1.0 + effective_local_returns) * (1.0 + fx_returns) - 1.0
    
    asset_pnls = notionals * base_returns
    total_notional = float(np.sum(notionals))
    total_pnl = float(np.sum(asset_pnls))
    portfolio_return = total_pnl / total_notional if total_notional > 0 else 0.0

    # Hop attribution
    hop_attribution: Dict[int, float] = {}
    for k in range(k_plus_1):
        # Dollar impact of hop k
        # Effective base return increment for hop k: hop_returns[k] * (1 + fx_returns)
        k_base_ret = hop_returns[k] * (1.0 + fx_returns)
        hop_attribution[k] = float(np.sum(notionals * k_base_ret))

    # Channel attribution
    channel_attribution: Dict[str, float] = {
        "DIRECT": hop_attribution.get(0, 0.0),
        "SUPPLY": 0.0,
        "CUSTOMER": 0.0,
        "CREDIT": 0.0,
        "SECTOR": 0.0,
    }

    asset_valuations: List[AssetValuation] = []
    for i in range(num_nodes):
        node = node_ids[i]
        tick = tickers[i]
        notional_i = float(notionals[i])
        r_loc_i = float(effective_local_returns[i])
        r_fx_i = float(fx_returns[i])
        r_base_i = float(base_returns[i])
        pnl_i = float(asset_pnls[i])
        inst_detail = instrument_details[i]

        # Per-node hop PnLs
        node_hop_pnls = tuple(
            float(notional_i * hop_returns[k, i] * (1.0 + r_fx_i))
            for k in range(k_plus_1)
        )

        # Per-node channel breakdown
        node_channel_pnls: Dict[str, float] = {}
        if node_channel_breakdown and node in node_channel_breakdown:
            for ch, frac in node_channel_breakdown[node].items():
                pnl_ch = pnl_i * frac
                node_channel_pnls[ch] = pnl_ch
                channel_attribution[ch] = channel_attribution.get(ch, 0.0) + pnl_ch
        else:
            # Default direct hop 0 vs propagated hop 1..K
            node_channel_pnls["DIRECT"] = node_hop_pnls[0] if len(node_hop_pnls) > 0 else 0.0
            sum_prop = sum(node_hop_pnls[1:]) if len(node_hop_pnls) > 1 else 0.0
            node_channel_pnls["PROPAGATED"] = sum_prop

        asset_valuations.append(
            AssetValuation(
                node_id=node,
                ticker=tick,
                notional=notional_i,
                local_return=r_loc_i,
                fx_return=r_fx_i,
                base_return=r_base_i,
                pnl=pnl_i,
                hop_pnls=node_hop_pnls,
                channel_pnls=node_channel_pnls,
                instrument_detail=inst_detail,
            )
        )

    return PortfolioValuationResult(
        total_notional=total_notional,
        total_pnl=total_pnl,
        portfolio_return=portfolio_return,
        asset_valuations=tuple(asset_valuations),
        hop_attribution=hop_attribution,
        channel_attribution=channel_attribution,
    )
