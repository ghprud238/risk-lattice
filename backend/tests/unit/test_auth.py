"""Unit tests for RiskLattice Authentication and Google SSO Service."""

import base64
import json
import time
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.auth_service import auth_service

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
    assert data["token"].startswith("rl_sess_")
    assert data["user"]["email"] == "sarah.chen@citadel-macro.com"
    assert data["user"]["role"] == "CHIEF_RISK_OFFICER"
    assert "MRM_ADMIN" in data["user"]["permissions"]
    assert "APPROVE" in data["user"]["permissions"]


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
    """Validates that logout invalidates session token."""
    auth_resp = auth_service.authenticate_google(
        email="analyst@jpmorgan.com",
        name="Elena Rostova",
        role="ANALYST",
    )
    token = auth_resp.token

    # Verify session is initially valid
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

    # Authenticate with fake JWT
    response = client.post("/api/v1/auth/google", json={"credential": fake_jwt})
    assert response.status_code == 200
    data = response.json()

    assert data["user"]["email"] == "alex.researcher@google.com"
    assert data["user"]["name"] == "Alex Researcher"
    assert data["user"]["organization"] == "Google.Com"
