# SkillBridge API — Attendance Management System

## Task 1: Data Model & Core API

### Overview

SkillBridge is a REST API backend for an attendance management system supporting a government skilling programme. The system enforces role-based access control (RBAC) across five user types:

1. Student: Join batches, view own attendance
2. Trainer: Create sessions, mark attendance, manage batches
3. Institution: Create and manage batches, view batch summaries
4. Programme Manager: View institution and programme-wide summaries
5. Monitoring Officer: Read-only access to all attendance data via scoped JWT

#### Key Design Principles
1. Role-based access control (RBAC): Every protected endpoint validates user role from JWT  
2. JWT-based authentication: Stateless, scalable token validation  
3. Relational data modeling: Normalized schema supporting many-to-many relationships  
4. Secure by default: No frontend-based access control; all validation server-side

---

## Data Model

### 1. Users
What it does: Stores all system users across roles with authentication credentials.

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Primary key |
| `name` | String(255) | Full name |
| `email` | String(255) | Unique, indexed |
| `hashed_password` | String(255) | Bcrypt hash |
| `role` | Enum | `student` \| `trainer` \| `institution` \| `programme_manager` \| `monitoring_officer` |
| `institution_id` | Integer (FK, nullable) | References `users.id` for trainers/staff under an institution |
| `created_at` | DateTime | Timestamp (UTC) |

Constraints: `UNIQUE(email)`, `PK(id)`

### 2. Batches
What it does: Represents training batches organized by institutions.

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Primary key |
| `name` | String(255) | Batch name (e.g., "Python Basics") |
| `institution_id` | Integer (FK) | References `users.id` (institution role) |
| `created_at` | DateTime | Timestamp (UTC) |

Constraints: `PK(id)`, `FK(institution_id → users.id)`

### 3. Batch Trainers (Many-to-Many)
What it does: Maps trainers to batches, enabling multiple trainers per batch.

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Primary key |
| `batch_id` | Integer (FK) | References `batches.id` |
| `trainer_id` | Integer (FK) | References `users.id` (trainer role) |

Constraints: `PK(id)`, `UNIQUE(batch_id, trainer_id)`, `FK(batch_id)`, `FK(trainer_id)`

### 4. Batch Students (Many-to-Many)
What it does: Maps students to batches for enrollment tracking.

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Primary key |
| `batch_id` | Integer (FK) | References `batches.id` |
| `student_id` | Integer (FK) | References `users.id` (student role) |

Constraints: `PK(id)`, `UNIQUE(batch_id, student_id)`, `FK(batch_id)`, `FK(student_id)`

### 5. Batch Invites
What it does: Controlled onboarding mechanism for students to join batches via secure tokens.

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Primary key |
| `batch_id` | Integer (FK) | References `batches.id` |
| `email` | String(255) | Invite recipient email |
| `token` | String(255) | Unique, secure invite token |
| `status` | String(50) | `pending` \| `used` |
| `created_at` | DateTime | Timestamp (UTC) |
| `expires_at` | DateTime (nullable) | Optional expiration |

Constraints: `PK(id)`, `UNIQUE(token)`, `FK(batch_id)`, `INDEX(email, token)`

### 6. Sessions
What it does: Represents individual training sessions within a batch.

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Primary key |
| `batch_id` | Integer (FK) | References `batches.id` |
| `trainer_id` | Integer (FK) | References `users.id` (trainer role) |
| `title` | String(255) | Session title (e.g., "Intro to Python") |
| `date` | Date | Session date |
| `start_time` | Time | Session start (e.g., 09:00) |
| `end_time` | Time | Session end (e.g., 11:00) |
| `created_at` | DateTime | Timestamp (UTC) |

Constraints: `PK(id)`, `FK(batch_id)`, `FK(trainer_id)`

### 7. Attendance
What it does: Tracks per-student attendance for each session.

| Field | Type | Description |
|-------|------|-------------|
| `id` | Integer | Primary key |
| `session_id` | Integer (FK) | References `sessions.id` |
| `student_id` | Integer (FK) | References `users.id` (student role) |
| `status` | Enum | `present` \| `absent` \| `late` |
| `marked_at` | DateTime | Timestamp when marked (UTC) |
Constraints: `PK(id)`, `UNIQUE(session_id, student_id)`, `FK(session_id)`, `FK(student_id)`

The database was implemented on Neon PostgreSQL.

---

## API Endpoints

### Authentication

| Method | Path | Description | Auth | Returns |
|--------|------|-------------|------|---------|
| `POST` | `/auth/signup` | Register new user | None | JWT token |
| `POST` | `/auth/login` | Login with credentials | None | JWT token |
| `POST` | `/auth/monitoring-token` | Generate scoped monitoring token (1h) | API key | JWT token (1h expiry) |

#### Request/Response Examples

**POST /auth/signup**
```json
Request:
{
  "name": "Kartik Trainer",
  "email": "kartiktrainer@example.com",
  "password": "kartiktrainer123",
  "role": "trainer"
} //example for signup

Response (201):
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
} //response you get after the signup
```

**POST /auth/login**
```json
Request:
{
  "email": "kartiktrainer@example.com",
  "password": "kartiktrainer123"
} //example for the login of the above sign up

Response (200):
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
} //response you get after logging in
```

### Batch Management

| Method | Path | Allowed Roles | Description |
|--------|------|---------------|-------------|
| `POST` | `/batches` | Trainer, Institution | Create new batch |
| `GET` | `/batches/{id}/summary` | Any authenticated | Get batch summary (trainers, students, session count) |
| `POST` | `/batches/{id}/invite` | Trainer, Institution | Generate invite link for student |
| `POST` | `/batches/join` | Student | Join batch using invite token |

### Session Management

| Method | Path | Allowed Roles | Description |
|--------|------|---------------|-------------|
| `POST` | `/sessions` | Trainer | Create session |
| `GET` | `/sessions/{id}/attendance` | Trainer, Monitoring Officer | Get session attendance list |

### Attendance

| Method | Path | Allowed Roles | Description |
|--------|------|---------------|-------------|
| `POST` | `/attendance/mark` | Trainer | Mark student attendance for session |

### Reports & Summaries

| Method | Path | Allowed Roles | Description |
|--------|------|---------------|-------------|
| `GET` | `/batches/{id}/summary` | Any authenticated | Batch summary |
| `GET` | `/institutions/{id}/summary` | Programme Manager, Monitoring Officer | Institution summary |
| `GET` | `/programme/summary` | Programme Manager, Monitoring Officer | Programme-wide summary |
| `GET` | `/monitoring/attendance` | Monitoring Officer | All attendance records (read-only) |

---

## 🔒 Access Control

### Authentication Flow

1. User calls `POST /auth/login` or `POST /auth/signup` with credentials
2. Server returns JWT containing: `user_id`, `role`, `iat`, `exp`
3. Client includes token in `Authorization: Bearer <token>` header
4. Protected endpoints extract and validate token
5. If token invalid/expired or role not permitted → 401 Unauthorized or 403 Forbidden

### Error Responses

| Status | Scenario |
|--------|----------|
| `400` | Duplicate email, missing required fields |
| `401` | Missing/invalid token |
| `403` | User role not permitted |
| `404` | Resource not found |
| `422` | Validation error |

### Role Permissions

All role-based access is enforced server-side via `Depends(require_role(...))` decorator on every protected endpoint. No frontend-based authorization.

---

## 🌱 Seed Data (Seeding Script)

Command: `python -m src.seed`

### Test Accounts (password: `password123`)

1. Institutions: `alpha@inst.com`, `beta@inst.com`
2. Trainers: `trainer1@sb.com` through `trainer4@sb.com`
3. Students: `student1@sb.com` through `student15@sb.com`
4. Management: `pm@sb.com` (Programme Manager), `monitor@sb.com` (Monitoring Officer)

### Data Created

| Entity | Count |
|--------|-------|
| Users | 23 |
| Institutions | 2 |
| Trainers | 4 |
| Students | 15 |
| Batches | 3 |
| Sessions | 8 |
| Attendance Records | 40 |

---

## Key Design Decisions

### 1. Many-to-Many for Batch Trainers
1. Multiple trainers per batch  
2. Flexible scheduling and load balancing

### 2. Token-Based Batch Joining
1. Secure invite mechanism  
2. Optional expiration support  
3. One-time usage tracking

### 3. Attendance Decoupled from Sessions
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

