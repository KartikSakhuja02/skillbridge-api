from datetime import date, datetime, time
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    student = "student"
    trainer = "trainer"
    institution = "institution"
    programme_manager = "programme_manager"
    monitoring_officer = "monitoring_officer"


class AttendanceStatus(str, Enum):
    present = "present"
    absent = "absent"
    late = "late"


# ============ Auth Schemas ============
class SignupRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    institution_id: int | None = None
    created_at: datetime | None = None

    class Config:
        orm_mode = True


# ============ Batch Schemas ============
class BatchCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class BatchResponse(BaseModel):
    id: int
    name: str
    institution_id: int
    created_at: datetime | None = None

    class Config:
        orm_mode = True


class TrainerInfo(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        orm_mode = True


class StudentInfo(BaseModel):
    id: int
    name: str
    email: str

    class Config:
        orm_mode = True


class BatchSummaryResponse(BaseModel):
    batch: BatchResponse
    trainers: list[TrainerInfo]
    students: list[StudentInfo]
    session_count: int


# ============ Batch Invite Schemas ============
class InviteCreateRequest(BaseModel):
    email: str = Field(..., min_length=1, max_length=255)


class InviteResponse(BaseModel):
    token: str
    expires_at: datetime | None = None


class JoinBatchRequest(BaseModel):
    token: str = Field(..., min_length=1)


# ============ Session Schemas ============
class SessionCreateRequest(BaseModel):
    batch_id: int
    title: str = Field(..., min_length=1, max_length=255)
    date: date
    start_time: time
    end_time: time


class SessionResponse(BaseModel):
    id: int
    batch_id: int
    trainer_id: int
    title: str
    date: date
    start_time: time
    end_time: time
    created_at: datetime | None = None

    class Config:
        orm_mode = True


# ============ Attendance Schemas ============
class AttendanceMarkRequest(BaseModel):
    session_id: int
    student_id: int
    status: AttendanceStatus


class AttendanceResponse(BaseModel):
    id: int
    session_id: int
    student_id: int
    status: AttendanceStatus
    marked_at: datetime

    class Config:
        orm_mode = True


class SessionAttendanceDetail(BaseModel):
    student_id: int
    student_name: str
    status: AttendanceStatus
    marked_at: datetime


class SessionAttendanceResponse(BaseModel):
    session_id: int
    session_title: str
    batch_id: int
    date: date
    start_time: time
    end_time: time
    attendance: list[SessionAttendanceDetail]


# ============ Summary Schemas ============
class InstitutionSummaryResponse(BaseModel):
    institution_id: int
    institution_name: str
    batch_count: int
    trainer_count: int
    student_count: int


class ProgrammeSummaryResponse(BaseModel):
    total_institutions: int
    total_batches: int
    total_trainers: int
    total_students: int
    total_sessions: int
