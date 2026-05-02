# SkillBridge API

Hey, welcome to the team! This is the SkillBridge API, a FastAPI backend for managing attendance in a fictional state-level skilling programme. It handles 5 user roles: student, trainer, institution, programme_manager, and monitoring_officer. Built with FastAPI, PostgreSQL on Neon, and deployed on Render.

## 1. Live API

**Base URL:** https://skillbridge-api-lu20.onrender.com  
**Docs URL:** https://skillbridge-api-lu20.onrender.com/docs  

Note: Render free tier sleeps after inactivity — first request takes 30-60 seconds.

## 2. Local Setup from Scratch

Assuming you only have Python and pip installed:

```bash
# Clone the repo
git clone https://github.com/KartikSakhuja02/skillbridge-api.git
cd skillbridge-api

# Create and activate virtualenv
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy .env.example to .env and fill in DATABASE_URL and SECRET_KEY
cp .env.example .env
# Generate SECRET_KEY with: python -c "import secrets; print(secrets.token_hex(32))"

# Start server
uvicorn src.main:app --reload  # Must set PYTHONPATH=. on Windows

# Seed database (separate terminal)
python src/seed.py

# Run tests
python -m pytest tests/ -v
```

## 3. Test Accounts

All passwords: `password123`

- Institution: alpha@inst.com, beta@inst.com
- Trainer: trainer1@sb.com, trainer2@sb.com, trainer3@sb.com, trainer4@sb.com
- Student: student1@sb.com through student15@sb.com
- Programme Manager: pm@sb.com
- Monitoring Officer: monitor@sb.com

## 4. Sample curl Commands

All commands use curl.exe syntax for Windows PowerShell. Replace `<token>` with actual JWT.

### POST /auth/signup
```powershell
curl.exe -X POST https://skillbridge-api-lu20.onrender.com/auth/signup `
  -H "Content-Type: application/json" `
  -d '{"name": "New User", "email": "new@test.com", "password": "pass123", "role": "student"}'
```

### POST /auth/login
```powershell
curl.exe -X POST https://skillbridge-api-lu20.onrender.com/auth/login `
  -H "Content-Type: application/json" `
  -d '{"email": "trainer1@sb.com", "password": "password123"}'
```

### POST /auth/monitoring-token
```powershell
curl.exe -X POST https://skillbridge-api-lu20.onrender.com/auth/monitoring-token `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer <standard_token>" `
  -d '{"key": "skillbridge-monitoring-secret-key-2024"}'
```

### POST /batches/
```powershell
curl.exe -X POST https://skillbridge-api-lu20.onrender.com/batches/ `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer <token>" `
  -d '{"name": "New Batch"}'
```

### POST /batches/{id}/invite
```powershell
curl.exe -X POST https://skillbridge-api-lu20.onrender.com/batches/1/invite `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer <token>" `
  -d '{"email": "student1@sb.com"}'
```

### POST /batches/join
```powershell
curl.exe -X POST https://skillbridge-api-lu20.onrender.com/batches/join `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer <token>" `
  -d '{"token": "<invite_token>"}'
```

### POST /sessions/
```powershell
curl.exe -X POST https://skillbridge-api-lu20.onrender.com/sessions/ `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer <token>" `
  -d '{"batch_id": 1, "title": "Intro to Python", "date": "2024-06-01", "start_time": "09:00:00", "end_time": "11:00:00"}'
```

### POST /attendance/mark
```powershell
curl.exe -X POST https://skillbridge-api-lu20.onrender.com/attendance/mark `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer <token>" `
  -d '{"session_id": 1, "student_id": 1, "status": "present"}'
```

### GET /sessions/{id}/attendance
```powershell
curl.exe -X GET https://skillbridge-api-lu20.onrender.com/sessions/1/attendance `
  -H "Authorization: Bearer <token>"
```

### GET /batches/{id}/summary
```powershell
curl.exe -X GET https://skillbridge-api-lu20.onrender.com/batches/1/summary `
  -H "Authorization: Bearer <token>"
```

### GET /institutions/{id}/summary
```powershell
curl.exe -X GET https://skillbridge-api-lu20.onrender.com/institutions/1/summary `
  -H "Authorization: Bearer <token>"
```

### GET /programme/summary
```powershell
curl.exe -X GET https://skillbridge-api-lu20.onrender.com/programme/summary `
  -H "Authorization: Bearer <token>"
```

### GET /monitoring/attendance

**Full 3-step flow for Monitoring Officer:**

**Step 1: Login to get standard token**
```powershell
curl.exe -X POST https://skillbridge-api-lu20.onrender.com/auth/login `
  -H "Content-Type: application/json" `
  -d '{"email": "monitor@sb.com", "password": "password123"}'
```

**Step 2: Exchange for scoped monitoring token**
```powershell
curl.exe -X POST https://skillbridge-api-lu20.onrender.com/auth/monitoring-token `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer <standard_token>" `
  -d '{"key": "skillbridge-monitoring-secret-key-2024"}'
```

**Step 3: Use scoped token on monitoring endpoint**
```powershell
curl.exe -X GET https://skillbridge-api-lu20.onrender.com/monitoring/attendance `
  -H "Authorization: Bearer <scoped_token>"
```

## 5. Schema Decisions

### batch_trainers
Many-to-many join table between batches and trainers. A batch can have multiple trainers and a trainer can belong to multiple batches. Uses a unique constraint on (batch_id, trainer_id) to prevent duplicates. Reflects real-world co-trainer arrangements.

### batch_invites
Trainers generate a cryptographically random token via `secrets.token_urlsafe(32)`. Token is single-use (marked "used" after consumption) with an expiry timestamp. Prevents unauthorised enrollment — students need the token to join, not just the batch ID.

### Dual-token for Monitoring Officer
Standard 24-hour JWT on login like all other roles. To access /monitoring/attendance, they must exchange it for a short-lived 1-hour scoped token by also providing a hardcoded API key. The scoped token has `token_type: "monitoring"` which is checked on every request. Standard tokens are rejected on the monitoring endpoint. Monitoring tokens are rejected everywhere else.

JWT payload structures:

**Standard token (24 hours):**
```json
{
  "user_id": 1,
  "role": "trainer",
  "token_type": "access",
  "iat": 1704067200,
  "exp": 1704153600
}
```

**Monitoring scoped token (1 hour):**
```json
{
  "user_id": 21,
  "role": "monitoring_officer",
  "token_type": "monitoring",
  "iat": 1704067200,
  "exp": 1704070800
}
```

Token revocation in production: store JTI in Redis blocklist on logout, use short expiry + refresh tokens, rotate monitoring API key via environment variable with grace period.

Security issue: static API key with no rate limiting on /auth/monitoring-token. Fix: rate limit to 5 attempts per hour per user_id, hash the API key in the database.

## 6. What is Working / Partial / Skipped

### Fully Working
- All 13 endpoints implemented and tested
- Role-based access control enforced server-side on every endpoint
- JWT auth with correct payload fields
- Dual-token monitoring officer flow end to end
- 7 pytest tests passing (5 required + 2 bonus)
- Seed script: 2 institutions, 4 trainers, 15 students, 3 batches, 8 sessions, 40 attendance records
- Deployed live on Render with Neon PostgreSQL

### Partially Done
- Invite tokens don't validate that only the invited email can use them — any student with the token can join
- batch_invites.used implemented as a status string ("pending"/"used") instead of boolean — functionally equivalent

### Skipped
- Pagination on /monitoring/attendance
- Refresh token flow — tokens can't be refreshed, only re-issued via login

## 7. One Thing I'd Do Differently

Set up Docker from the start. Managing PYTHONPATH, virtual environments, and Python version differences between Windows local and Linux on Render caused the most debugging time. A Dockerfile would eliminate all of that — same environment everywhere, reproducible builds, no "works on my machine" issues.

Deployment notes: Deployed on Render free tier web service. Database on Neon managed PostgreSQL (ap-southeast-1 region). All environment variables in Render dashboard — nothing committed to repo. Python version pinned to 3.11 via .python-version file (SQLAlchemy 2.0 incompatible with Python 3.14 which Render uses by default). bcrypt pinned to 4.0.1 in requirements.txt (bcrypt 5.0.0 broke password verification). PYTHONPATH=. set in Render start command.
  not just the invited email address)
- The `batch_invites.used` field is implemented as a `status` string
  ("pending"/"used") instead of a boolean as specified — functionally equivalent

## What I Skipped

- Pagination on `/monitoring/attendance` (returns all records)
- Refresh token flow (tokens cannot be refreshed, only re-issued via login)

---

## One Thing I'd Do Differently

I would set up the project with Docker from the start. Managing `PYTHONPATH`,
virtual environments, and Python version differences between Windows (local)
and Linux (Render) caused the most debugging time. A `Dockerfile` would
eliminate all of that — same environment everywhere, reproducible builds,
and easier CI/CD.

Now commit and push it:
powershellgit add README.md
git commit -m "Add complete README covering all 5 tasks"
git push origin main
Then verify your live API works with this quick test in PowerShell:
powershellcurl -X POST https://skillbridge-api-lu20.onrender.com/auth/login `
  -H "Content-Type: application/json" `
  -d '{"email": "trainer1@sb.com", "password": "password123"}'
If you get a token back, Task 4 and Task 5 are both done! 🎉

1. Flexible status tracking  
2. Easy aggregation for reports  
3. Async marking support

### 4. Institution as User Role
1. Simplifies multi-tenancy  
2. Trainers can belong to institutions via FK

### 5. Role-Based Access on Every Request
1. Stateless JWT validation  
2. No frontend-based security bypass  
3. Horizontal scalability

---

## Quick Start

```bash
cd submission
pip install -r requirements.txt
python -m src.seed
uvicorn src.main:app --reload
```

API: http://127.0.0.1:8000
Docs: http://127.0.0.1:8000/docs

---

## Summary

Task 1 Status: COMPLETED

1. 7 database entities  
2. 12 API endpoints with RBAC  
3. JWT authentication (24h token)  
4. 23 test users + 40 attendance records  
5. Comprehensive error handling  
6. Production-ready structure

------------------------------------------------------------------------------------


## Task 2: Advanced Authentication & Security

### Overview

Task 2 extends the authentication system with multi-layered security controls beyond standard JWT authentication. The system now differentiates between general access tokens and highly restricted scoped tokens, ensuring strict separation of privileges.

---

## Token Types

1. Standard Access Token (24 hours)
a. Issued On:
    I. POST /auth/signup
    II. POST /auth/login
b. Used for:
    All protected API endpoints
c. Payload Includes:
    I. user_id
    II. role
    III. token_type = "access"
    IV. iat, exp

2. Monitoring Scoped Token (1 hour)
a. Issued via:
    I. POST /auth/monitoring-token
b. Only available to:
    I. *monitoring_office* role
c. Requires:
    I. Valid login token + API Key
d. Payload includes:
    I. user_id
    II. role = "monitoring_officer"
    III. token_type = "monitoring"
e. Used exclusively for:
    I. GET /monitoring/attendance

## Authentication Flow

1. Standard Flow:
a. User logs in via /auth/login
b. Receives 24-hour access token
c. Uses token for all standard endpoints

2. Monitoring Flow (Strictly Controlled):
a. Monitoring officer logs in -> Gets standard token
b. Calls /auth/monitoring-token with:
    I. Bearer token (step 1)
    II. API key (from .env)
c. Receives 1-hour scoped monitoring token
d. Uses this token ONLY for:
    I. /monitoring/attendance

## Security Layers Implemented

1. Token Type Enforcement:
a. Every request validates:
    I. token_type
b. Prevents:
    I. Monitoring tokens being used on normal endpoints
2. Role-Based Access Control (RBAC)
a. Enforced using:
    I. Depends(require_role(...))
b. Applied to:
    I. Every protected endpoint
3. API Key Protection:
a. Required for:
    I. /auth/monitoring-token
b. Stored in:
    I. .env
c. Prevents unauthorized token generation even if JWT is compromised.
4. Short-Lived Priviledged Access:
a. Monitoring token expires in 1 hour.
b. Reduced risk of:
    I. Token leakage
    II. Long-term misuse

### Endpoint Restrictions

Endpoint   	            |           Token Required        |     Notes
----------------------------------------------------------------------------------------
/monitoring/attendance	|       Monitoring token ONLY     | 	Read-only access
----------------------------------------------------------------------------------------
All other endpoints     |	Standard token ONLY           | 	Monitoring token rejected
----------------------------------------------------------------------------------------

### Misuse Prevention

| Scenario                               | Result             |
| -------------------------------------- | ------------------ |
| Using monitoring token on normal API   | `401 Unauthorized` |
| Using standard token on monitoring API | `401 Unauthorized` |
| Wrong role requesting monitoring token | `403 Forbidden`    |
| Invalid API key                        | `401 Unauthorized` |

### Design Rationale
1. Separation of Concerns: Monitoring access is isolated from operational API usage
2. Defense in Depth: JWT + API key + role + token_type validation
3. Principle of Least Privilege: Monitoring officers receive minimal, time-bound access
4. Production-Grade Security Pattern: Scoped tokens simulate real-world systems like AWS STS or OAuth scopes

---

## JWT Payload Structures

### Standard Access Token (24 hours)

1. Issued by: `POST /auth/signup`, `POST /auth/login`  
2. Used by: All protected endpoints (except `/monitoring/attendance`)  
3. Expiry: 24 hours

```json
{
  "user_id": 2,
  "role": "trainer",
  "token_type": "access",
  "iat": 1714554300,
  "exp": 1714640700
}
```

| Field | Type | Purpose |
|-------|------|---------|
| `user_id` | Integer | Database user ID for record lookup |
| `role` | String | User role for RBAC checks (trainer, student, institution, etc.) |
| `token_type` | String | Distinguishes from monitoring tokens; must be `"access"` |
| `iat` | Unix timestamp | Issued-at time (prevents pre-dated tokens) |
| `exp` | Unix timestamp | Expiration (24 hours from issue) |

**Example Validation in Endpoint:**
```python
# Reject if token_type is monitoring
if payload.get("token_type") == "monitoring":
    raise HTTPException(status_code=401, detail="Cannot use monitoring token here")

# Allow standard access
return payload
```

---

### Monitoring Scoped Token (1 hour)

1. Issued by: `POST /auth/monitoring-token` (requires standard token + API key)  
2. Used by: `GET /monitoring/attendance` only  
3. Expiry: 1 hour  
4. Availability: Monitoring Officer role only

```json
{
  "user_id": 21,
  "role": "monitoring_officer",
  "token_type": "monitoring",
  "iat": 1714554300,
  "exp": 1714557900
}
```

| Field | Type | Purpose |
|-------|------|---------|
| `user_id` | Integer | Monitoring officer's user ID |
| `role` | String | Must be `"monitoring_officer"` for endpoint validation |
| `token_type` | String | Scoped flag; must be `"monitoring"` to access `/monitoring/attendance` |
| `iat` | Unix timestamp | Issued-at time |
| `exp` | Unix timestamp | Expiration (1 hour from issue) |

**Example Validation in GET /monitoring/attendance:**
```python
# Reject if not monitoring token type
if payload.get("token_type") != "monitoring":
    raise HTTPException(
        status_code=401,
        detail="This endpoint requires a monitoring scoped token"
    )

# Reject if wrong role
if payload.get("role") != "monitoring_officer":
    raise HTTPException(status_code=401, detail="Monitoring token for wrong role")

# Allow access
return monitoring_data
```

---

## Token Rotation & Revocation Strategy

### Current Implementation (Development Only)
1. Tokens are **stateless** — no database lookup on every request
2. Once issued, valid until expiration
3. No revocation mechanism

### Production-Grade Implementation

#### 1. Token Revocation List (TRL)
```python
# Add to database
class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"
    id: Mapped[int] = mapped_column(primary_key=True)
    jti: Mapped[str] = mapped_column(String(255), unique=True)  # JWT ID
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone.utc))
    reason: Mapped[str] = mapped_column(String(255))  # e.g., "logout", "password_reset"

# On logout, add JWT to blacklist
POST /auth/logout → adds token.jti to blacklist

# On token validation, check blacklist
def decode_token(token: str):
    payload = jwt.decode(token, SECRET_KEY)
    if is_revoked(payload["jti"]):
        raise HTTPException(401, "Token has been revoked")
    return payload
```

#### 2. Automatic Token Rotation
```python
# Issue refresh token alongside access token
POST /auth/login → returns {
    "access_token": "short_lived_24h",
    "refresh_token": "long_lived_7d",
    "token_type": "bearer"
}

# Client calls periodically
POST /auth/refresh → returns new access_token
# Old access_token added to blacklist automatically
```

#### 3. Password Reset Invalidation
```python
# On password change, revoke all user's tokens
POST /auth/change-password → 
  1. Updates password hash
  2. Revokes all tokens where user_id = X
  3. Forces re-login

def revoke_user_tokens(user_id: int):
    db.query(TokenBlacklist).filter(
        TokenBlacklist.user_id == user_id
    ).update({"revoked_at": datetime.now(timezone.utc)})
    db.commit()
```

#### 4. Key Rotation Strategy
```python
# Store multiple signing keys
CURRENT_KEY = os.getenv("JWT_SIGNING_KEY_V2")
PREVIOUS_KEY = os.getenv("JWT_SIGNING_KEY_V1")

# Accept tokens signed with either key
def decode_token(token: str):
    for key in [CURRENT_KEY, PREVIOUS_KEY]:
        try:
            return jwt.decode(token, key, algorithms=[ALGORITHM])
        except jwt.InvalidTokenError:
            continue
    raise HTTPException(401, "Invalid token")

# During key rotation:
# 1. Set CURRENT_KEY to V2
# 2. Keep PREVIOUS_KEY as V1
# 3. All new tokens signed with V2
# 4. Old tokens (V1) still accepted for 24 hours
# 5. After grace period, remove V1
```

---

## Security Issues & Proposed Fixes

### Issue #1: No Token Revocation (High Priority)

**Problem:**
1. Tokens are stateless; once issued, they're valid until expiration
2. If a token is leaked or a user logs out, the token **cannot be invalidated**
3. An attacker with a stolen token can use it for 24 hours

**Current Impact:**
1. Logout is meaningless — user token still works after logout
2. Password reset doesn't force re-login
3. No way to invalidate tokens on account compromise

**Proposed Fix (Production Ready):**
1. Add `token_jti` (JWT ID) to every token payload:
```python
payload = {
    "user_id": user.id,
    "role": user.role.value,
    "jti": secrets.token_urlsafe(32),  # Unique token ID
    "token_type": "access"
}
```

2. Create `token_blacklist` table to store revoked JTIs:
```python
class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"
    jti: Mapped[str] = mapped_column(String(255), unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone.utc))
```

3. On every request, check if JTI is blacklisted:
```python
def decode_token(token: str) -> dict:
    payload = jwt.decode(token, SECRET_KEY)
    if is_token_revoked(payload["jti"]):
        raise HTTPException(401, "Token has been revoked")
    return payload
```

4. Implement logout endpoint:
```python
@router.post("/logout")
def logout(current_user: dict = Depends(get_current_user)):
    revoke_token(current_user["jti"])
    return {"message": "Logged out successfully"}
```

**Trade-off:** Requires database lookup on every request (slight latency), but gains revocation capability.

**Alternative (Lower Impact):** Use Redis cache for blacklist instead of database:
```python
# Fast in-memory lookup
redis_client.set(f"blacklist:{jti}", "revoked", ex=86400)  # 24h TTL
```

---

### Issue #2: Hardcoded API Key (Medium Priority)

**Problem:**
- `MONITORING_API_KEY` is stored in `.env` file
- If `.env` is committed to git (even in history), key is permanently leaked
- No way to rotate the key without redeployment

**Current Impact:**
- Anyone with access to git history can generate monitoring tokens
- Cannot quickly revoke compromised key

**Proposed Fix:**
1. Move to **AWS Secrets Manager** or **HashiCorp Vault**:
```python
import boto3

def get_monitoring_api_key():
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='skillbridge/monitoring-api-key')
    return response['SecretString']

MONITORING_API_KEY = get_monitoring_api_key()
```

2. Implement key rotation without redeployment:
```python
# Create new key in Secrets Manager
@router.post("/admin/rotate-monitoring-key")  # Admin endpoint
def rotate_monitoring_key(current_user: dict = Depends(require_role("admin"))):
    old_key = get_monitoring_api_key()
    new_key = secrets.token_urlsafe(32)
    update_secret("skillbridge/monitoring-api-key", new_key)
    log_rotation_event(old_key, new_key)
    return {"message": "Key rotated. Old key valid for 24h for backward compatibility"}
```

**Trade-off:** Adds AWS/Vault dependency, but enables secure key management.

---

### Issue #3: No Request Rate Limiting (Medium Priority)

**Problem:**
1. No protection against brute-force attacks on `/auth/login`
2. Attacker can try unlimited passwords without throttling
3. `/auth/monitoring-token` can be called unlimited times (but requires valid JWT)

**Proposed Fix:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/login")
@limiter.limit("5/minute")  # 5 attempts per minute per IP
def login(body: LoginRequest, db: Session = Depends(get_db)):
    # ... existing login logic
```

---

### Issue #4: No Audit Logging (Low Priority in MVP, High in Production)

**Problem:**
1. No record of who accessed what and when
2. No way to investigate suspicious activity
3. Compliance/regulatory issues (GDPR, audit trails)

**Proposed Fix:**
```python
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    endpoint: Mapped[str] = mapped_column(String(255))
    method: Mapped[str] = mapped_column(String(10))  # GET, POST, etc.
    status_code: Mapped[int] = mapped_column(Integer)
    ip_address: Mapped[str] = mapped_column(String(45))  # IPv6-safe
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone.utc))

@app.middleware("http")
async def audit_middleware(request, call_next):
    response = await call_next(request)
    log_audit_event(
        user_id=request.state.user_id,
        endpoint=request.url.path,
        method=request.method,
        status_code=response.status_code,
        ip_address=request.client.host
    )
    return response
```

---

## Summary

Task 2 Status: COMPLETED

1. Dual-token authentication system  
2. Scoped JWT with explicit token_type  
3. API key-protected privileged access  
4. Strict endpoint-level enforcement  
5. Short-lived high-privilege tokens  
6. JWT payload structures documented  
7. Token rotation/revocation strategy documented  
8. Security vulnerabilities identified + fixes proposed

