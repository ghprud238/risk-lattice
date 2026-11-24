# Feature 12: Dual Enterprise Authentication (Google SSO + Proprietary System) & RBAC

## Executive Overview
Enterprise risk platforms require rigorous identity verification, domain fencing, and fine-grained authorization. RiskLattice implements a **dual-option enterprise authentication architecture**:
1. **Google Workspace SSO**: Native Google Identity Services (GIS) OAuth 2.0 with institutional domain verification (`@hedgefund.com`, `@bank.com`), cryptographically signed JWT sessions, and developer sandbox personas.
2. **Proprietary Institutional Authentication**: Dedicated username/email + password authentication system utilizing salted bcrypt hashing (`rounds=10`), signed HS256 JWT tokens (24h lifespan), persistent DuckDB user/session storage, and immutable audit logs.
3. **4-Tier Institutional Role-Based Access Control (RBAC)**: Enforces access restrictions across simulation parameters, portfolio uploads, executive reporting, and cryptographic four-eyes sign-offs.

---

## Role-Based Access Control (RBAC) Matrix

| User Role | View Graph & Stress Results | Run Simulations | Ingest Portfolios / SEC Filings | Authorize Runs (Four-Eyes Vault) | Export CCAR / Board Reports |
|---|:---:|:---:|:---:|:---:|:---:|
| **CHIEF_RISK_OFFICER** | Yes | Yes | Yes | **Yes** | Yes |
| **PORTFOLIO_MANAGER** | Yes | Yes | Yes | No | Yes |
| **ANALYST** | Yes | Yes | Yes | No | Draft Only |
| **AUDITOR** | Read-Only | No | No | Verification Only | Yes |

---

## Proprietary Authentication Architecture & Database Tables

The proprietary login system stores credentials and tracks active sessions directly in DuckDB:

### 1. `users` Table
```sql
CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    full_name VARCHAR NOT NULL,
    password_hash VARCHAR NOT NULL,  -- Salted bcrypt hash ($2b$10$...)
    institution VARCHAR NOT NULL,
    role VARCHAR NOT NULL,           -- CHIEF_RISK_OFFICER, PORTFOLIO_MANAGER, ANALYST, AUDITOR
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

### 2. `user_sessions` Table
```sql
CREATE TABLE IF NOT EXISTS user_sessions (
    session_id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL REFERENCES users(user_id),
    session_token VARCHAR UNIQUE NOT NULL, -- Signed HS256 JWT
    issued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    ip_address VARCHAR,
    user_agent VARCHAR,
    is_revoked BOOLEAN DEFAULT FALSE
);
```

### 3. `user_audit_logs` Table
```sql
CREATE TABLE IF NOT EXISTS user_audit_logs (
    log_id VARCHAR PRIMARY KEY,
    user_id VARCHAR,
    email VARCHAR NOT NULL,
    event_type VARCHAR NOT NULL,  -- USER_REGISTERED, LOGIN_SUCCESS, LOGIN_FAILURE, LOGOUT
    ip_address VARCHAR,
    user_agent VARCHAR,
    details VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Pre-Seeded Institutional Accounts
RiskLattice seeds 4 default institutional accounts automatically on startup:
- **Chief Risk Officer**: `cro@risklattice.com` / `cro123!`
- **Portfolio Manager**: `pm@risklattice.com` / `pm123!`
- **Quantitative Analyst**: `analyst@risklattice.com` / `analyst123!`
- **Compliance Auditor**: `auditor@risklattice.com` / `auditor123!`

---

## Technical Implementation

### File Locations
- **Backend Service**: `backend/app/services/auth_service.py`
- **Database Schema**: `backend/app/db/schema.sql`
- **API Endpoints**: `backend/app/main.py` (`/api/v1/auth/*`)
- **Unit Tests**: `backend/tests/unit/test_auth.py`
- **Frontend Context**: `frontend/src/context/AuthContext.tsx`
- **Frontend Login Component**: `frontend/src/components/LoginScreen.tsx`

---

## Verification & Test Coverage
- `backend/tests/unit/test_auth.py::test_proprietary_registration_and_login`
- `backend/tests/unit/test_auth.py::test_default_seeded_accounts`
- `backend/tests/unit/test_auth.py::test_google_auth_sandbox_persona`
- `backend/tests/unit/test_auth.py::test_auth_me_endpoint`
- `backend/tests/unit/test_auth.py::test_auth_logout_terminates_session`
- `backend/tests/unit/test_auth.py::test_decode_google_jwt_payload`
- `backend/tests/unit/test_auth.py::test_list_users_endpoint`
