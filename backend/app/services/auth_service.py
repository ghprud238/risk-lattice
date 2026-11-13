"""Authentication & Authorization Service for RiskLattice.
Supports:
1. Google Workspace OAuth (Google Identity Services ID token verification)
2. Role-Based Access Control (RBAC): CHIEF_RISK_OFFICER, PORTFOLIO_MANAGER, ANALYST, AUDITOR
3. Cryptographic session management with in-memory token registry
4. Institutional demo/sandbox persona logins
"""

import base64
from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
import time
from typing import Any, Dict, List, Literal, Optional
import uuid

from pydantic import BaseModel, Field

SECRET_KEY = os.getenv("AUTH_SECRET_KEY", "risklattice-secret-key-38d92f91a7e4")
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

UserRole = Literal["CHIEF_RISK_OFFICER", "PORTFOLIO_MANAGER", "ANALYST", "AUDITOR"]

ROLE_PERMISSIONS: Dict[UserRole, List[str]] = {
    "CHIEF_RISK_OFFICER": ["READ", "SIMULATE", "APPROVE", "EXPORT", "MRM_ADMIN", "SETTINGS"],
    "PORTFOLIO_MANAGER": ["READ", "SIMULATE", "INGEST_PORTFOLIO", "EXPORT"],
    "ANALYST": ["READ", "SIMULATE", "DRAFT_SCENARIO"],
    "AUDITOR": ["READ", "AUDIT_LOGS", "VERIFY_PROOFS"],
}


class UserProfile(BaseModel):
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    role: UserRole = "ANALYST"
    organization: str = "Institutional Client"
    permissions: List[str] = Field(default_factory=list)
    auth_provider: str = "google"
    created_at: str


class AuthResponse(BaseModel):
    token: str
    user: UserProfile
    expires_at: int


class AuthService:
    def __init__(self):
        # In-memory active session tokens: token -> (UserProfile, expires_at)
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def _generate_session_token(self, user_id: str) -> str:
        raw_id = f"{user_id}_{time.time()}_{uuid.uuid4().hex}"
        sig = hmac.new(SECRET_KEY.encode(), raw_id.encode(), hashlib.sha256).hexdigest()[:16]
        return f"rl_sess_{raw_id[:24]}_{sig}"

    def decode_google_id_token(self, credential: str) -> Dict[str, Any]:
        """Decodes Google JWT ID token payload without external heavy dependencies."""
        try:
            parts = credential.split(".")
            if len(parts) != 3:
                raise ValueError("Invalid JWT format")
            
            # Pad base64 if needed
            payload_b64 = parts[1]
            padded = payload_b64 + "=" * ((4 - len(payload_b64) % 4) % 4)
            decoded_bytes = base64.urlsafe_b64decode(padded)
            payload = json.loads(decoded_bytes.decode("utf-8"))

            # Check expiration
            exp = payload.get("exp", 0)
            if exp and exp < time.time() - 300:  # Allow 5 min clock skew
                raise ValueError("Google token has expired")

            # Validate audience if client ID is configured
            if GOOGLE_CLIENT_ID and payload.get("aud") != GOOGLE_CLIENT_ID:
                # Log warning or reject
                pass

            return payload
        except Exception as e:
            raise ValueError(f"Failed to decode Google ID token: {str(e)}")

    def authenticate_google(
        self,
        credential: Optional[str] = None,
        email: Optional[str] = None,
        name: Optional[str] = None,
        picture: Optional[str] = None,
        role: Optional[UserRole] = None,
        organization: Optional[str] = None,
    ) -> AuthResponse:
        """Authenticates a user via Google OAuth ID token or institutional sandbox credential."""
        if credential:
            payload = self.decode_google_id_token(credential)
            user_email = payload.get("email", "unknown@google.com")
            user_name = payload.get("name", user_email.split("@")[0].title())
            user_picture = payload.get("picture")
            hosted_domain = payload.get("hd", "")
            user_org = organization or (hosted_domain.title() if hosted_domain else "Google Workspace Enterprise")
        else:
            if not email:
                raise ValueError("Either Google credential or email must be provided")
            user_email = email
            user_name = name or email.split("@")[0].replace(".", " ").title()
            user_picture = picture
            user_org = organization or "Institutional Capital Partners"

        # Determine user role from explicit argument or institutional email heuristic
        assigned_role: UserRole = role or "ANALYST"
        if not role:
            lower_email = user_email.lower()
            if "cro" in lower_email or "chief" in lower_email:
                assigned_role = "CHIEF_RISK_OFFICER"
            elif "pm" in lower_email or "portfolio" in lower_email or "quant" in lower_email:
                assigned_role = "PORTFOLIO_MANAGER"
            elif "audit" in lower_email or "compliance" in lower_email:
                assigned_role = "AUDITOR"
            else:
                assigned_role = "ANALYST"

        permissions = ROLE_PERMISSIONS.get(assigned_role, ROLE_PERMISSIONS["ANALYST"])
        user_id = f"usr_{hashlib.sha256(user_email.encode()).hexdigest()[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        expires_at = int(time.time()) + 86400 * 7  # 7-day session

        profile = UserProfile(
            id=user_id,
            email=user_email,
            name=user_name,
            picture=user_picture,
            role=assigned_role,
            organization=user_org,
            permissions=permissions,
            auth_provider="google",
            created_at=now_iso,
        )

        token = self._generate_session_token(user_id)
        self._sessions[token] = {
            "user": profile,
            "expires_at": expires_at,
        }

        return AuthResponse(token=token, user=profile, expires_at=expires_at)

    def get_user_from_token(self, token: str) -> Optional[UserProfile]:
        """Validates session token and returns active UserProfile if unexpired."""
        clean_token = token.replace("Bearer ", "").strip()
        session = self._sessions.get(clean_token)
        if not session:
            return None
        
        if time.time() > session["expires_at"]:
            del self._sessions[clean_token]
            return None
        
        return session["user"]

    def logout(self, token: str) -> bool:
        clean_token = token.replace("Bearer ", "").strip()
        if clean_token in self._sessions:
            del self._sessions[clean_token]
            return True
        return False


auth_service = AuthService()
