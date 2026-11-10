"""Portfolio Ingestion, Validation, and Versioning Service per Section 12 & 14.2.
Enforces privacy: portfolio balances remain inside Tier 1/2 and are never sent to external LLMs.
"""

import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from typing import Dict, List, Optional, Tuple
import uuid

from app.domain.errors import ContagionDomainException, FailureCode
from app.domain.models import HoldingItem, PortfolioVersion


class PortfolioService:
    def __init__(self):
        self._previews: Dict[str, List[Dict]] = {}
        self._versions: Dict[str, PortfolioVersion] = {}

    def preview_csv(self, csv_text: str) -> Tuple[str, List[Dict], List[str]]:
        """Parses CSV and generates preview with validation candidates.
        Required columns: ticker (or symbol), notional (or value).
        Optional: asset_class, currency.
        """
        preview_id = str(uuid.uuid4())
        f = io.StringIO(csv_text.strip())
        reader = csv.DictReader(f)
        
        errors: List[str] = []
        rows: List[Dict] = []
        
        if not reader.fieldnames:
            raise ContagionDomainException(
                code=FailureCode.INPUT_UNIT_MISMATCH,
                message="CSV header is empty or missing",
                status_code=400,
            )

        # Normalize fieldnames
        field_map = {fn.strip().lower(): fn for fn in reader.fieldnames}
        ticker_col = field_map.get("ticker") or field_map.get("symbol") or field_map.get("asset")
        notional_col = field_map.get("notional") or field_map.get("value") or field_map.get("amount")

        if not ticker_col or not notional_col:
            raise ContagionDomainException(
                code=FailureCode.INPUT_UNIT_MISMATCH,
                message=f"CSV missing required columns ('ticker' and 'notional'). Found: {reader.fieldnames}",
                status_code=400,
            )

        total_notional = 0.0
        parsed_entries = []
        for i, row in enumerate(reader):
            raw_ticker = row[ticker_col].strip().upper()
            raw_notional = row[notional_col].strip().replace("$", "").replace(",", "")
            try:
                notional_val = float(raw_notional)
            except ValueError:
                errors.append(f"Row {i+1}: Invalid notional value '{raw_notional}'")
                continue

            if notional_val <= 0:
                errors.append(f"Row {i+1}: Notional must be positive, got {notional_val}")
                continue

            total_notional += notional_val
            parsed_entries.append({
                "ticker": raw_ticker,
                "notional": notional_val,
                "asset_class": row.get(field_map.get("asset_class", ""), "EQUITY").strip(),
                "currency": row.get(field_map.get("currency", ""), "USD").strip().upper(),
            })

        for entry in parsed_entries:
            entry["weight"] = entry["notional"] / total_notional if total_notional > 0 else 0.0
            rows.append(entry)

        self._previews[preview_id] = rows
        return preview_id, rows, errors

    def approve_portfolio_version(
        self,
        portfolio_id: str,
        preview_id: Optional[str] = None,
        holdings_data: Optional[List[Dict]] = None,
    ) -> PortfolioVersion:
        """Approves a portfolio preview into an immutable, hashed PortfolioVersion."""
        if preview_id and preview_id in self._previews:
            raw_rows = self._previews[preview_id]
        elif holdings_data is not None:
            raw_rows = holdings_data
        else:
            raise ContagionDomainException(
                code=FailureCode.ENTITY_AMBIGUOUS,
                message="Neither preview_id nor holdings_data provided for approval",
                status_code=404,
            )

        version_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()

        total_notional = sum(r["notional"] for r in raw_rows)
        holdings: List[HoldingItem] = []
        for r in raw_rows:
            node_id = f"NODE_{r['ticker']}"
            notional = float(r["notional"])
            weight = notional / total_notional if total_notional > 0 else 0.0
            holdings.append(
                HoldingItem(
                    node_id=node_id,
                    ticker=r["ticker"],
                    notional=notional,
                    weight=weight,
                    asset_class=r.get("asset_class", "EQUITY"),
                    currency=r.get("currency", "USD"),
                )
            )

        # Compute SHA-256 content hash
        hash_payload = {
            "portfolio_id": portfolio_id,
            "as_of": now_iso,
            "holdings": [
                {"ticker": h.ticker, "notional": h.notional, "currency": h.currency}
                for h in sorted(holdings, key=lambda x: x.ticker)
            ]
        }
        raw_json = json.dumps(hash_payload, sort_keys=True)
        content_hash = hashlib.sha256(raw_json.encode("utf-8")).hexdigest()

        version = PortfolioVersion(
            portfolio_version_id=version_id,
            portfolio_id=portfolio_id,
            base_currency="USD",
            as_of=now_iso,
            holdings=tuple(holdings),
            content_hash=content_hash,
        )
        self._versions[version_id] = version
        return version

    def get_portfolio_version(self, version_id: str) -> Optional[PortfolioVersion]:
        return self._versions.get(version_id)


portfolio_service = PortfolioService()
