from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import Date, DateTime, Enum as SAEnum, ForeignKey, String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class UserRole(str, Enum):
	institution = "institution"
	trainer = "trainer"
	student = "student"
	programme_manager = "programme_manager"
	monitoring_officer = "monitoring_officer"


class AttendanceStatus(str, Enum):
	present = "present"
	absent = "absent"
	late = "late"


class User(Base):
	__tablename__ = "users"

	id: Mapped[int] = mapped_column(primary_key=True, index=True)
	name: Mapped[str] = mapped_column(String(255), nullable=False)
	email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
	hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
	role: Mapped[UserRole] = mapped_column(SAEnum(UserRole, name="user_role"), nullable=False)
	institution_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class Batch(Base):
	__tablename__ = "batches"

	id: Mapped[int] = mapped_column(primary_key=True, index=True)
	name: Mapped[str] = mapped_column(String(255), nullable=False)
	institution_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class BatchTrainer(Base):
	__tablename__ = "batch_trainers"
	__table_args__ = (UniqueConstraint("batch_id", "trainer_id", name="uq_batch_trainer"),)

	id: Mapped[int] = mapped_column(primary_key=True, index=True)
	batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"), nullable=False, index=True)
	trainer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)


class BatchStudent(Base):
	__tablename__ = "batch_students"
	__table_args__ = (UniqueConstraint("batch_id", "student_id", name="uq_batch_student"),)

	id: Mapped[int] = mapped_column(primary_key=True, index=True)
	batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"), nullable=False, index=True)
	student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)


class BatchInvite(Base):
	__tablename__ = "batch_invites"

	id: Mapped[int] = mapped_column(primary_key=True, index=True)
	batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"), nullable=False, index=True)
	email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
	token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
	status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
	expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Session(Base):
	__tablename__ = "sessions"

	id: Mapped[int] = mapped_column(primary_key=True, index=True)
	batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"), nullable=False, index=True)
	trainer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
	title: Mapped[str] = mapped_column(String(255), nullable=False)
	date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
	start_time: Mapped[datetime.time] = mapped_column(Time, nullable=False)
	end_time: Mapped[datetime.time] = mapped_column(Time, nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class Attendance(Base):
	__tablename__ = "attendance"
	__table_args__ = (UniqueConstraint("session_id", "student_id", name="uq_session_student_attendance"),)

	id: Mapped[int] = mapped_column(primary_key=True, index=True)
	session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), nullable=False, index=True)
	student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
	status: Mapped[AttendanceStatus] = mapped_column(
		SAEnum(AttendanceStatus, name="attendance_status"), nullable=False
	)
	marked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
