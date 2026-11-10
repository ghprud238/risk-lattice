"""
Natural-Language Shock Scenario Translator.
PRD Section 4 & 5:
- Converts user scenario text into canonical initial factor/node impulse vector s^(0)
- Constrained strictly to existing canonical node IDs in DuckDB
- Clamped strictly to [-0.95, +2.00] bounds
- Anti-hallucination validation with deterministic rule mapping + LLM routing
"""
import re
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from app.db.database import db_manager
from app.agents.llm_router import llm_router


class NodeShockImpulse(BaseModel):
    node_id: str
    shock_value: float = Field(ge=-0.95, le=2.00)
    rationale: str


class ShockTranslationResponse(BaseModel):
    scenario_title: str
    impulses: List[NodeShockImpulse]
    unmapped_concepts: List[str] = Field(default_factory=list)


class ShockTranslator:
    def __init__(self, router=None, db=None):
        self.router = router or llm_router
        self.db = db or db_manager
        self.valid_nodes = self._load_canonical_node_ids()

    def _load_canonical_node_ids(self) -> Dict[str, str]:
        """Loads valid node_ids and their types from DuckDB."""
        try:
            df = self.db.query_df("SELECT node_id, node_type, name FROM graph_nodes;")
            return {row["node_id"]: row["name"] for _, row in df.iterrows()}
        except Exception:
            return {}

    def translate_prompt(self, user_text: str) -> ShockTranslationResponse:
        """
        Parses scenario description into canonical shock vector s^(0).
        Constrained strictly to known nodes, clamped to [-0.95, 2.00].
        """
        if not self.valid_nodes:
            self.valid_nodes = self._load_canonical_node_ids()

        # Rule-based semantic mapper for common macro & supply chain keywords
        rule_impulses: List[NodeShockImpulse] = []
        lower = user_text.lower()

        # Taiwan / Semiconductor Foundries
        if any(w in lower for w in ["taiwan", "tsmc", "wafer", "foundry", "hsinchu", "chip fab"]):
            val = -0.70 if any(w in lower for w in ["blockade", "halt", "earthquake", "war", "freeze"]) else -0.40
            rule_impulses.append(NodeShockImpulse(node_id="FOUNDRY_TW", shock_value=val, rationale="Taiwan semiconductor foundry disruption"))

        # Baltic Dry / Shipping / Maritime
        if any(w in lower for w in ["shipping", "freight", "baltic", "panama", "suez", "transit halt", "port"]):
            val = 1.80 if "surge" in lower or "spike" in lower else -0.48
            rule_impulses.append(NodeShockImpulse(node_id="BALTIC_DRY", shock_value=val, rationale="Maritime freight disruption"))

        # Crude Oil / Brent / Energy
        if any(w in lower for w in ["oil", "brent", "crude", "petroleum", "hormuz", "tanker"]):
            val = 0.65 if any(w in lower for w in ["spike", "surge", "blockade"]) else -0.55
            rule_impulses.append(NodeShockImpulse(node_id="BRENT_CRUDE", shock_value=val, rationale="Crude oil price shock"))

        # Rates / Yields / US10Y
        if any(w in lower for w in ["rate jump", "real rate", "duration shock", "10-year", "10y", "treasury yield"]):
            rule_impulses.append(NodeShockImpulse(node_id="US10Y_REAL", shock_value=0.026, rationale="Real interest rate jump"))

        # Credit Spreads / HY OAS / Interbank
        if any(w in lower for w in ["credit spread", "high yield", "oas", "spread widening", "credit freeze"]):
            rule_impulses.append(NodeShockImpulse(node_id="HY_OAS", shock_value=0.085, rationale="High yield spread blowout"))
        if any(w in lower for w in ["sofr", "interbank", "funding freeze", "liquidity crunch"]):
            rule_impulses.append(NodeShockImpulse(node_id="SOFR_SPREAD", shock_value=0.035, rationale="SOFR interbank funding spread surge"))

        # Volatility / VIX
        if any(w in lower for w in ["vix", "market panic", "volatility surge", "crash"]):
            rule_impulses.append(NodeShockImpulse(node_id="VIX", shock_value=0.85, rationale="CBOE volatility index spike"))

        # Dollar / DXY
        if any(w in lower for w in ["dollar surge", "dxy", "strong dollar"]):
            rule_impulses.append(NodeShockImpulse(node_id="DXY", shock_value=0.140, rationale="US Dollar Index appreciation"))

        # Lithium / Batteries
        if any(w in lower for w in ["lithium", "battery", "salar", "chile"]):
            rule_impulses.append(NodeShockImpulse(node_id="LITHIUM_BRINE_SA", shock_value=-0.60, rationale="South American lithium brine supply disruption"))

        # Build mock response for LLM router
        mock_resp = ShockTranslationResponse(
            scenario_title=user_text[:60],
            impulses=rule_impulses if rule_impulses else [
                NodeShockImpulse(node_id="US10Y_REAL", shock_value=0.02, rationale="Default macro duration shock")
            ],
            unmapped_concepts=[]
        )

        valid_list_str = ", ".join(list(self.valid_nodes.keys())[:25])
        prompt = f"""
Translate this macro scenario into an initial impulse vector s^(0):
Scenario: "{user_text}"

Canonical valid node IDs: {valid_list_str}
For each impacted node, assign a shock value between -0.95 and +2.00.
"""
        response: ShockTranslationResponse = self.router.complete_structured(
            prompt=prompt,
            response_model=ShockTranslationResponse,
            system_prompt="You are a quantitative macro shock scenario translator.",
            mock_response=mock_resp
        )

        # Validate and clamp all impulses strictly
        clamped_impulses = []
        for imp in response.impulses:
            if imp.node_id in self.valid_nodes:
                clamped_val = float(max(-0.95, min(2.00, imp.shock_value)))
                clamped_impulses.append(NodeShockImpulse(
                    node_id=imp.node_id,
                    shock_value=round(clamped_val, 4),
                    rationale=imp.rationale or f"Shock on {imp.node_id}"
                ))

        return ShockTranslationResponse(
            scenario_title=response.scenario_title or user_text[:60],
            impulses=clamped_impulses,
            unmapped_concepts=response.unmapped_concepts
        )

    def to_shock_vector(self, translation: ShockTranslationResponse) -> Dict[str, float]:
        """Converts ShockTranslationResponse into a dict for ContagionPropagator."""
        return {imp.node_id: imp.shock_value for imp in translation.impulses}


# Global translator instance
shock_translator = ShockTranslator()
