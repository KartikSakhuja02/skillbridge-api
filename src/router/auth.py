from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from src.database import get_db
from src.model import User
from src.schemas import SignupRequest, LoginRequest, TokenResponse
from src.auth_utils import (
    hash_password, verify_password,
    create_access_token, create_monitoring_token,
    get_current_user, MONITORING_API_KEY, _role_str
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse)
def signup(body: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=422, detail="Email already registered")

    user = User(
        name            = body.name,
        email           = body.email,
        hashed_password = hash_password(body.password),
        role            = body.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"user_id": user.id, "role": user.role.value})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"user_id": user.id, "role": user.role.value})
    return {"access_token": token, "token_type": "bearer"}


class MonitoringTokenRequest(BaseModel):
    key: str


@router.post("/monitoring-token", response_model=TokenResponse)
def get_monitoring_token(
    body:         MonitoringTokenRequest,
    current_user: dict    = Depends(get_current_user),
    db:           Session = Depends(get_db)
):
    # _role_str handles both "monitoring_officer" string and UserRole enum
    role = _role_str(current_user.get("role", ""))

    if role != "monitoring_officer":
        raise HTTPException(
            status_code=403,
            detail=f"Only monitoring officers can get a monitoring token. Your role: '{role}'"
        )

    if body.key != MONITORING_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    token = create_monitoring_token(user_id=current_user["user_id"])
    return {"access_token": token, "token_type": "bearer"}