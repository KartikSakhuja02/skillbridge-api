"""
pytest test suite for SkillBridge API.
Run with: pytest tests/ -v
At least 2 tests hit a real (test) database as required.
"""
import pytest
import jwt
import os


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 1 — Successful student signup and login, asserting a valid JWT is returned
# Hits real database ✓
# ═══════════════════════════════════════════════════════════════════════════════

def test_student_signup_and_login(client):
    """
    Sign up a new student, log in, and assert the response
    contains a valid JWT with correct payload fields.
    """
    # Signup
    signup_resp = client.post("/auth/signup", json={
        "name":     "Jane Student",
        "email":    "jane@test.com",
        "password": "securepass123",
        "role":     "student",
    })
    assert signup_resp.status_code == 200, f"Signup failed: {signup_resp.json()}"
    signup_data = signup_resp.json()
    assert "access_token" in signup_data
    assert signup_data["token_type"] == "bearer"

    # Login
    login_resp = client.post("/auth/login", json={
        "email":    "jane@test.com",
        "password": "securepass123",
    })
    assert login_resp.status_code == 200, f"Login failed: {login_resp.json()}"
    token = login_resp.json()["access_token"]

    # Decode and verify JWT payload (without verifying signature — just check fields)
    decoded = jwt.decode(token, options={"verify_signature": False})
    assert "user_id"    in decoded, "JWT missing user_id"
    assert "role"       in decoded, "JWT missing role"
    assert "exp"        in decoded, "JWT missing exp"
    assert "iat"        in decoded, "JWT missing iat"
    assert "token_type" in decoded, "JWT missing token_type"
    assert decoded["role"]       == "student"
    assert decoded["token_type"] == "access"

    print("\n✓ Test 1 passed: student signup, login, JWT validated")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 2 — Trainer creates a session with all required fields
# Hits real database ✓
# ═══════════════════════════════════════════════════════════════════════════════

def test_trainer_creates_session(client, trainer_token, institution_token):
    """
    Trainer creates a batch (via institution) then creates a session in it.
    Asserts the session is returned with all required fields.
    """
    # Institution creates a batch first
    batch_resp = client.post(
        "/batches/",
        json={"name": "Test Batch for Sessions"},
        headers={"Authorization": f"Bearer {institution_token}"}
    )
    assert batch_resp.status_code == 201, f"Batch creation failed: {batch_resp.json()}"
    batch_id = batch_resp.json()["id"]

    # Trainer creates a session in that batch
    session_resp = client.post(
        "/sessions/",
        json={
            "batch_id":   batch_id,
            "title":      "Introduction to Testing",
            "date":       "2024-06-01",
            "start_time": "09:00:00",
            "end_time":   "11:00:00",
        },
        headers={"Authorization": f"Bearer {trainer_token}"}
    )
    assert session_resp.status_code == 201, f"Session creation failed: {session_resp.json()}"

    data = session_resp.json()
    assert data["title"]    == "Introduction to Testing"
    assert data["batch_id"] == batch_id
    assert "id"             in data
    assert "trainer_id"     in data
    assert "date"           in data
    assert "start_time"     in data
    assert "end_time"       in data

    print("\n✓ Test 2 passed: trainer created session with all required fields")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 3 — Student successfully marks their own attendance
# Hits real database ✓
# ═══════════════════════════════════════════════════════════════════════════════

def test_student_marks_attendance(client, student_token, trainer_token, institution_token):
    """
    Full flow: institution creates batch → trainer creates session →
    student joins batch → student marks attendance.
    """
    # Step 1: institution creates a batch
    batch_resp = client.post(
        "/batches/",
        json={"name": "Attendance Test Batch"},
        headers={"Authorization": f"Bearer {institution_token}"}
    )
    assert batch_resp.status_code == 201
    batch_id = batch_resp.json()["id"]

    # Step 2: trainer creates a session
    session_resp = client.post(
        "/sessions/",
        json={
            "batch_id":   batch_id,
            "title":      "Attendance Test Session",
            "date":       "2024-06-02",
            "start_time": "10:00:00",
            "end_time":   "12:00:00",
        },
        headers={"Authorization": f"Bearer {trainer_token}"}
    )
    assert session_resp.status_code == 201
    session_id = session_resp.json()["id"]

    # Step 3: trainer generates an invite for the batch
    invite_resp = client.post(
        f"/batches/{batch_id}/invite",
        json={"email": "teststudent@test.com"},
        headers={"Authorization": f"Bearer {trainer_token}"}
    )
    assert invite_resp.status_code == 200, f"Invite failed: {invite_resp.json()}"
    token = invite_resp.json()["token"]

    # Step 4: student joins the batch using invite token
    join_resp = client.post(
        "/batches/join",
        json={"token": token},
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert join_resp.status_code == 200, f"Join failed: {join_resp.json()}"

    # Step 5: student marks attendance
    attendance_resp = client.post(
        "/attendance/mark",
        json={
            "session_id": session_id,
            "student_id": 999,        # ignored — router uses current_user["user_id"]
            "status":     "present",
        },
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert attendance_resp.status_code == 201, f"Attendance failed: {attendance_resp.json()}"

    data = attendance_resp.json()
    assert data["status"]     == "present"
    assert data["session_id"] == session_id

    print("\n✓ Test 3 passed: student marked own attendance successfully")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 4 — POST to /monitoring/attendance returns 405
# Does NOT need database ✓
# ═══════════════════════════════════════════════════════════════════════════════

def test_monitoring_post_returns_405(client):
    """
    The /monitoring/attendance endpoint must return 405 for any non-GET request.
    This is enforced regardless of auth status.
    """
    response = client.post("/monitoring/attendance", json={})
    assert response.status_code == 405, (
        f"Expected 405 Method Not Allowed, got {response.status_code}: {response.json()}"
    )
    print("\n✓ Test 4 passed: POST /monitoring/attendance returned 405")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST 5 — Request to protected endpoint with no token returns 401
# Does NOT need database ✓
# ═══════════════════════════════════════════════════════════════════════════════

def test_protected_endpoint_no_token_returns_401(client):
    """
    Any protected endpoint called without a Bearer token must return 401 or 403.
    Tests multiple endpoints to be thorough.
    """
    endpoints = [
        ("GET",  "/sessions/1/attendance"),
        ("POST", "/sessions/"),
        ("POST", "/batches/"),
        ("GET",  "/programme/summary"),
    ]

    for method, path in endpoints:
        if method == "GET":
            resp = client.get(path)
        else:
            resp = client.post(path, json={})

        assert resp.status_code in (401, 403), (
            f"Expected 401 or 403 for {method} {path} with no token, "
            f"got {resp.status_code}: {resp.json()}"
        )

    print("\n✓ Test 5 passed: all protected endpoints return 401/403 with no token")


# ═══════════════════════════════════════════════════════════════════════════════
# BONUS TEST — Wrong role gets 403
# ═══════════════════════════════════════════════════════════════════════════════

def test_wrong_role_returns_403(client, student_token):
    """
    A student trying to create a session (trainer-only) must get 403.
    """
    resp = client.post(
        "/sessions/",
        json={
            "batch_id":   1,
            "title":      "Unauthorized Session",
            "date":       "2024-06-01",
            "start_time": "09:00:00",
            "end_time":   "11:00:00",
        },
        headers={"Authorization": f"Bearer {student_token}"}
    )
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.json()}"
    print("\n✓ Bonus test passed: student got 403 trying trainer endpoint")


# ═══════════════════════════════════════════════════════════════════════════════
# BONUS TEST — Duplicate email signup returns 422
# ═══════════════════════════════════════════════════════════════════════════════

def test_duplicate_email_returns_422(client):
    """
    Signing up with an already-registered email must return 422.
    """
    # First signup
    client.post("/auth/signup", json={
        "name": "First User", "email": "duplicate@test.com",
        "password": "pass123", "role": "student",
    })

    # Second signup with same email
    resp = client.post("/auth/signup", json={
        "name": "Second User", "email": "duplicate@test.com",
        "password": "pass456", "role": "student",
    })
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}"
    print("\n✓ Bonus test passed: duplicate email returned 422")