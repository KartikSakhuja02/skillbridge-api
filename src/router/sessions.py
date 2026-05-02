from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.auth_utils import require_role
from src.database import get_db
from src.model import User, Batch, Session as SessionModel, Attendance
from src.schemas import SessionCreateRequest, SessionResponse, SessionAttendanceResponse, SessionAttendanceDetail

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    req:          SessionCreateRequest,
    current_user: dict    = Depends(require_role("trainer")),
    db:           Session = Depends(get_db),
):
    batch = db.query(Batch).filter(Batch.id == req.batch_id).first()
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    session = SessionModel(
        batch_id   = req.batch_id,
        trainer_id = current_user["user_id"],
        title      = req.title,
        date       = req.date,
        start_time = req.start_time,
        end_time   = req.end_time,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

@router.get("/{session_id}/attendance", response_model=SessionAttendanceResponse)
def get_session_attendance(
    session_id:   int,
    current_user: dict    = Depends(require_role("trainer")),
    db:           Session = Depends(get_db),
):
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    records = db.query(Attendance).filter(Attendance.session_id == session_id).all()
    details = []
    for r in records:
        student = db.query(User).filter(User.id == r.student_id).first()
        if student:
            details.append(SessionAttendanceDetail(
                student_id   = student.id,
                student_name = student.name,
                status       = r.status,
                marked_at    = r.marked_at,
            ))

    return SessionAttendanceResponse(
        session_id    = session.id,
        session_title = session.title,
        batch_id      = session.batch_id,
        date          = session.date,
        start_time    = session.start_time,
        end_time      = session.end_time,
        attendance    = details,
    )