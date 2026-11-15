# Feature 12: Google Workspace SSO & Role-Based Access Control (RBAC)

## Executive Overview
Enterprise risk platforms require rigorous identity verification and fine-grained authorization. RiskLattice implements native **Google Workspace SSO** with institutional domain verification (`@hedgefund.com`, `@bank.com`), cryptographically signed JWT sessions, and a **4-tier Role-Based Access Control (RBAC)** architecture.

---

## Role-Based Access Control (RBAC) Matrix

| User Role | View Graph & Stress Results | Run Simulations | Ingest Portfolios / SEC Filings | Authorize Runs (Four-Eyes Vault) | Export CCAR / Board Reports |
|---|:---:|:---:|:---:|:---:|:---:|
| **CHIEF_RISK_OFFICER** | Yes | Yes | Yes | **Yes** | Yes |
| **PORTFOLIO_MANAGER** | Yes | Yes | Yes | No | Yes |
| **RISK_ANALYST** | Yes | Yes | Yes | No | Draft Only |
| **AUDITOR / REGULATOR** | Read-Only | No | No | Verification Only | Yes |

---

## Institutional Google Authentication Flow

1. **User Sign-In**:
   - Institutional user clicks "Sign in with Google Workspace" or selects an authenticated enterprise persona in developer sandbox mode.
2. **Google OAuth2 JWT Verification**:
   - The frontend passes the Google ID token to `POST /api/v1/auth/google`.
   - The backend validates the cryptographic signature, checks token expiration, and verifies domain matching against allowed institutional tenants.
3. **Institutional Session Minting**:
   - The backend mints a secure HTTP-only cookie or Bearer session token containing user profile, email, organization, and mapped RBAC permissions.
4. **Endpoint Guardrails**:
   - High-privilege endpoints (such as `POST /api/v1/governance/signoff`) verify caller claims before executing sensitive state changes.

---

## Technical Implementation

### File Locations
- **Backend Service**: `backend/app/services/auth_service.py`
- **Unit Tests**: `backend/tests/unit/test_auth.py`
- **Frontend Context**: `frontend/src/context/AuthContext.tsx`
- **Frontend Login Component**: `frontend/src/components/LoginScreen.tsx`

### Persona Test Accounts (Sandbox)
- **Elena Rostova**: Chief Risk Officer (`elena.rostova@citadel-risk.com`)
- **David Vance**: Senior Quantitative PM (`david.vance@citadel-risk.com`)
- **Marcus Sterling**: Lead Stress Testing Analyst (`marcus.sterling@citadel-risk.com`)
- **Sarah Jenkins**: Senior Regulatory Auditor (`sarah.jenkins@ny-fed.gov`)

---

## Verification & Test Coverage
- `backend/tests/unit/test_auth.py::test_google_auth_sandbox_persona`
- `backend/tests/unit/test_auth.py::test_auth_me_endpoint`
- `backend/tests/unit/test_auth.py::test_auth_logout_terminates_session`
- `backend/tests/unit/test_auth.py::test_decode_google_jwt_payload`
