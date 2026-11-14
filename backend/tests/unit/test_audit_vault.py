"""Unit tests for Four-Eyes Audit Vault & Executive Report Generator.
PRD Section 16 & Section 24.1 compliant.
"""

import pytest

from app.services.audit_vault_service import AuditStatus, AuditVaultService
from app.services.report_generator_service import ReportGeneratorService


def test_four_eyes_signoff_lifecycle_and_security():
    """Verifies complete Four-Eyes workflow, identity separation, and SHA-256 sealing."""
    vault = AuditVaultService()
    run_id = "test-run-citadel-099"

    # Step 1: Analyst submits run
    entry = vault.submit_for_review(
        run_id=run_id,
        scenario_name="Red Sea Tanker Escalation",
        submitted_by="elena.rostova@citadel.com",
        submitted_by_role="ANALYST",
        pnl_impact=-15_000_000.0,
        cvar_99=18_750_000.0,
        shock_summary={"BRENT_CRUDE": -0.30, "BALTIC_DRY": -0.25},
        comments="Submitted for CRO sign-off per monthly review.",
    )
    assert entry.status == AuditStatus.PENDING_REVIEW

    # Step 2: Submitter cannot approve their own run (Four-Eyes Enforcement)
    with pytest.raises(PermissionError, match="Four-Eyes Principle Violation"):
        vault.approve_run(
            run_id=run_id,
            approver_email="elena.rostova@citadel.com",
            approver_role="CHIEF_RISK_OFFICER",
        )

    # Step 3: Unauthorized role cannot approve
    with pytest.raises(PermissionError, match="Unauthorized: Role 'ANALYST'"):
        vault.approve_run(
            run_id=run_id,
            approver_email="marcus.vance@citadel.com",
            approver_role="ANALYST",
        )

    # Step 4: CRO signs off
    approved = vault.approve_run(
        run_id=run_id,
        approver_email="sarah.chen@citadel.com",
        approver_role="CHIEF_RISK_OFFICER",
        comments="Stress assumptions verified against commodity swap book.",
    )
    assert approved.status == AuditStatus.APPROVED_BY_CRO
    assert approved.approved_by == "sarah.chen@citadel.com"
    assert approved.cryptographic_seal_sha256 is not None
    assert len(approved.cryptographic_seal_sha256) == 64  # SHA-256 hex length

    # Step 5: Auditor locks into regulatory packet
    bundle = vault.lock_for_regulatory_audit(
        run_id=run_id,
        auditor_email="compliance.officer@citadel.com",
    )
    assert bundle["governance_status"] == "COMPLIANT_SR_11_7"
    assert bundle["audit_entry"]["status"] == AuditStatus.LOCKED_REGULATORY
    assert bundle["digital_seal"] == approved.cryptographic_seal_sha256


def test_executive_report_generator():
    """Verifies generation of board-ready PDF/HTML memo and structured breakdown."""
    generator = ReportGeneratorService()

    memo = generator.generate_memo(
        scenario_name="Taiwan Foundry Disruption",
        portfolio_notional=100_000_000.0,
        pnl_loss=-23_450_000.0,
        cvar_99=29_312_500.0,
        var_95=21_200_000.0,
        cro_name="Sarah Chen, Ph.D.",
        cro_title="Chief Risk Officer",
        firm_name="Citadel Global Equities",
    )

    assert "CONFIDENTIAL" in memo.classification
    assert memo.drawdown_pct == -23.45
    assert len(memo.top_losses) >= 3
    assert len(memo.critical_paths) >= 2
    assert len(memo.recommended_hedges) >= 2
    assert len(memo.sec_citations) >= 2

    # Assert HTML styling and contents
    assert "<!DOCTYPE html>" in memo.html_content
    assert "TAIWAN FOUNDRY DISRUPTION" in memo.html_content
    assert "FEDERAL RESERVE SR 11-7" in memo.html_content
    assert "Sarah Chen, Ph.D." in memo.html_content
