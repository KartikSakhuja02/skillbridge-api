from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os
from dotenv import load_dotenv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SECRET_KEY                      = os.getenv("SECRET_KEY")
ALGORITHM                       = os.getenv("ALGORITHM", "HS256")
TOKEN_EXPIRE_MINUTES            = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))
MONITORING_API_KEY              = os.getenv("MONITORING_API_KEY")
MONITORING_TOKEN_EXPIRE_MINUTES = int(os.getenv("MONITORING_TOKEN_EXPIRE_MINUTES", 60))

pwd_context   = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()


# ─── Password helpers ─────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ─── Token creation ───────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_minutes: int = TOKEN_EXPIRE_MINUTES) -> str:
    payload = data.copy()
    now     = datetime.now(timezone.utc)
    payload.update({
        "token_type": "access",
        "iat":        now,
        "exp":        now + timedelta(minutes=expires_minutes),
    })
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_monitoring_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "user_id":    user_id,
        "role":       "monitoring_officer",
        "token_type": "monitoring",
        "iat":        now,
        "exp":        now + timedelta(minutes=MONITORING_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ─── Token decoding ───────────────────────────────────────────────────────────

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ─── Helper: normalize role to plain string ───────────────────────────────────

def _role_str(role) -> str:
    """
    Always returns a plain string regardless of whether
    role is already a string or a UserRole enum.
    e.g. UserRole.trainer -> "trainer"
         "trainer"        -> "trainer"
    """
    if hasattr(role, "value"):
        return role.value
    return str(role)


# ─── FastAPI dependencies ─────────────────────────────────────────────────────

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> dict:
    """
    Reads Bearer token, returns decoded JWT payload dict.
    Blocks monitoring scoped tokens from being used on regular endpoints.
    """
    payload = decode_token(credentials.credentials)
    if payload.get("token_type") == "monitoring":
        raise HTTPException(
            status_code=401,
            detail="Monitoring scoped token cannot be used here. Use your standard login token."
        )
    return payload


def get_monitoring_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> dict:
    """
    Only accepts the short-lived monitoring scoped token.
    Used exclusively on GET /monitoring/attendance.
    """
    payload = decode_token(credentials.credentials)
    if payload.get("token_type") != "monitoring":
        raise HTTPException(
            status_code=401,
            detail="This endpoint requires a monitoring scoped token. "
                   "Get one from POST /auth/monitoring-token"
        )
    if payload.get("role") != "monitoring_officer":
        raise HTTPException(
            status_code=401,
            detail="Monitoring token issued for wrong role"
        )
    return payload


def require_role(*allowed_roles):
    """
    Works with both string roles ("trainer") and enum roles (UserRole.trainer).
    Returns the JWT payload dict as current_user.
    Usage: Depends(require_role("trainer", "institution"))
        or Depends(require_role(UserRole.trainer, UserRole.institution))
    """
    # Normalize all allowed roles to plain strings once at definition time
    allowed = {_role_str(r) for r in allowed_roles}

    def checker(current_user: dict = Depends(get_current_user)):
        role = _role_str(current_user.get("role", ""))
        if role not in allowed:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required role(s): {', '.join(sorted(allowed))}"
            )
        return current_user   # returns dict, not User object

    return checker