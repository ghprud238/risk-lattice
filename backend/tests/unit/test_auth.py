"""Unit and Integration Tests for RiskLattice Authentication & Authorization.
Covers:
1. Proprietary username/password registration & login with bcrypt and JWT
2. Google Workspace OAuth & Identity Services token decoding
3. Role-Based Access Control (RBAC) permissions
4. Default pre-seeded institutional accounts
5. DuckDB persistence in users, user_sessions, and user_audit_logs tables
6. Session lifecycle and logout invalidation
"""

import base64
import json
import time
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.auth_service import auth_service
from app.db.database import db_manager

client = TestClient(app)


def test_google_auth_sandbox_persona():
    """Validates login with institutional sandbox persona and role assignment."""
    payload = {
        "email": "sarah.chen@citadel-macro.com",
        "name": "Sarah Chen",
        "role": "CHIEF_RISK_OFFICER",
        "organization": "Citadel Macro Fund",
    }
    response = client.post("/api/v1/auth/google", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "token" in data
    assert len(data["token"]) > 20
    assert data["user"]["email"] == "sarah.chen@citadel-macro.com"
    assert data["user"]["role"] == "CHIEF_RISK_OFFICER"
    assert "MRM_ADMIN" in data["user"]["permissions"]
    assert "APPROVE" in data["user"]["permissions"]


def test_proprietary_registration_and_login():
    """Validates proprietary registration, password hashing, and subsequent login."""
    unique_email = f"trader_{int(time.time() * 1000)}@hedgefund.com"
    reg_payload = {
        "email": unique_email,
        "password": "StrongPassword2026!",
        "name": "Jordan Belfort",
        "role": "PORTFOLIO_MANAGER",
        "organization": "Stratton Oakmont Macro",
    }
    # 1. Register
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 200, reg_res.text
    reg_data = reg_res.json()
    assert reg_data["user"]["email"] == unique_email
    assert reg_data["user"]["role"] == "PORTFOLIO_MANAGER"
    assert "INGEST_PORTFOLIO" in reg_data["user"]["permissions"]
    token = reg_data["token"]

    # 2. Verify in DB
    user_rows = db_manager.execute("SELECT email, password_hash, role FROM users WHERE email = ?", [unique_email])
    assert len(user_rows) == 1
    assert user_rows[0][0] == unique_email
    assert user_rows[0][1].startswith("$2b$") or user_rows[0][1].startswith("$2a$")  # bcrypt hash
    assert user_rows[0][2] == "PORTFOLIO_MANAGER"

    # 3. Login with correct password
    login_payload = {
        "email": unique_email,
        "password": "StrongPassword2026!",
    }
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["user"]["email"] == unique_email
    assert "token" in login_data

    # 4. Login with incorrect password
    bad_login = client.post("/api/v1/auth/login", json={"email": unique_email, "password": "WrongPassword!"})
    assert bad_login.status_code == 401

    # 5. Duplicate registration should fail
    dup_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert dup_res.status_code == 400


def test_default_seeded_accounts():
    """Validates that default institutional accounts are seeded and can login."""
    # Test CRO default
    cro_login = client.post("/api/v1/auth/login", json={"email": "cro@risklattice.com", "password": "cro123!"})
    assert cro_login.status_code == 200
    cro_data = cro_login.json()
    assert cro_data["user"]["role"] == "CHIEF_RISK_OFFICER"
    assert "MRM_ADMIN" in cro_data["user"]["permissions"]

    # Test Analyst default
    analyst_login = client.post("/api/v1/auth/login", json={"email": "analyst@risklattice.com", "password": "analyst123!"})
    assert analyst_login.status_code == 200
    analyst_data = analyst_login.json()
    assert analyst_data["user"]["role"] == "ANALYST"


def test_auth_me_endpoint():
    """Validates /api/v1/auth/me returns active session user profile."""
    # Authenticate
    auth_resp = auth_service.authenticate_google(
        email="marcus.vance@point72-tmt.com",
        name="Marcus Vance",
        role="PORTFOLIO_MANAGER",
        organization="Point72 Asset Management",
    )
    token = auth_resp.token

    # Query /me
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["user"]["email"] == "marcus.vance@point72-tmt.com"
    assert data["user"]["role"] == "PORTFOLIO_MANAGER"
    assert "INGEST_PORTFOLIO" in data["user"]["permissions"]


def test_auth_logout_terminates_session():
    """Validates that logout invalidates session token across memory and DB."""
    auth_resp = auth_service.authenticate_google(
        email="analyst@jpmorgan.com",
        name="Elena Rostova",
        role="ANALYST",
    )
    token = auth_resp.token

    headers = {"Authorization": f"Bearer {token}"}
    me_resp1 = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp1.status_code == 200

    # Logout
    logout_resp = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_resp.status_code == 200
    assert logout_resp.json()["logged_out"] is True

    # Subsequent request must be 401 Unauthorized
    me_resp2 = client.get("/api/v1/auth/me", headers=headers)
    assert me_resp2.status_code == 401


def test_decode_google_jwt_payload():
    """Validates JWT decoding for Google Identity Services tokens."""
    header = {"alg": "RS256", "typ": "JWT"}
    payload = {
        "iss": "https://accounts.google.com",
        "sub": "109876543210987654321",
        "email": "alex.researcher@google.com",
        "email_verified": True,
        "name": "Alex Researcher",
        "picture": "https://lh3.googleusercontent.com/a/sample-photo",
        "hd": "google.com",
        "exp": int(time.time()) + 3600,
    }

    def b64url(d: dict) -> str:
        s = json.dumps(d).encode("utf-8")
        return base64.urlsafe_b64encode(s).decode("utf-8").rstrip("=")

    fake_jwt = f"{b64url(header)}.{b64url(payload)}.fakesignature123456789"
    decoded = auth_service.decode_google_id_token(fake_jwt)
    assert decoded["email"] == "alex.researcher@google.com"
    assert decoded["name"] == "Alex Researcher"
    assert decoded["hd"] == "google.com"


def test_list_users_endpoint():
    """Validates that /api/v1/auth/users lists all institutional users."""
    login = client.post("/api/v1/auth/login", json={"email": "cro@risklattice.com", "password": "cro123!"})
    token = login.json()["token"]

    res = client.get("/api/v1/auth/users", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    users = res.json()["users"]
    assert len(users) >= 4
    emails = [u["email"] for u in users]
    assert "cro@risklattice.com" in emails
    assert "pm@risklattice.com" in emails
