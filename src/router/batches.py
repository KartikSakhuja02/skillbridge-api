import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.auth_utils import require_role
from src.database import get_db
from src.model import User, Batch, BatchTrainer, BatchStudent, BatchInvite, Session as SessionModel
from src.schemas import (
    BatchCreateRequest, BatchResponse, BatchSummaryResponse,
    InviteCreateRequest, InviteResponse, JoinBatchRequest,
    TrainerInfo, StudentInfo,
)

router = APIRouter(prefix="/batches", tags=["batches"])

@router.post("/", response_model=BatchResponse, status_code=status.HTTP_201_CREATED)
def create_batch(
    req:          BatchCreateRequest,
    current_user: dict    = Depends(require_role("institution", "trainer")),
    db:           Session = Depends(get_db),
):
    batch = Batch(name=req.name, institution_id=current_user["user_id"])
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch

@router.get("/{batch_id}/summary", response_model=BatchSummaryResponse)
def get_batch_summary(
    batch_id:     int,
    current_user: dict    = Depends(require_role("institution", "programme_manager", "trainer")),
    db:           Session = Depends(get_db),
):
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    trainers = db.query(User).join(
        BatchTrainer, BatchTrainer.trainer_id == User.id
    ).filter(BatchTrainer.batch_id == batch_id).all()

    students = db.query(User).join(
        BatchStudent, BatchStudent.student_id == User.id
    ).filter(BatchStudent.batch_id == batch_id).all()

    session_count = db.query(SessionModel).filter(SessionModel.batch_id == batch_id).count()

    return BatchSummaryResponse(
        batch         = batch,
        trainers      = [TrainerInfo.from_orm(t) for t in trainers],
        students      = [StudentInfo.from_orm(s) for s in students],
        session_count = session_count,
    )

@router.post("/{batch_id}/invite", response_model=InviteResponse)
def invite_to_batch(
    batch_id:     int,
    req:          InviteCreateRequest,
    current_user: dict    = Depends(require_role("trainer", "institution")),
    db:           Session = Depends(get_db),
):
    batch = db.query(Batch).filter(Batch.id == batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    token  = secrets.token_urlsafe(32)
    invite = BatchInvite(batch_id=batch_id, email=req.email, token=token, status="pending")
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return InviteResponse(token=token, expires_at=invite.expires_at)

@router.post("/join", status_code=status.HTTP_200_OK)
def join_batch(
    req:          JoinBatchRequest,
    current_user: dict    = Depends(require_role("student")),
    db:           Session = Depends(get_db),
):
    invite = db.query(BatchInvite).filter(
        BatchInvite.token  == req.token,
        BatchInvite.status == "pending",
    ).first()
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid or expired invite token")

    existing = db.query(BatchStudent).filter(
        BatchStudent.batch_id   == invite.batch_id,
        BatchStudent.student_id == current_user["user_id"],
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already enrolled in this batch")

    db.add(BatchStudent(batch_id=invite.batch_id, student_id=current_user["user_id"]))
    invite.status = "used"
    db.commit()
    return {"message": "Successfully joined batch", "batch_id": invite.batch_id}