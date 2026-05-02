from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from src.database import get_db
from src.model import Attendance
from src.auth_utils import get_monitoring_user

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/attendance")
def monitoring_attendance(
    db:   Session = Depends(get_db),
    user: dict    = Depends(get_monitoring_user)
):
    """
    Read-only attendance dump.
    Requires the scoped monitoring token from POST /auth/monitoring-token.
    """
    records = db.query(Attendance).all()
    return [
        {
            "id":         r.id,
            "session_id": r.session_id,
            "student_id": r.student_id,
            "status":     r.status,
            "marked_at":  r.marked_at,
        }
        for r in records
    ]


@router.api_route("/attendance", methods=["POST", "PUT", "DELETE", "PATCH"])
def monitoring_not_allowed(request: Request):
    """Block all non-GET methods with 405."""
    return JSONResponse(
        status_code=405,
        content={"detail": "Method Not Allowed — monitoring endpoint is read-only"}
    )