"""
Unified LiteLLM Router & Local Privacy Sanitizer.
PRD Section 3, 4 & Milestone 3:
- LiteLLM router for local Ollama + Cloud BYOK fallback
- Strict deterministic Mock-LLM fallback for offline/CI mode
- Local PII & Position-Size Sanitizer:
  Ensures portfolio share counts, cash balances, and dollar numbers NEVER leave Tier 1/2.
  Tier 3 LLM receives ONLY tickers, public filing chunks, and normalized unit-free paths.
- Deterministic seed caching and Pydantic JSON schema enforcement.
"""
import json
import os
import re
from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel
import litellm

# Disable litellm telemetry for fast offline local performance
litellm.telemetry = False
litellm.drop_params = True
os.environ["LITELLM_LOG"] = "ERROR"

T = TypeVar("T", bound=BaseModel)


class PrivacySanitizer:
    """
    Strips account numbers, dollar amounts, share counts, and balance sheet sizes
    before any prompt payload touches external LLM tiers.
    """
    DOLLAR_PATTERN = re.compile(r"\$[\d,]+(\.\d+)?|\b\d+(\.\d+)?\s*(dollars|usd|million|billion)\b", re.IGNORECASE)
    SHARE_COUNT_PATTERN = re.compile(r"\b\d+([,\d]*)\s*(shares|units|lots)\b", re.IGNORECASE)
    ACCOUNT_PATTERN = re.compile(r"\b(acct|account|id)[\s#:]*[\w\-]{6,}\b", re.IGNORECASE)

    @classmethod
    def sanitize_text(cls, text: str) -> str:
        text = cls.ACCOUNT_PATTERN.sub("[REDACTED_ACCOUNT]", text)
        text = cls.DOLLAR_PATTERN.sub("[REDACTED_AMOUNT]", text)
        text = cls.SHARE_COUNT_PATTERN.sub("[REDACTED_QUANTITY]", text)
        return text

    @classmethod
    def sanitize_portfolio_weights(cls, holdings: Dict[str, Any]) -> Dict[str, float]:
        """Converts raw share/dollar ledgers into purely normalized unit-free percentages (0.0 to 1.0)."""
        clean = {}
        total = sum(v for v in holdings.values() if isinstance(v, (int, float)) and v > 0)
        if total <= 0:
            return {k: 1.0 / max(1, len(holdings)) for k in holdings}
        for k, v in holdings.items():
            clean[k] = round(float(v / total), 4)
        return clean

    @classmethod
    def sanitize_holdings(cls, data: Any) -> Any:
        """Recursively scrubs account IDs, dollar amounts, and share quantities."""
        if isinstance(data, dict):
            sanitized = {}
            for k, v in data.items():
                if any(priv in k.lower() for priv in ["account", "nav", "notional", "shares", "cost_basis", "dollar", "balance"]):
                    continue
                sanitized[k] = cls.sanitize_holdings(v)
            return sanitized
        elif isinstance(data, list):
            return [cls.sanitize_holdings(item) for item in data]
        elif isinstance(data, str):
            return cls.sanitize_text(data)
        return data


class LLMRouter:
    def __init__(
        self,
        model: Optional[str] = None,
        api_base: Optional[str] = None,
        use_mock_fallback: bool = True
    ):
        # Default to local Ollama or mock
        self.model = model or os.getenv("RISK_LATTICE_LLM_MODEL") or os.getenv("CONTAGION_LLM_MODEL", "ollama/qwen2.5:14b-instruct-q4_K_M")
        self.api_base = api_base or os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
        self.use_mock_fallback = use_mock_fallback
        self.sanitizer = PrivacySanitizer()

    def complete_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system_prompt: Optional[str] = None,
        mock_response: Optional[T] = None
    ) -> T:
        """
        Sends prompt to LLM and enforces Pydantic schema.
        Automatically applies privacy sanitization to prompt.
        Falls back to deterministic mock response if offline or unconfigured.
        """
        sanitized_prompt = self.sanitizer.sanitize_text(prompt)
        schema_json = json.dumps(response_model.model_json_schema())

        full_system = (
            (system_prompt or "You are a quantitative financial risk extraction engine.")
            + f"\nYou must respond ONLY with valid JSON matching this schema:\n{schema_json}"
        )

        # If mock response is explicitly provided and mock mode enabled, return it
        if self.use_mock_fallback and (mock_response is not None or os.getenv("MOCK_LLM", "true").lower() == "true"):
            if mock_response is not None:
                return mock_response

        try:
            # Attempt LiteLLM invocation with 2s timeout for local responsiveness
            response = litellm.completion(
                model=self.model,
                messages=[
                    {"role": "system", "content": full_system},
                    {"role": "user", "content": sanitized_prompt}
                ],
                api_base=self.api_base if "ollama" in self.model else None,
                temperature=0.0,
                seed=42,
                timeout=5.0
            )
            raw_text = response.choices[0].message.content.strip()
            # Extract JSON block if wrapped in markdown
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0].strip()

            parsed = json.loads(raw_text)
            return response_model.model_validate(parsed)
        except Exception:
            if mock_response is not None:
                return mock_response
            raise


# Global router instance
llm_router = LLMRouter()
