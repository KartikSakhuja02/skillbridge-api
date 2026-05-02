from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.auth_utils import require_role
from src.database import get_db
from src.model import User, Session as SessionModel, BatchStudent, Attendance
from src.schemas import AttendanceMarkRequest, AttendanceResponse

router = APIRouter(prefix="/attendance", tags=["attendance"])

@router.post("/mark", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED)
def mark_attendance(
    req:          AttendanceMarkRequest,
    current_user: dict    = Depends(require_role("student")),
    db:           Session = Depends(get_db),
):
    session = db.query(SessionModel).filter(SessionModel.id == req.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    enrollment = db.query(BatchStudent).filter(
        BatchStudent.batch_id  == session.batch_id,
        BatchStudent.student_id == current_user["user_id"],
    ).first()
    if not enrollment:
        raise HTTPException(status_code=403, detail="You are not enrolled in this batch")

    existing = db.query(Attendance).filter(
        Attendance.session_id == req.session_id,
        Attendance.student_id == current_user["user_id"],
    ).first()
    if existing:
        existing.status = req.status
        db.commit()
        db.refresh(existing)
        return existing

    attendance = Attendance(
        session_id = req.session_id,
        student_id = current_user["user_id"],
        status     = req.status,
    )
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return attendance