from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.auth_utils import require_role
from src.database import get_db
from src.model import User, Batch, Session as SessionModel
from src.schemas import ProgrammeSummaryResponse

router = APIRouter(prefix="/programme", tags=["programme"])

@router.get("/summary", response_model=ProgrammeSummaryResponse)
def get_programme_summary(
    current_user: dict    = Depends(require_role("programme_manager", "monitoring_officer")),
    db:           Session = Depends(get_db),
):
    return ProgrammeSummaryResponse(
        total_institutions = db.query(User).filter(User.role == "institution").count(),
        total_batches      = db.query(Batch).count(),
        total_trainers     = db.query(User).filter(User.role == "trainer").count(),
        total_students     = db.query(User).filter(User.role == "student").count(),
        total_sessions     = db.query(SessionModel).count(),
    )