"""
Run with: python -m src.seed
Creates 2 institutions, 4 trainers, 15 students, 3 batches, 8 sessions, attendance records.
"""
import sys
print("Script started...", flush=True)

try:
    from src.database import SessionLocal, engine, Base
    from src.models import (
        User, UserRole, Batch, BatchTrainer, BatchStudent,
        BatchInvite, Session as SessionModel, Attendance, AttendanceStatus
    )
    from src.auth_utils import hash_password
    print("Imports successful!", flush=True)
except Exception as e:
    print(f"IMPORT ERROR: {e}", flush=True)
    sys.exit(1)

from datetime import date, time, datetime, timedelta, timezone
import secrets, random

def run():
    print("Seeding database...", flush=True)

    try:
        Base.metadata.create_all(bind=engine)
        print("Tables created/verified.", flush=True)
    except Exception as e:
        print(f"ERROR creating tables: {e}", flush=True)
        sys.exit(1)

    db = SessionLocal()

    try:
        # Check if already seeded
        existing = db.query(User).count()
        if existing > 0:
            print(f"Database already has {existing} users. Skipping seed.", flush=True)
            print("If you want to re-seed, delete all rows first.", flush=True)
            db.close()
            return

        # --- 2 Institutions ---
        print("Creating institutions...", flush=True)
        inst1 = User(name="Alpha Institute", email="alpha@inst.com",
                     hashed_password=hash_password("password123"), role=UserRole.institution)
        inst2 = User(name="Beta Institute", email="beta@inst.com",
                     hashed_password=hash_password("password123"), role=UserRole.institution)
        db.add_all([inst1, inst2])
        db.commit()
        db.refresh(inst1)
        db.refresh(inst2)
        print(f"  inst1.id={inst1.id}, inst2.id={inst2.id}", flush=True)

        # --- 4 Trainers ---
        print("Creating trainers...", flush=True)
        trainers = []
        for i in range(1, 5):
            t = User(
                name=f"Trainer {i}",
                email=f"trainer{i}@sb.com",
                hashed_password=hash_password("password123"),
                role=UserRole.trainer,
                institution_id=inst1.id if i <= 2 else inst2.id
            )
            db.add(t)
            trainers.append(t)
        db.commit()
        for t in trainers:
            db.refresh(t)
        print(f"  Created {len(trainers)} trainers", flush=True)

        # --- Programme Manager and Monitoring Officer ---
        print("Creating PM and Monitoring Officer...", flush=True)
        pm = User(name="Programme Manager", email="pm@sb.com",
                  hashed_password=hash_password("password123"), role=UserRole.programme_manager)
        mo = User(name="Monitor Officer", email="monitor@sb.com",
                  hashed_password=hash_password("password123"), role=UserRole.monitoring_officer)
        db.add_all([pm, mo])
        db.commit()

        # --- 15 Students ---
        print("Creating 15 students...", flush=True)
        students = []
        for i in range(1, 16):
            s = User(
                name=f"Student {i}",
                email=f"student{i}@sb.com",
                hashed_password=hash_password("password123"),
                role=UserRole.student
            )
            db.add(s)
            students.append(s)
        db.commit()
        for s in students:
            db.refresh(s)
        print(f"  Created {len(students)} students", flush=True)

        # --- 3 Batches ---
        print("Creating batches...", flush=True)
        batch1 = Batch(name="Python Basics",    institution_id=inst1.id)
        batch2 = Batch(name="Web Dev Bootcamp", institution_id=inst1.id)
        batch3 = Batch(name="Data Science 101", institution_id=inst2.id)
        db.add_all([batch1, batch2, batch3])
        db.commit()
        db.refresh(batch1)
        db.refresh(batch2)
        db.refresh(batch3)
        print(f"  batch1.id={batch1.id}, batch2.id={batch2.id}, batch3.id={batch3.id}", flush=True)

        # --- Assign trainers to batches ---
        print("Assigning trainers to batches...", flush=True)
        db.add_all([
            BatchTrainer(batch_id=batch1.id, trainer_id=trainers[0].id),
            BatchTrainer(batch_id=batch2.id, trainer_id=trainers[1].id),
            BatchTrainer(batch_id=batch3.id, trainer_id=trainers[2].id),
            BatchTrainer(batch_id=batch3.id, trainer_id=trainers[3].id),
        ])

        # --- Enroll students ---
        print("Enrolling students...", flush=True)
        for i, student in enumerate(students):
            batch = [batch1, batch2, batch3][i % 3]
            db.add(BatchStudent(batch_id=batch.id, student_id=student.id))
        db.commit()

        # --- 8 Sessions ---
        print("Creating sessions...", flush=True)
        session_data = [
            (batch1, trainers[0], "Intro to Python",       date(2024, 1, 10)),
            (batch1, trainers[0], "Variables & Types",     date(2024, 1, 12)),
            (batch1, trainers[0], "Control Flow",          date(2024, 1, 15)),
            (batch2, trainers[1], "HTML & CSS Basics",     date(2024, 1, 11)),
            (batch2, trainers[1], "JavaScript Intro",      date(2024, 1, 14)),
            (batch3, trainers[2], "NumPy & Pandas",        date(2024, 1, 10)),
            (batch3, trainers[2], "Data Visualisation",    date(2024, 1, 13)),
            (batch3, trainers[3], "Machine Learning Intro",date(2024, 1, 16)),
        ]

        sessions = []
        for batch, trainer, title, d in session_data:
            s = SessionModel(
                batch_id=batch.id,
                trainer_id=trainer.id,
                title=title,
                date=d,
                start_time=time(9, 0),
                end_time=time(11, 0)
            )
            db.add(s)
            sessions.append(s)
        db.commit()
        for s in sessions:
            db.refresh(s)
        print(f"  Created {len(sessions)} sessions", flush=True)

        # --- Attendance records ---
        print("Creating attendance records...", flush=True)
        statuses = [
            AttendanceStatus.present, AttendanceStatus.present,
            AttendanceStatus.present, AttendanceStatus.absent,
            AttendanceStatus.late
        ]
        attendance_count = 0
        for session in sessions:
            enrolled = db.query(BatchStudent).filter(
                BatchStudent.batch_id == session.batch_id
            ).all()
            for enrollment in enrolled:
                db.add(Attendance(
                    session_id=session.id,
                    student_id=enrollment.student_id,
                    status=random.choice(statuses),
                    marked_at=datetime.now(timezone.utc),
                ))
                attendance_count += 1
        db.commit()
        print(f"  Created {attendance_count} attendance records", flush=True)

        print("\nDone! Database seeded successfully.", flush=True)

    except Exception as e:
        print(f"\nERROR during seeding: {e}", flush=True)
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run()