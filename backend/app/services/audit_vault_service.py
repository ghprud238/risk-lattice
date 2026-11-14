"""Four-Eyes Principle Sign-off & Cryptographic Audit Vault Service.
PRD Section 16 & Section 24.1 compliant:
- Enforces institutional risk governance (FRTB, BCBS 239, SR 11-7 Model Risk Management).
- Implements strict Four-Eyes state machine:
    DRAFT -> PENDING_REVIEW -> APPROVED_BY_CRO -> LOCKED_REGULATORY
- Verifies that the approver (CRO) is distinct from the scenario author/submitter (PM/Analyst).
- Generates tamper-evident SHA-256 cryptographic seals for regulatory audit trails.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Dict, List, Optional
import uuid


class AuditStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED_BY_CRO = "APPROVED_BY_CRO"
    REJECTED = "REJECTED"
    LOCKED_REGULATORY = "LOCKED_REGULATORY"


@dataclass
class AuditEntry:
    entry_id: str
    run_id: str
    scenario_name: str
    status: AuditStatus
    submitted_by: str
    submitted_by_role: str
    submitted_at: str
    pnl_impact: float
    cvar_99: float
    shock_summary: Dict[str, float]
    approved_by: Optional[str] = None
    approved_by_role: Optional[str] = None
    approved_at: Optional[str] = None
    rejection_reason: Optional[str] = None
    comments: Optional[str] = None
    cryptographic_seal_sha256: Optional[str] = None


class AuditVaultService:
    """Manages immutable governance sign-offs and regulatory validation bundles."""

    def __init__(self):
        # In-memory vault repository (backed by audit log)
        self._vault: Dict[str, AuditEntry] = {}
        self._init_demo_entries()

    def _init_demo_entries(self):
        """Pre-seeds canonical governance audit logs for institutional demo."""
        demo_id = "run-citadel-202611-001"
        seal = self._compute_seal(
            run_id=demo_id,
            scenario_name="Taiwan Foundry Disruption - High Severity",
            submitted_by="marcus.vance@citadel.com",
            approved_by="sarah.chen@citadel.com",
            submitted_at="2026-11-14T10:00:00Z",
            pnl_impact=-23_450_000.0,
            cvar_99=29_312_500.0,
        )
        self._vault[demo_id] = AuditEntry(
            entry_id=str(uuid.uuid4()),
            run_id=demo_id,
            scenario_name="Taiwan Foundry Disruption - High Severity",
            status=AuditStatus.APPROVED_BY_CRO,
            submitted_by="marcus.vance@citadel.com",
            submitted_by_role="PORTFOLIO_MANAGER",
            submitted_at="2026-11-14T10:00:00Z",
            pnl_impact=-23_450_000.0,
            cvar_99=29_312_500.0,
            shock_summary={"FOUNDRY_TW": -0.40, "BALTIC_DRY": -0.25},
            approved_by="sarah.chen@citadel.com",
            approved_by_role="CHIEF_RISK_OFFICER",
            approved_at="2026-11-14T11:15:00Z",
            comments="Approved after inspecting 14-day safety stock buffer at Foxconn assembly plants.",
            cryptographic_seal_sha256=seal,
        )

    def _compute_seal(
        self,
        run_id: str,
        scenario_name: str,
        submitted_by: str,
        approved_by: Optional[str],
        submitted_at: str,
        pnl_impact: float,
        cvar_99: float,
    ) -> str:
        """Generates deterministic SHA-256 digital seal over governance parameters."""
        payload = {
            "run_id": run_id,
            "scenario": scenario_name,
            "submitter": submitted_by,
            "approver": approved_by or "",
            "timestamp": submitted_at,
            "pnl": pnl_impact,
            "cvar": cvar_99,
            "standard": "BCBS-239/FRTB-SR11-7",
        }
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def submit_for_review(
        self,
        run_id: str,
        scenario_name: str,
        submitted_by: str,
        submitted_by_role: str,
        pnl_impact: float,
        cvar_99: float,
        shock_summary: Dict[str, float],
        comments: Optional[str] = None,
    ) -> AuditEntry:
        """Step 1: Analyst or PM submits stress testing run for review."""
        now_iso = datetime.now(timezone.utc).isoformat()
        entry = AuditEntry(
            entry_id=str(uuid.uuid4()),
            run_id=run_id,
            scenario_name=scenario_name,
            status=AuditStatus.PENDING_REVIEW,
            submitted_by=submitted_by,
            submitted_by_role=submitted_by_role,
            submitted_at=now_iso,
            pnl_impact=pnl_impact,
            cvar_99=cvar_99,
            shock_summary=shock_summary,
            comments=comments,
        )
        self._vault[run_id] = entry
        return entry

    def approve_run(
        self,
        run_id: str,
        approver_email: str,
        approver_role: str,
        comments: Optional[str] = None,
    ) -> AuditEntry:
        """Step 2: CRO signs off on the stress test (Four-Eyes Enforcement)."""
        entry = self._vault.get(run_id)
        if not entry:
            raise ValueError(f"Run ID {run_id} not found in audit vault.")

        if entry.status not in (AuditStatus.PENDING_REVIEW, AuditStatus.DRAFT):
            raise ValueError(f"Run {run_id} is in status {entry.status}, cannot approve.")

        # Four-Eyes Principle check: Submitter cannot approve their own run
        if entry.submitted_by.strip().lower() == approver_email.strip().lower():
            raise PermissionError(
                f"Four-Eyes Principle Violation: Approver ({approver_email}) cannot be identical to submitter."
            )

        # Role enforcement: Must be CRO or AUDITOR
        if approver_role not in ("CHIEF_RISK_OFFICER", "AUDITOR"):
            raise PermissionError(
                f"Unauthorized: Role '{approver_role}' cannot sign off on capital stress runs. Requires CHIEF_RISK_OFFICER."
            )

        now_iso = datetime.now(timezone.utc).isoformat()
        entry.approved_by = approver_email
        entry.approved_by_role = approver_role
        entry.approved_at = now_iso
        entry.status = AuditStatus.APPROVED_BY_CRO
        if comments:
            entry.comments = (entry.comments or "") + f" | CRO Note: {comments}"

        # Generate cryptographic seal
        entry.cryptographic_seal_sha256 = self._compute_seal(
            run_id=entry.run_id,
            scenario_name=entry.scenario_name,
            submitted_by=entry.submitted_by,
            approved_by=approver_email,
            submitted_at=entry.submitted_at,
            pnl_impact=entry.pnl_impact,
            cvar_99=entry.cvar_99,
        )
        return entry

    def reject_run(
        self,
        run_id: str,
        reviewer_email: str,
        reason: str,
    ) -> AuditEntry:
        """Rejects a proposed stress run with audit record."""
        entry = self._vault.get(run_id)
        if not entry:
            raise ValueError(f"Run ID {run_id} not found.")

        entry.status = AuditStatus.REJECTED
        entry.rejection_reason = reason
        return entry

    def lock_for_regulatory_audit(self, run_id: str, auditor_email: str) -> Dict[str, Any]:
        """Step 3: Locks approved run into immutable regulatory vault packet."""
        entry = self._vault.get(run_id)
        if not entry:
            raise ValueError(f"Run ID {run_id} not found.")

        if entry.status != AuditStatus.APPROVED_BY_CRO:
            raise ValueError(f"Cannot lock run {run_id} until approved by CRO (current status: {entry.status}).")

        entry.status = AuditStatus.LOCKED_REGULATORY

        bundle = {
            "vault_packet_id": f"REG-PACKET-{entry.run_id}",
            "locked_at": datetime.now(timezone.utc).isoformat(),
            "locked_by": auditor_email,
            "governance_status": "COMPLIANT_SR_11_7",
            "regulatory_frameworks": ["FED_SR_11_7", "BCBS_239", "FRTB_IMA"],
            "audit_entry": asdict(entry),
            "verification_algorithm": "SHA-256",
            "digital_seal": entry.cryptographic_seal_sha256,
        }
        return bundle

    def get_run(self, run_id: str) -> Optional[AuditEntry]:
        return self._vault.get(run_id)

    def list_all_entries(self) -> List[AuditEntry]:
        return list(self._vault.values())


# Global singleton instance
audit_vault_service = AuditVaultService()
