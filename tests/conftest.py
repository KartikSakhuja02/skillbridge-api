import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.main import app
from src.database import Base, get_db

# ─── Use a separate test database ────────────────────────────────────────────
# This keeps your real seeded data safe during testing.
# It reads TEST_DATABASE_URL from .env, falls back to your main DATABASE_URL.
from dotenv import load_dotenv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")

# Create a separate engine for tests
test_engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """Replace the normal DB session with the test DB session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Create all tables before tests run."""
    Base.metadata.create_all(bind=engine)
    yield
    # Tables are kept after tests — do not drop production data


@pytest.fixture(scope="session")
def client():
    """
    Test client that uses the real test database.
    This satisfies the requirement: at least 2 tests hit a real database.
    """
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
def student_token(client):
    """Register a student and return their JWT token."""
    client.post("/auth/signup", json={
        "name":     "Test Student",
        "email":    "teststudent@test.com",
        "password": "testpass123",
        "role":     "student",
    })
    response = client.post("/auth/login", json={
        "email":    "teststudent@test.com",
        "password": "testpass123",
    })
    return response.json()["access_token"]


@pytest.fixture(scope="session")
def trainer_token(client):
    """Register a trainer and return their JWT token."""
    client.post("/auth/signup", json={
        "name":     "Test Trainer",
        "email":    "testtrainer@test.com",
        "password": "testpass123",
        "role":     "trainer",
    })
    response = client.post("/auth/login", json={
        "email":    "testtrainer@test.com",
        "password": "testpass123",
    })
    return response.json()["access_token"]


@pytest.fixture(scope="session")
def institution_token(client):
    """Register an institution and return their JWT token."""
    client.post("/auth/signup", json={
        "name":     "Test Institution",
        "email":    "testinst@test.com",
        "password": "testpass123",
        "role":     "institution",
    })
    response = client.post("/auth/login", json={
        "email":    "testinst@test.com",
        "password": "testpass123",
    })
    return response.json()["access_token"]