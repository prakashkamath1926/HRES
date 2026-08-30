"""
Auth API — Production-ready authentication with:
- Email + Password registration and login (with bcrypt)
- Google OAuth 2.0 token verification
- JWT-based session management
- Role-based access control (RBAC)
- Secure logout (token blacklist via in-memory set for now)
"""
import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime, timedelta

from backend.app.core.config import settings
from backend.app.repositories.users import (
    create_user, get_user_by_email, authenticate_email_password,
    upsert_google_user
)

logger = logging.getLogger("hres.auth")
router = APIRouter(prefix="/auth", tags=["auth"])

# ── Token blacklist (in-memory; use Redis in production) ───────────────────────
_revoked_tokens: set = set()

# ── Security ────────────────────────────────────────────────────────────────────
security = HTTPBearer(auto_error=False)

# ── Org type → default role mapping ────────────────────────────────────────────
ORG_ROLE_MAP = {
    "government": "government",
    "civil": "government",
    "ngo": "ngo",
    "hospital": "hospital",
    "fire_station": "fire_station",
    "police": "police",
    "organization": "organization",
    "civilian": "civilian",
}


# ── Pydantic Models ─────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    org_type: Optional[str] = "civilian"
    org_id: Optional[str] = None  # official organization ID/registration number

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


class GoogleLoginRequest(BaseModel):
    token: str  # Google ID token


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


# ── JWT Helpers ─────────────────────────────────────────────────────────────────

def _create_jwt(data: dict, expires_hours: int = 24) -> str:
    try:
        import jwt
    except ImportError:
        raise HTTPException(500, "PyJWT not installed. Run: pip install pyjwt")
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=expires_hours)
    payload["iat"] = datetime.utcnow()
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def _decode_jwt(token: str) -> dict:
    try:
        import jwt
        return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {str(e)}")


def _safe_user(user: dict) -> dict:
    """Return only safe, non-PII fields for the token payload."""
    return {
        "sub": user.get("email"),
        "email": user.get("email"),
        "name": user.get("name"),
        "role": user.get("role", "civilian"),
        "org_type": user.get("org_type"),
        "org_id": user.get("org_id"),
        "org_mail": user.get("org_mail"),
        "employee_id": user.get("employee_id"),
    }


# ── Endpoints ───────────────────────────────────────────────────────────────────

@router.post("/register", response_model=AuthResponse)
def register(req: RegisterRequest):
    """Register with email, password, and organization type."""
    existing = get_user_by_email(req.email)
    if existing:
        raise HTTPException(400, "An account with this email already exists. Please sign in.")

    role = ORG_ROLE_MAP.get(req.org_type or "civilian", "civilian")
    user = create_user(
        email=req.email,
        name=req.name,
        role=role,
        org_type=req.org_type,
        org_id=req.org_id,
        password=req.password,
    )
    if not user:
        raise HTTPException(500, "Registration failed. Please try again.")

    token = _create_jwt(_safe_user(user))
    return AuthResponse(access_token=token, user=_safe_user(user))


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest):
    """Login with email and password."""
    user = authenticate_email_password(req.email, req.password)
    if not user:
        raise HTTPException(401, "Invalid email or password.")
    token = _create_jwt(_safe_user(user))
    return AuthResponse(access_token=token, user=_safe_user(user))


@router.post("/google", response_model=AuthResponse)
def google_login(req: GoogleLoginRequest):
    """Login or register via Google OAuth token."""

    # ── Dev/Mock mode ──────────────────────────────────────────────────────────
    if req.token.startswith("mock_"):
        if not settings.GOOGLE_CLIENT_ID:
            email = req.token.replace("mock_", "")
            name = email.split("@")[0].capitalize()
            user = get_user_by_email(email)
            if not user:
                org_type = _infer_org_from_email(email)
                role = ORG_ROLE_MAP.get(org_type, "civilian")
                user = create_user(email=email, name=name, role=role, org_type=org_type, google_sub=f"mock_{email}")
            token = _create_jwt(_safe_user(user))
            return AuthResponse(access_token=token, user=_safe_user(user))
        raise HTTPException(400, "Mock tokens are not allowed when Google Client ID is configured.")

    # ── Real Google token verification ─────────────────────────────────────────
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(500, "GOOGLE_CLIENT_ID is not configured in the server environment.")

    try:
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests
        idinfo = id_token.verify_oauth2_token(
            req.token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=10
        )
    except ValueError as e:
        raise HTTPException(401, f"Google token verification failed: {str(e)}")

    email = idinfo.get("email")
    name = idinfo.get("name", email)
    google_sub = idinfo.get("sub")

    if not email:
        raise HTTPException(400, "Google account does not have a verified email address.")

    user = upsert_google_user(email=email, name=name, google_sub=google_sub)
    token = _create_jwt(_safe_user(user))
    return AuthResponse(access_token=token, user=_safe_user(user))


@router.post("/logout")
def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Invalidate the current JWT token."""
    if credentials:
        _revoked_tokens.add(credentials.credentials)
    return {"message": "Logged out successfully."}


@router.get("/me")
def get_me(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user info from JWT."""
    if not credentials:
        raise HTTPException(401, "Not authenticated")
    if credentials.credentials in _revoked_tokens:
        raise HTTPException(401, "Token has been revoked. Please log in again.")
    payload = _decode_jwt(credentials.credentials)
    return {k: v for k, v in payload.items() if k not in ("exp", "iat")}


# ── Dependency for protected routes ────────────────────────────────────────────

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    if not credentials:
        raise HTTPException(401, "Authentication required")
    if credentials.credentials in _revoked_tokens:
        raise HTTPException(401, "Session expired. Please log in again.")
    return _decode_jwt(credentials.credentials)


def require_role(allowed_roles: list[str]):
    def checker(user: dict = Depends(get_current_user)):
        if user.get("role") not in allowed_roles and user.get("role") != "admin":
            raise HTTPException(403, f"Access denied. Required role: {allowed_roles}")
        return user
    return checker


class ProfileUpdateRequest(BaseModel):
    org_mail: Optional[str] = None
    employee_id: Optional[str] = None

@router.put("/profile")
def update_profile(req: ProfileUpdateRequest, user: dict = Depends(get_current_user)):
    from backend.app.repositories.users import update_user_profile
    updated = update_user_profile(user["email"], req.org_mail, req.employee_id)
    if not updated:
        raise HTTPException(404, "User not found")
    return _safe_user(updated)

@router.get("/history")
def get_user_history(user: dict = Depends(get_current_user)):
    """Fetch incidents the user interacted with via audit_events."""
    from backend.app.repositories.database import get_db_connection
    conn, dialect = get_db_connection()
    cursor = conn.cursor()
    try:
        # Search audit events for user's email in the message or payload
        # Simple heuristic since audit_events stores natural language messages
        search_term = f"%{user['email']}%"
        if dialect == "postgres":
            cursor.execute("SELECT incident_id, timestamp, event_type, message FROM audit_events WHERE message ILIKE %s OR payload ILIKE %s ORDER BY timestamp DESC", (search_term, search_term))
        else:
            cursor.execute("SELECT incident_id, timestamp, event_type, message FROM audit_events WHERE message LIKE ? OR payload LIKE ? ORDER BY timestamp DESC", (search_term, search_term))
        
        events = [dict(row) for row in cursor.fetchall()]
        
        # Deduplicate to just unique incident IDs
        incidents_set = set()
        history = []
        for e in events:
            if e["incident_id"] not in incidents_set:
                incidents_set.add(e["incident_id"])
                history.append({
                    "incident_id": e["incident_id"],
                    "timestamp": e["timestamp"],
                    "event_type": e["event_type"],
                    "last_message": e["message"]
                })
        return {"history": history}
    finally:
        conn.close()


# ── Helper ──────────────────────────────────────────────────────────────────────

def _infer_org_from_email(email: str) -> str:
    domain = email.split("@")[-1].lower() if "@" in email else ""
    if "hospital" in domain or "health" in domain:
        return "hospital"
    if "fire" in domain or "fdny" in domain:
        return "fire_station"
    if "police" in domain or "cop" in domain:
        return "police"
    if "gov" in domain or "nic.in" in domain:
        return "government"
    if "ngo" in domain:
        return "ngo"
    return "civilian"
