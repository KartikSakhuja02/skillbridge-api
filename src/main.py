from fastapi import FastAPI
from src.database import engine, Base
from src.routers import auth, batches, sessions, attendance, institutions, programme, monitoring

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SkillBridge API",
    description="Attendance management system for the SkillBridge skilling programme",
    version="1.0.0"
)

app.include_router(auth.router)
app.include_router(batches.router)
app.include_router(sessions.router)
app.include_router(attendance.router)
app.include_router(institutions.router)
app.include_router(programme.router)
app.include_router(monitoring.router)

@app.get("/")
def root():
    return {"message": "SkillBridge API is running", "docs": "/docs"}