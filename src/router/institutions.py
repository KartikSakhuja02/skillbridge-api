from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.auth_utils import require_role
from src.database import get_db
from src.model import User, Batch, BatchTrainer, BatchStudent
from src.schemas import InstitutionSummaryResponse

router = APIRouter(prefix="/institutions", tags=["institutions"])

@router.get("/{institution_id}/summary", response_model=InstitutionSummaryResponse)
def get_institution_summary(
    institution_id: int,
    current_user:   dict    = Depends(require_role("programme_manager", "monitoring_officer")),
    db:             Session = Depends(get_db),
):
    institution = db.query(User).filter(
        User.id   == institution_id,
        User.role == "institution",
    ).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")

    batch_count   = db.query(Batch).filter(Batch.institution_id == institution_id).count()
    trainer_count = db.query(User).filter(
        User.institution_id == institution_id,
        User.role == "trainer"
    ).count()
    student_count = db.query(BatchStudent).join(
        Batch, BatchStudent.batch_id == Batch.id
    ).filter(Batch.institution_id == institution_id).count()

    return InstitutionSummaryResponse(
        institution_id   = institution.id,
        institution_name = institution.name,
        batch_count      = batch_count,
        trainer_count    = trainer_count,
        student_count    = student_count,
    )